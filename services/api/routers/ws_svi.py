"""WebSocket endpoint for real-time SVI push notifications to responder dashboards."""

import asyncio
import json
from collections import defaultdict
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from packages.config import get_settings
from packages.utils import get_logger

logger = get_logger("saathi.api.ws_svi")
router = APIRouter(tags=["Realtime SVI WebSocket"])


class SVIConnectionManager:
    """Manages active WebSocket connections per session_id and broadcasts updates."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[session_id].add(websocket)
        logger.info("ws_client_connected", session_id=session_id)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)
                if not self._connections[session_id]:
                    del self._connections[session_id]
        logger.info("ws_client_disconnected", session_id=session_id)

    async def broadcast(self, session_id: str, data: dict):
        """Broadcasts JSON payload to all active WebSockets for a session_id."""
        async with self._lock:
            sockets = list(self._connections.get(session_id, set()))

        dead_sockets = []
        for ws in sockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead_sockets.append(ws)

        if dead_sockets:
            async with self._lock:
                for ws in dead_sockets:
                    if session_id in self._connections:
                        self._connections[session_id].discard(ws)


manager = SVIConnectionManager()


async def broadcast_svi_update(session_id: str, data: dict):
    """Publish SVI update to in-memory websockets and Redis (if available)."""
    # 1. In-memory websocket broadcast
    await manager.broadcast(session_id, data)

    # 2. Redis publish (if redis library and server available)
    settings = get_settings()
    try:
        import redis.asyncio as redis  # type: ignore

        r = redis.from_url(settings.REDIS_URL)
        channel = f"svi_updates:{session_id}"
        await r.publish(channel, json.dumps(data))
        await r.close()
    except Exception:
        # Graceful fallback: Redis is optional in development/test
        pass


@router.websocket("/ws/svi/{session_id}")
async def svi_websocket(websocket: WebSocket, session_id: str):
    """WebSocket connection handler for live SVI updates."""
    await manager.connect(session_id, websocket)

    settings = get_settings()
    redis_task = None

    # Try background Redis listener if Redis is available
    async def listen_redis():
        try:
            import redis.asyncio as redis  # type: ignore

            r = redis.from_url(settings.REDIS_URL)
            pubsub = r.pubsub()
            await pubsub.subscribe(f"svi_updates:{session_id}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await websocket.send_json(payload)
        except Exception:
            pass

    try:
        redis_task = asyncio.create_task(listen_redis())

        # Keep connection open and listen for client messages / ping
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("ws_connection_closed", session_id=session_id, reason=str(e))
    finally:
        if redis_task:
            redis_task.cancel()
        await manager.disconnect(session_id, websocket)
