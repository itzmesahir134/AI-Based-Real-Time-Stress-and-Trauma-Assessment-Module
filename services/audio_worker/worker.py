"""Audio and inference worker process for SAATHI-AI.

Listens to task queues (Redis) and processes audio processing,
quality analysis, feature extraction, and transcription tasks.
"""
import asyncio
import signal
import sys

from packages.config import get_settings
from packages.utils import get_logger, setup_logging

settings = get_settings()
logger = get_logger("saathi.audio_worker")


class AudioWorker:
    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        self.running = True
        setup_logging(log_level=settings.LOG_LEVEL)
        logger.info(
            "audio_worker_started",
            environment=settings.ENVIRONMENT,
            redis_url=settings.REDIS_URL,
        )

        try:
            while self.running:
                # Polling/listening loop for incoming audio processing jobs
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            logger.info("audio_worker_cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        self.running = False
        logger.info("audio_worker_shutdown_complete")

    def stop(self) -> None:
        self.running = False


async def main() -> None:
    worker = AudioWorker()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            # Signal handling on Windows
            signal.signal(sig, lambda s, f: worker.stop())

    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
