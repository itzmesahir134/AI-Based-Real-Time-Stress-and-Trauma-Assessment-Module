"""M22: Risk Band Classifier.

Maps continuous SVI score (0-100) to operational triage risk bands (Spec §22).
    LOW:      0 - 24.9
    MODERATE: 25 - 49.9
    HIGH:     50 - 74.9
    CRITICAL: 75 - 100
"""

from packages.schemas.common import RiskBand


def classify_risk_band(svi: float) -> RiskBand:
    """Spec M22: Classify numerical SVI into standardized RiskBand.

    Args:
        svi: Support Vulnerability Index score (0-100).

    Returns:
        RiskBand enum (LOW, MODERATE, HIGH, CRITICAL).
    """
    if svi >= 75.0:
        return RiskBand.CRITICAL
    elif svi >= 50.0:
        return RiskBand.HIGH
    elif svi >= 25.0:
        return RiskBand.MODERATE
    else:
        return RiskBand.LOW
