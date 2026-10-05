"""M23: Safety Override Engine.

Enforces zero-delay clinical safety overrides (Spec §23).
If an acute crisis or imminent harm trigger is identified by M13,
the priority is escalated to CRITICAL regardless of numerical SVI.
"""

from typing import Tuple
from packages.schemas.common import RiskBand
from packages.schemas.scoring import CrisisResult


def apply_safety_override(
    base_risk_band: RiskBand,
    crisis: CrisisResult,
) -> Tuple[RiskBand, bool]:
    """Spec M23: Evaluate whether safety trigger forces CRITICAL priority.

    Args:
        base_risk_band: Calculated RiskBand from SVI score.
        crisis: CrisisResult from M13.

    Returns:
        (final_risk_band, safety_override_applied)
    """
    if crisis.safety_flag:
        return RiskBand.CRITICAL, True
    return base_risk_band, False
