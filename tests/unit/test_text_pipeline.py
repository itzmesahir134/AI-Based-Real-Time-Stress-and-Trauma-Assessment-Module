import pytest
from packages.schemas.audio import TranscriptResponse, TranscriptSegment
from packages.schemas.text import (
    LinguisticFeatures,
    NormalizedTranscript,
    TextInferenceResult,
)
from services.inference.linguistic_features import extract_linguistic_features
from services.inference.text_classifier import classify_text_distress
from services.inference.transcript_normalizer import normalize_transcript


@pytest.mark.unit
def test_transcript_normalizer_cleans_artifacts_preserves_hesitations():
    raw_segments = [
        TranscriptSegment(
            text="Hello [noise] please... please help [inaudible]",
            start_time=0.0,
            end_time=1.5,
            confidence=0.88,
        ),
        TranscriptSegment(
            text="I... I cannot take this anymore! (laughter)",
            start_time=1.6,
            end_time=3.0,
            confidence=0.92,
        ),
    ]
    response = TranscriptResponse(segments=raw_segments, language="en")
    normalized = normalize_transcript(response)

    assert isinstance(normalized, NormalizedTranscript)
    assert "[noise]" not in normalized.text
    assert "[inaudible]" not in normalized.text
    assert "(laughter)" not in normalized.text
    # Hesitations and repetitions preserved
    assert "please... please" in normalized.text
    assert "I... I cannot" in normalized.text
    assert "asr_artifacts_cleaned" in normalized.normalization_flags
    assert len(normalized.segments) == 2


@pytest.mark.unit
def test_transcript_normalizer_empty():
    normalized = normalize_transcript("")
    assert normalized.text == ""
    assert "EMPTY_TRANSCRIPT" in normalized.normalization_flags


@pytest.mark.unit
def test_linguistic_features_english_emergency():
    text = "Please help me! He has a knife and threatens to kill me right now! I am terrified!"
    features = extract_linguistic_features(text, language="en")

    assert isinstance(features, LinguisticFeatures)
    assert features.indicator_count >= 4
    assert any("help" in ind.lower() for ind in features.help_request_indicators)
    assert any(term in ["knife", "kill", "threaten", "threatens"] for term in [t.lower() for t in features.threat_indicators])
    assert len(features.urgency_indicators) >= 1
    assert "terrified" in [ind.lower() for ind in features.fear_indicators]


@pytest.mark.unit
def test_linguistic_features_hindi_emergency():
    text = "मेरी मदद करो! वह चाकू लेकर मुझे मारने आया है, बहुत डर लग रहा है, जल्दी पुलिस भेजो!"
    features = extract_linguistic_features(text, language="hi")

    assert isinstance(features, LinguisticFeatures)
    assert features.indicator_count >= 3
    assert len(features.threat_indicators) >= 1
    assert len(features.help_request_indicators) >= 1
    assert len(features.urgency_indicators) >= 1
    assert len(features.fear_indicators) >= 1


@pytest.mark.unit
def test_linguistic_features_neutral_speech():
    text = "The bus arrives at four o'clock tomorrow afternoon."
    features = extract_linguistic_features(text)
    assert features.indicator_count == 0


@pytest.mark.unit
def test_text_distress_classifier_acute_distress():
    norm = NormalizedTranscript(
        text="Help me, he is attacking me with a weapon, please hurry right now!",
        segments=[],
        language="en",
    )
    result = classify_text_distress(norm)

    assert isinstance(result, TextInferenceResult)
    assert result.abstained is False
    assert result.score is not None
    assert result.score >= 60.0
    assert result.confidence >= 0.50
    assert any("threat" in ind for ind in result.indicators)
    assert any("help_request" in ind for ind in result.indicators)


@pytest.mark.unit
def test_text_distress_classifier_neutral():
    norm = NormalizedTranscript(
        text="I am calling to verify my account appointment for next Tuesday.",
        segments=[],
        language="en",
    )
    result = classify_text_distress(norm)

    assert result.abstained is False
    assert result.score is not None
    assert result.score <= 20.0
    assert "neutral_conversational_language" in result.indicators


@pytest.mark.unit
def test_text_distress_classifier_abstained_on_empty():
    norm = NormalizedTranscript(text="", segments=[], language="en")
    result = classify_text_distress(norm)

    assert result.abstained is True
    assert result.score is None
    assert "empty_transcript" in result.indicators
