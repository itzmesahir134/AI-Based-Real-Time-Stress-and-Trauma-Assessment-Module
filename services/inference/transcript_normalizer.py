"""M10: Transcript Normalizer.

Standardizes Whisper/ASR transcripts by removing acoustic artifact tags,
normalizing Unicode (NFC), and cleaning whitespace while strictly preserving
hesitations, repetitions, and emotional exclamations required as psychological distress evidence.
"""

from typing import List, Optional, Union
import re
import unicodedata

from packages.schemas.audio import TranscriptResponse, TranscriptSegment
from packages.schemas.text import NormalizedSegment, NormalizedTranscript

# Regex for non-linguistic ASR artifact markers
_ASR_ARTIFACT_RE = re.compile(
    r"\[\s*(inaudible|unintelligible|noise|applause|laughter|music|cough|sigh|silence|whisper|groan)\s*\]|"
    r"\(\s*(inaudible|unintelligible|noise|applause|laughter|music|cough|sigh|silence|whisper|groan)\s*\)|"
    r"<\s*(inaudible|unintelligible|noise|applause|laughter|music|cough|sigh|silence|whisper|groan)\s*>",
    re.IGNORECASE,
)

_MULTISPACE_RE = re.compile(r"[ \t]+")


def normalize_transcript(
    transcript: Union[TranscriptResponse, List[Union[TranscriptSegment, dict]], str],
    language: str = "en",
) -> NormalizedTranscript:
    """Spec M10: Normalize raw transcript while preserving emotional/distress markers.

    Args:
        transcript: TranscriptResponse, list of TranscriptSegments/dicts, or raw text string.
        language: Language code (e.g. 'en', 'hi', 'mr').

    Returns:
        NormalizedTranscript object.
    """
    flags: List[str] = []

    # 1. Extract raw segments and language
    raw_segments: List[tuple[str, float, float, float]] = []
    if isinstance(transcript, TranscriptResponse):
        language = transcript.language or language
        for seg in transcript.segments:
            raw_segments.append((seg.text, seg.start_time, seg.end_time, seg.confidence))
    elif isinstance(transcript, list):
        for item in transcript:
            if isinstance(item, TranscriptSegment):
                raw_segments.append((item.text, item.start_time, item.end_time, item.confidence))
            elif isinstance(item, dict):
                raw_segments.append((
                    item.get("text", ""),
                    float(item.get("start_time", 0.0)),
                    float(item.get("end_time", 0.0)),
                    float(item.get("confidence", 1.0)),
                ))
    elif isinstance(transcript, str):
        if not transcript.strip():
            return NormalizedTranscript(text="", segments=[], normalization_flags=["EMPTY_TRANSCRIPT"], language=language)
        raw_segments.append((transcript, 0.0, 0.0, 1.0))

    if not raw_segments:
        return NormalizedTranscript(text="", segments=[], normalization_flags=["EMPTY_TRANSCRIPT"], language=language)


    # 2. Process segments
    cleaned_segments: List[NormalizedSegment] = []
    has_artifact_removal = False
    has_nfc = False

    for text, start, end, conf in raw_segments:
        if not text:
            continue

        # Check NFC
        nfc_text = unicodedata.normalize("NFC", text)
        if nfc_text != text:
            has_nfc = True
        text = nfc_text

        # Strip ASR bracketed/parenthesized non-speech artifact tokens
        cleaned_text, num_subs = _ASR_ARTIFACT_RE.subn(" ", text)
        if num_subs > 0:
            has_artifact_removal = True

        # Collapse whitespace within the segment
        cleaned_text = _MULTISPACE_RE.sub(" ", cleaned_text).strip()

        if cleaned_text:
            cleaned_segments.append(
                NormalizedSegment(
                    text=cleaned_text,
                    start_time=round(start, 3),
                    end_time=round(end, 3),
                    confidence=round(conf, 3),
                )
            )

    if not cleaned_segments:
        return NormalizedTranscript(text="", segments=[], normalization_flags=["EMPTY_TRANSCRIPT"], language=language)

    if has_artifact_removal:
        flags.append("asr_artifacts_cleaned")

    if has_nfc:
        flags.append("unicode_nfc_normalized")
    flags.append("whitespace_cleaned")

    full_text = " ".join(seg.text for seg in cleaned_segments)

    return NormalizedTranscript(
        text=full_text,
        segments=cleaned_segments,
        normalization_flags=flags,
        language=language,
    )
