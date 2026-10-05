"""M12: Text Distress Classifier.

Calculates a calibrated continuous text distress score (0-100) from
normalized transcripts and linguistic feature vectors.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

from packages.schemas.text import LinguisticFeatures, NormalizedTranscript, TextInferenceResult

_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "text" / "text_distress_model.joblib"


@lru_cache(maxsize=1)
def _load_text_pipeline():
    """Load the trained NLP model pipeline if available."""
    if _MODEL_PATH.exists():
        try:
            import joblib
            return joblib.load(_MODEL_PATH)
        except Exception:
            return None
    return None


# Dimensional base impact weights
_DIM_WEIGHTS: Dict[str, float] = {
    "threat": 26.0,
    "fear": 20.0,
    "help_request": 20.0,
    "helplessness": 16.0,
    "urgency": 14.0,
    "negative_affect": 12.0,
    "self_blame": 8.0,
    "uncertainty": 5.0,
}


def classify_text_distress(
    transcript: NormalizedTranscript,
    features: Optional[LinguisticFeatures] = None,
    language: str = "en",
) -> TextInferenceResult:
    """Spec M12: Classify text distress score from linguistic indicators and NLP models.

    Args:
        transcript: NormalizedTranscript from M10.
        features: Optional pre-extracted LinguisticFeatures from M11 (extracted if None).
        language: Language code.

    Returns:
        TextInferenceResult with 0-100 distress score and evidence breakdown.
    """
    text = transcript.text.strip()
    if not text:
        return TextInferenceResult(
            score=None,
            confidence=0.0,
            indicators=["empty_transcript"],
            model_version="v1.0.0-lexicon-heuristic",
            language=language,
            abstained=True,
        )

    # If features not supplied, extract them on the fly
    if features is None:
        from .linguistic_features import extract_linguistic_features
        features = extract_linguistic_features(transcript, language=language)

    # 1. Evaluate dimensional contributions
    dim_counts = {
        "threat": len(features.threat_indicators),
        "fear": len(features.fear_indicators),
        "help_request": len(features.help_request_indicators),
        "helplessness": len(features.helplessness_indicators),
        "urgency": len(features.urgency_indicators),
        "negative_affect": len(features.negative_affect_indicators),
        "self_blame": len(features.self_blame_indicators),
        "uncertainty": len(features.uncertainty_indicators),
    }

    raw_sum = 0.0
    active_indicators: List[str] = []

    for dim, weight in _DIM_WEIGHTS.items():
        cnt = dim_counts[dim]
        if cnt > 0:
            # Diminishing returns scaling for repeated indicators in same dimension
            dim_score = weight * (1.0 + 0.25 * min(cnt - 1, 3))
            raw_sum += dim_score
            # Record evidence tag
            indicator_terms = getattr(features, f"{dim}_indicators", [])
            terms_preview = ", ".join(indicator_terms[:3])
            active_indicators.append(f"{dim}: {terms_preview}")

    # 2. Text density & length adjustments
    words = text.split()
    total_words = len(words)
    indicator_count = features.indicator_count

    if indicator_count > 0:
        # Density factor: high proportion of distress words in brief emergency calls raises urgency
        density = indicator_count / max(total_words, 1)
        density_multiplier = 1.0 + 0.5 * min(density, 1.0)
        rule_score = float(np.clip(raw_sum * density_multiplier, 15.0, 100.0))
    else:
        # Calm conversational baseline
        rule_score = 10.0
        active_indicators = ["neutral_conversational_language"]

    # Check for trained NLP model
    pipeline = _load_text_pipeline()
    model_version = "v1.0.0-lexicon-heuristic"
    if pipeline is not None:
        try:
            ml_pred = float(pipeline.predict([text])[0])
            if indicator_count == 0:
                # Neutral baseline: keep within low risk band
                final_score = float(np.clip(0.30 * ml_pred + 0.70 * rule_score, 0.0, 18.0))
            else:
                # Ensemble 60% ML + 40% linguistic indicator rules
                final_score = float(np.clip(0.60 * ml_pred + 0.40 * rule_score, 0.0, 100.0))
            model_version = "v1.1.0-tfidf-rf"
        except Exception:
            final_score = rule_score
    else:
        final_score = rule_score

    # 3. Confidence calibration
    # Confidence scales with word count and segment confidence
    segment_confs = [seg.confidence for seg in transcript.segments if seg.confidence is not None]
    mean_seg_conf = float(np.mean(segment_confs)) if segment_confs else 0.85

    # Word count scaling: 1 word ~ 0.50, 10+ words ~ 0.85, 30+ words ~ 0.95
    length_factor = float(np.clip(total_words / 20.0, 0.45, 1.0))
    calibrated_conf = round(float(np.clip(mean_seg_conf * length_factor, 0.20, 0.98)), 2)

    return TextInferenceResult(
        score=round(final_score, 1),
        confidence=calibrated_conf,
        indicators=active_indicators,
        model_version=model_version,
        language=language,
        abstained=False,
    )
