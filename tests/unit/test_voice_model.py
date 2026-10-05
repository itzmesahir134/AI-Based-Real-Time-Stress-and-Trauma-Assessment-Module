import pytest
from packages.schemas.audio import (
    AudioQualityResult,
    VoiceFeatureVector,
    VoiceInferenceResult,
)
from services.inference.voice_model import evaluate_voice_distress


@pytest.mark.unit
def test_voice_distress_abstained_on_poor_quality():
    features = VoiceFeatureVector(
        pitch_mean=210.0,
        pitch_std=45.0,
        voiced_fraction=0.75,
        energy_mean=0.1,
    )
    poor_quality = AudioQualityResult(
        quality_score=0.10,
        distortion_flags=["HIGH_NOISE_FLOOR"],
    )

    result = evaluate_voice_distress(features, quality=poor_quality)
    assert isinstance(result, VoiceInferenceResult)
    assert result.abstained is True
    assert result.score is None
    assert "audio_quality_insufficient" in result.evidence_features


@pytest.mark.unit
def test_voice_distress_abstained_on_unvoiced():
    features = VoiceFeatureVector(voiced_fraction=0.0, energy_mean=0.0)
    result = evaluate_voice_distress(features)
    assert result.abstained is True
    assert result.score is None
    assert "no_voiced_speech_detected" in result.evidence_features


@pytest.mark.unit
def test_voice_distress_calm_speech():
    features = VoiceFeatureVector(
        pitch_mean=140.0,
        pitch_std=12.0,
        pitch_range=40.0,
        jitter=0.008,
        shimmer=0.02,
        energy_mean=0.08,
        energy_std=0.03,
        pause_ratio=0.15,
        spectral_centroid_mean=1200.0,
        speech_rate_syl_per_sec=3.5,
        voiced_fraction=0.85,
    )
    good_quality = AudioQualityResult(quality_score=0.92)

    result = evaluate_voice_distress(features, quality=good_quality)
    assert result.abstained is False
    assert result.score is not None
    assert result.score < 30.0  # Calm baseline
    assert result.confidence >= 0.70


@pytest.mark.unit
def test_voice_distress_acute_agitation():
    features = VoiceFeatureVector(
        pitch_mean=320.0,  # Shrill/screaming
        pitch_std=65.0,   # Wide erratic swings
        pitch_range=220.0,
        jitter=0.055,     # Tremor
        shimmer=0.12,
        energy_mean=0.25,
        energy_std=0.22,
        pause_ratio=0.60, # Gasping/choking pauses
        spectral_centroid_mean=2800.0,
        speech_rate_syl_per_sec=7.0,
        voiced_fraction=0.70,
    )
    good_quality = AudioQualityResult(quality_score=0.88)

    result = evaluate_voice_distress(features, quality=good_quality)
    assert result.abstained is False
    assert result.score is not None
    assert result.score > 60.0  # Elevated distress
    assert any(
        ev in result.evidence_features
        for ev in ["elevated_pitch_variability", "vocal_perturbation_tremor", "erratic_energy_dynamics"]
    )
