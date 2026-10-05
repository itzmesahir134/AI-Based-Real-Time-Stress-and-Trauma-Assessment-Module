"""M19: Evidence Quality Estimator.

Computes reliability weight multipliers (0.0 to 1.0) per modality
based on acoustic SNR, transcription fidelity, and questionnaire completeness (Spec §19).
"""

from typing import Optional
from packages.schemas.assessment import QualityFactors
from packages.schemas.audio import AudioQualityResult, VoiceInferenceResult
from packages.schemas.scoring import ContextRiskResult, SelfReportResult
from packages.schemas.text import TextInferenceResult


def estimate_evidence_quality(
    audio_quality: Optional[AudioQualityResult] = None,
    voice_inference: Optional[VoiceInferenceResult] = None,
    text_inference: Optional[TextInferenceResult] = None,
    self_report_result: Optional[SelfReportResult] = None,
    context_result: Optional[ContextRiskResult] = None,
    interaction_quality: Optional[float] = None,
) -> QualityFactors:
    """Spec M19: Estimate reliability quality factors for each modality.

    Args:
        audio_quality: AudioQualityResult from M04.
        voice_inference: VoiceInferenceResult from M09.
        text_inference: TextInferenceResult from M12.
        self_report_result: SelfReportResult from M15.
        context_result: ContextRiskResult from M17.
        interaction_quality: Optional behavioral interaction quality score.

    Returns:
        QualityFactors object with quality multipliers for available modalities.
    """
    # Voice quality: product of physical audio reliability and model confidence
    voice_q: Optional[float] = None
    if voice_inference is not None:
        if voice_inference.abstained:
            voice_q = 0.0
        else:
            snr_weight = audio_quality.quality_score if audio_quality is not None else 0.85
            voice_q = round(float(snr_weight * voice_inference.confidence), 3)

    # Text quality: model confidence on normalized transcript
    text_q: Optional[float] = None
    if text_inference is not None:
        if text_inference.abstained:
            text_q = 0.0
        else:
            text_q = round(float(text_inference.confidence), 3)

    # Self report quality: questionnaire completeness ratio
    sr_q: Optional[float] = None
    if self_report_result is not None:
        sr_q = round(float(self_report_result.completeness), 3)

    # Context quality: data availability ratio
    ctx_q: Optional[float] = None
    if context_result is not None:
        ctx_q = round(float(context_result.completeness), 3)

    # Interaction quality
    int_q: Optional[float] = None
    if interaction_quality is not None:
        int_q = round(float(interaction_quality), 3)

    return QualityFactors(
        voice=voice_q,
        text=text_q,
        self_report=sr_q,
        context=ctx_q,
        interaction=int_q,
    )
