"""M16: Context Parser.

Normalizes caller history, situational context, and intake data into structured ContextData.
"""

from typing import Any, Dict, List, Union
from packages.schemas.scoring import ContextData


def parse_context(
    raw_data: Union[ContextData, Dict[str, Any]],
) -> ContextData:
    """Spec M16: Parse and validate intake context data.

    Args:
        raw_data: ContextData object or raw intake dictionary.

    Returns:
        Structured ContextData object.
    """
    if isinstance(raw_data, ContextData):
        return raw_data

    incident_type = str(raw_data.get("incident_type", "unknown")).lower()
    ongoing_threat = bool(raw_data.get("ongoing_threat", False))
    prior_case = bool(raw_data.get("prior_case", False))
    immediate_support_requested = bool(raw_data.get("immediate_support_requested", False))

    raw_vuln = raw_data.get("vulnerability_factors", [])
    if isinstance(raw_vuln, str):
        vulnerability_factors = [f.strip().lower() for f in raw_vuln.split(",") if f.strip()]
    elif isinstance(raw_vuln, list):
        vulnerability_factors = [str(f).strip().lower() for f in raw_vuln if str(f).strip()]
    else:
        vulnerability_factors = []

    return ContextData(
        incident_type=incident_type,
        ongoing_threat=ongoing_threat,
        prior_case=prior_case,
        vulnerability_factors=vulnerability_factors,
        immediate_support_requested=immediate_support_requested,
    )
