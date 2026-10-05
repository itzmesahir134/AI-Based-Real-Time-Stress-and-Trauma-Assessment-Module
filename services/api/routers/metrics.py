"""Prometheus-format /metrics endpoint + in-process counter registry (Phase 13E)."""
import time
import asyncio
from collections import defaultdict
from typing import Dict

from fastapi import APIRouter, Response

router = APIRouter(tags=["Observability"])

# ---------------------------------------------------------------------------
# In-process metric registry (no external Prometheus client lib needed)
# ---------------------------------------------------------------------------
_lock = asyncio.Lock()
_counters: Dict[str, int] = defaultdict(int)
_histograms: Dict[str, list] = defaultdict(list)
_gauges: Dict[str, float] = {}


async def inc_counter(name: str, labels: Dict[str, str] | None = None) -> None:
    """Increment a named counter, thread-safe."""
    key = _label_key(name, labels or {})
    async with _lock:
        _counters[key] += 1


async def observe_histogram(name: str, value: float, labels: Dict[str, str] | None = None) -> None:
    """Record a histogram observation."""
    key = _label_key(name, labels or {})
    async with _lock:
        _histograms[key].append(value)


async def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None) -> None:
    """Set a gauge value."""
    key = _label_key(name, labels or {})
    async with _lock:
        _gauges[key] = value


def _label_key(name: str, labels: Dict[str, str]) -> str:
    if not labels:
        return name
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"{name}{{{label_str}}}"


# ---------------------------------------------------------------------------
# Text-format Prometheus endpoint
# ---------------------------------------------------------------------------
BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float("inf")]


@router.get("/metrics", include_in_schema=False)
async def get_metrics():
    """Phase 13E: Prometheus text-format /metrics endpoint."""
    lines = []

    # Counters
    lines.append("# HELP saathi_requests_total Total API requests by endpoint and status")
    lines.append("# TYPE saathi_requests_total counter")
    async with _lock:
        for key, value in _counters.items():
            metric_name = key.split("{")[0]
            if metric_name == "saathi_requests_total":
                labels_part = key[len(metric_name):]
                lines.append(f"saathi_requests_total{labels_part} {value}")

        # Assessment counters
        lines.append("")
        lines.append("# HELP saathi_assessments_total Total assessments run")
        lines.append("# TYPE saathi_assessments_total counter")
        for key, value in _counters.items():
            metric_name = key.split("{")[0]
            if metric_name == "saathi_assessments_total":
                labels_part = key[len(metric_name):]
                lines.append(f"saathi_assessments_total{labels_part} {value}")

        # Safety overrides
        lines.append("")
        lines.append("# HELP saathi_safety_overrides_total Total safety override triggers")
        lines.append("# TYPE saathi_safety_overrides_total counter")
        override_count = _counters.get("saathi_safety_overrides_total", 0)
        lines.append(f"saathi_safety_overrides_total {override_count}")

        # Histograms
        lines.append("")
        lines.append("# HELP saathi_pipeline_duration_seconds Assessment pipeline end-to-end duration")
        lines.append("# TYPE saathi_pipeline_duration_seconds histogram")
        hist_key = "saathi_pipeline_duration_seconds"
        obs = _histograms.get(hist_key, [])
        for bucket in BUCKETS:
            count = sum(1 for v in obs if v <= bucket)
            le_label = "+Inf" if bucket == float("inf") else str(bucket)
            lines.append(f'saathi_pipeline_duration_seconds_bucket{{le="{le_label}"}} {count}')
        lines.append(f"saathi_pipeline_duration_seconds_count {len(obs)}")
        lines.append(f"saathi_pipeline_duration_seconds_sum {sum(obs):.4f}")

        # Gauges
        lines.append("")
        lines.append("# HELP saathi_active_sessions_total Current active sessions")
        lines.append("# TYPE saathi_active_sessions_total gauge")
        active = _gauges.get("saathi_active_sessions_total", 0)
        lines.append(f"saathi_active_sessions_total {active}")

    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
