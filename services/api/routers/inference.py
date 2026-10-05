from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from packages.schemas import (
    AudioQualityResult,
    ContextData,
    CrisisResult,
    LinguisticFeatures,
    NormalizedTranscript,
    SelfReportQuestionnaire,
    TextInferenceResult,
    VoiceFeatureVector,
    VoiceInferenceResult,
)
from services.inference import (
    classify_text_distress,
    evaluate_voice_distress,
    extract_linguistic_features,
    normalize_transcript,
)
from services.scoring import detect_crisis

router = APIRouter(prefix="/api/v1/inference", tags=["Inference Models"])


class VoiceInferenceRequest(BaseModel):
    features: VoiceFeatureVector
    quality: Optional[AudioQualityResult] = None
    language: str = "en"


class TextInferenceRequest(BaseModel):
    text: Optional[str] = None
    transcript: Optional[NormalizedTranscript] = None
    features: Optional[LinguisticFeatures] = None
    language: str = "en"


class CrisisInferenceRequest(BaseModel):
    text: Optional[str] = None
    transcript: Optional[NormalizedTranscript] = None
    self_report: Optional[SelfReportQuestionnaire] = None
    context: Optional[ContextData] = None


@router.post("/voice", response_model=VoiceInferenceResult, status_code=status.HTTP_200_OK)
async def infer_voice_distress(req: VoiceInferenceRequest):
    """Spec M09: Predict acoustic distress indicator score from features."""
    try:
        return evaluate_voice_distress(
            features=req.features,
            quality=req.quality,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voice distress inference failed: {str(e)}",
        )


@router.post("/text", response_model=TextInferenceResult, status_code=status.HTTP_200_OK)
async def infer_text_distress(req: TextInferenceRequest):
    """Spec M12: Classify text distress indicator score from transcript."""
    try:
        if req.transcript is not None:
            norm_trans = req.transcript
        elif req.text:
            norm_trans = normalize_transcript(req.text, language=req.language)
        else:
            norm_trans = normalize_transcript("", language=req.language)

        ling_features = req.features
        if ling_features is None and norm_trans.text:
            ling_features = extract_linguistic_features(norm_trans, language=req.language)

        return classify_text_distress(
            transcript=norm_trans,
            features=ling_features,
            language=req.language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text distress inference failed: {str(e)}",
        )


@router.post("/crisis", response_model=CrisisResult, status_code=status.HTTP_200_OK)
async def infer_crisis_state(req: CrisisInferenceRequest):
    """Spec M13: Two-layer crisis and imminent harm detection."""
    try:
        trans_input = req.transcript or req.text
        return detect_crisis(
            transcript=trans_input,
            self_report=req.self_report,
            context=req.context,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Crisis detection failed: {str(e)}",
        )
