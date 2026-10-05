"""M09: Voice Distress Model.

Evaluates acoustic and prosodic feature vectors from M08 to compute
a continuous voice distress indicator score (0-100) with calibrated confidence,
evidence breakdown, and quality gating.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
import numpy as np

from packages.schemas.audio import AudioQualityResult, VoiceFeatureVector, VoiceInferenceResult

_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "voice" / "voice_distress_model.joblib"


@lru_cache(maxsize=1)
def _load_voice_pipeline():
    """Load the trained ML pipeline if available."""
    if _MODEL_PATH.exists():
        try:
            import joblib
            return joblib.load(_MODEL_PATH)
        except Exception:
            return None
    return None


def evaluate_voice_distress(
    features: VoiceFeatureVector,
    quality: Optional[AudioQualityResult] = None,
    language: str = "en",
) -> VoiceInferenceResult:
    """Spec M09: Predict voice distress indicator score from acoustic features.

    Args:
        features: VoiceFeatureVector extracted from M08.
        quality: Optional AudioQualityResult from M04 for quality gating.
        language: Language code for acoustic reference norms.

    Returns:
        VoiceInferenceResult with distress score (0-100), confidence, and evidence features.
    """
    # 1. Quality & Abstained Check (Spec M04/M09 quality gating)
    if quality is not None:
        if quality.quality_score < 0.15 or "EMPTY_AUDIO" in quality.distortion_flags:
            return VoiceInferenceResult(
                score=None,
                confidence=0.0,
                evidence_features=["audio_quality_insufficient"],
                model_version="v1.0.0-heuristic",
                abstained=True,
            )

    if features.voiced_fraction <= 0.0 or features.energy_mean < 1e-5:
        return VoiceInferenceResult(
            score=None,
            confidence=0.0,
            evidence_features=["no_voiced_speech_detected"],
            model_version="v1.0.0-heuristic",
            abstained=True,
        )

    # 2. Normalized indicator extraction
    # A. Pitch variability & range (pitch_std > 20 Hz indicates elevated distress/instability)
    norm_pitch_var = float(np.clip((features.pitch_std - 15.0) / 60.0, 0.0, 1.0))
    norm_pitch_range = float(np.clip((features.pitch_range - 60.0) / 180.0, 0.0, 1.0))
    pitch_dyn = 0.6 * norm_pitch_var + 0.4 * norm_pitch_range

    # B. Pitch elevation (screaming, high agitation, or acute fear)
    norm_pitch_high = float(np.clip((features.pitch_mean - 220.0) / 160.0, 0.0, 1.0))

    # C. Perturbation: Jitter (pitch perturbation) and Shimmer (amplitude perturbation)
    norm_jitter = float(np.clip((features.jitter - 0.015) / 0.045, 0.0, 1.0))
    norm_shimmer = float(np.clip((features.shimmer - 0.035) / 0.075, 0.0, 1.0))
    perturbation = 0.5 * norm_jitter + 0.5 * norm_shimmer

    # D. Energy variation & dynamic coefficient of variation
    energy_cv = features.energy_std / max(features.energy_mean, 1e-4)
    norm_energy_var = float(np.clip((energy_cv - 0.45) / 0.90, 0.0, 1.0))

    # E. Pause dynamics & speech disruptions (choked voice, frequent gasps)
    norm_pause = float(np.clip((features.pause_ratio - 0.25) / 0.50, 0.0, 1.0))

    # F. Spectral centroid tension (high-frequency energy shift from strained vocal cords)
    norm_centroid = float(np.clip((features.spectral_centroid_mean - 1600.0) / 1400.0, 0.0, 1.0))

    # G. Frantic speech rate
    norm_rate = float(np.clip((features.speech_rate_syl_per_sec - 4.5) / 3.0, 0.0, 1.0))

    # Indicator map for evidence explanation
    indicators = [
        ("elevated_pitch_variability", pitch_dyn, 0.22),
        ("vocal_perturbation_tremor", perturbation, 0.20),
        ("erratic_energy_dynamics", norm_energy_var, 0.18),
        ("speech_disruptions_and_pauses", norm_pause, 0.15),
        ("acute_pitch_elevation", norm_pitch_high, 0.12),
        ("high_frequency_vocal_tension", norm_centroid, 0.08),
        ("rapid_frantic_speech_rate", norm_rate, 0.05),
    ]

    # Weighted composite distress indicator (0.0 to 1.0)
    total_weight = sum(weight for _, _, weight in indicators)
    raw_distress = sum(val * weight for _, val, weight in indicators) / total_weight

    # Handle flat / emotionally blunted monotone speech (atypical low pitch std + moderate/low mean)
    if features.pitch_std < 10.0 and features.pitch_mean > 70.0 and features.voiced_fraction > 0.3:
        raw_distress = max(raw_distress, 0.40)
        indicators.append(("affective_monotone_blunting", 0.70, 0.15))

    heuristic_score = float(np.clip(raw_distress * 100.0, 0.0, 100.0))

    # Check for trained ML model checkpoint
    pipeline = _load_voice_pipeline()
    model_version = "v1.0.0-heuristic"
    if pipeline is not None:
        try:
            mfccs = features.mfcc_mean if features.mfcc_mean and len(features.mfcc_mean) == 13 else [0.0] * 13
            x_vec = np.array([[
                features.pitch_mean,
                features.pitch_std,
                features.pitch_range,
                features.speech_rate_syl_per_sec,
                features.pause_ratio,
                features.pause_count,
                features.energy_mean,
                features.energy_std,
                features.jitter,
                features.shimmer,
                features.spectral_centroid_mean,
                features.zcr_mean,
                features.voiced_fraction,
                *mfccs
            ]])
            ml_pred = float(pipeline.predict(x_vec)[0])
            # Ensemble 60% ML + 40% calibrated acoustic rules for robust interpretability
            score = round(float(np.clip(0.60 * ml_pred + 0.40 * heuristic_score, 0.0, 100.0)), 1)
            model_version = "v1.1.0-gb-ensemble"
        except Exception:
            score = round(heuristic_score, 1)
    else:
        score = round(heuristic_score, 1)

    # 3. Evidence extraction: select top contributing indicators
    active_indicators = [
        (name, val * weight) for name, val, weight in indicators if val >= 0.20
    ]
    active_indicators.sort(key=lambda item: item[1], reverse=True)
    evidence = [name for name, _ in active_indicators[:4]]

    if not evidence:
        evidence = ["baseline_neutral_prosody"]

    # 4. Confidence calibration
    base_reliability = quality.quality_score if quality is not None else 0.85
    voiced_factor = 0.5 + 0.5 * features.voiced_fraction
    confidence = round(float(np.clip(base_reliability * voiced_factor, 0.10, 0.98)), 2)

    return VoiceInferenceResult(
        score=score,
        confidence=confidence,
        evidence_features=evidence,
        model_version=model_version,
        abstained=False,
    )
