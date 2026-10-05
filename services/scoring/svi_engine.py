"""M21: Support Vulnerability Index (SVI) Fusion Engine.

Computes the composite SVI score (0-100), calibrated confidence, evidence coverage,
modality contributions, and clinical explanations using quality-adjusted weighted averaging (Spec §21).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from packages.schemas.assessment import (
    AssessmentStatus,
    ModalityContributions,
    ModalityScores,
    QualityFactors,
    RiskBand,
    SVIResult,
)
from .risk_classifier import classify_risk_band

# Default modality weights (Spec §21.2)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "voice": 0.20,
    "text": 0.25,
    "self_report": 0.30,
    "context": 0.15,
    "interaction": 0.10,
}


def calculate_svi(
    modality_scores: ModalityScores,
    quality_factors: Optional[QualityFactors] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, float, AssessmentStatus, ModalityContributions, List[str], List[str]]:
    """Spec M21: Compute composite Support Vulnerability Index (SVI).

    Args:
        modality_scores: Raw 0-100 scores across modalities.
        quality_factors: Reliability multipliers (0.0 to 1.0) per modality.
        weights: Optional dictionary of nominal weights (defaults to DEFAULT_WEIGHTS).

    Returns:
        (svi, confidence, coverage, status, contributions, contributors, missing_evidence)
    """
    w_map = weights or DEFAULT_WEIGHTS
    q_factors = quality_factors or QualityFactors()

    modalities = ["voice", "text", "self_report", "context", "interaction"]
    available_eff_weights: Dict[str, float] = {}
    valid_scores: Dict[str, float] = {}
    missing_evidence: List[str] = []

    for mod in modalities:
        score = getattr(modality_scores, mod)
        q = getattr(q_factors, mod)

        # If quality is None but score is provided, default quality to 0.85
        if score is not None:
            effective_q = 0.85 if q is None else float(q)
            if effective_q > 0.05:
                w_nominal = w_map.get(mod, 0.20)
                eff_w = w_nominal * effective_q
                available_eff_weights[mod] = eff_w
                valid_scores[mod] = float(score)
            else:
                missing_evidence.append(f"low_quality_{mod}")
        else:
            missing_evidence.append(f"uncollected_{mod}")

    # Calculate evidence coverage
    total_nominal_weight = sum(w_map.values())
    present_nominal_weight = sum(w_map.get(m, 0.0) for m in valid_scores)
    evidence_coverage = round(float(np.clip(present_nominal_weight / total_nominal_weight, 0.0, 1.0)), 2)

    # Determine assessment status
    if evidence_coverage >= 0.70:
        status = AssessmentStatus.COMPLETE
    elif evidence_coverage >= 0.35:
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.INSUFFICIENT_EVIDENCE

    # Calculate SVI
    denom = sum(available_eff_weights.values())
    contributions_dict: Dict[str, Optional[float]] = {m: None for m in modalities}

    if denom > 0:
        numerator = sum(available_eff_weights[m] * valid_scores[m] for m in valid_scores)
        svi = round(float(np.clip(numerator / denom, 0.0, 100.0)), 1)

        # Modality contributions (sums to final SVI)
        for m in valid_scores:
            c_val = round((available_eff_weights[m] / denom) * valid_scores[m], 2)
            contributions_dict[m] = c_val
    else:
        svi = 0.0

    contributions = ModalityContributions(**contributions_dict)

    # Ranked explanation contributors
    ranked = sorted(
        [(m, valid_scores[m], contributions_dict[m] or 0.0) for m in valid_scores],
        key=lambda item: item[2],
        reverse=True,
    )
    contributors = [
        f"{m.replace('_', ' ').capitalize()} distress indicator (score={s:.1f}, contrib={c:.1f})"
        for m, s, c in ranked
    ]
    if not contributors:
        contributors = ["No active distress modalities recorded"]

    # Calibrated confidence
    mean_q = denom / max(present_nominal_weight, 1e-4) if denom > 0 else 0.0
    calibrated_conf = round(float(np.clip(evidence_coverage * mean_q, 0.10, 0.98)), 2)

    return (
        svi,
        calibrated_conf,
        evidence_coverage,
        status,
        contributions,
        contributors,
        missing_evidence,
    )
