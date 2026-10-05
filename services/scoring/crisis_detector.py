"""M13: Crisis Detector.

Two-layer crisis detection engine (Spec §13, §23):
Layer 1: Deterministic rule-based evaluation of explicit suicidal ideation,
         lethal threats, and critical self-report triggers. Must never fail silently.
Layer 2: Multimodal heuristic corroboration.
"""

from typing import List, Optional, Union
import re

from packages.schemas.scoring import ContextData, CrisisResult, SelfReportQuestionnaire, SelfReportResult
from packages.schemas.text import NormalizedTranscript

# High-priority crisis patterns (English, Hindi Devanagari, Hinglish)
_SUICIDE_PATTERNS = [
    re.compile(r"\b(kill myself|commit suicide|end my life|want to die|take my own life|hanging myself|swallowed pills)\b", re.IGNORECASE),
    re.compile(r"(आत्महत्या|खुदकुशी|मरना चाहता|मरना चाहती|जान दे दूंगी|जान दे दूंगा)"),
    re.compile(r"\b(mar jaunga|mar jaungi|khudkushi|jaan de dung[ai])\b", re.IGNORECASE),
]

_LETHAL_THREAT_PATTERNS = [
    re.compile(r"\b(has a gun|has a knife|he'?s gonna kill me|trying to kill me|gonna shoot|stab me|stabbed|strangling me|choking me to death)\b", re.IGNORECASE),
    re.compile(r"(बंदूक तान|चाकू मार|जान से मार देगा|जान से मार देगी|गला घोंट रहा|गोली मार)"),
    re.compile(r"\b(bandook|chaaku maar|goli maar|jaan se maar)\b", re.IGNORECASE),
]


def detect_crisis(
    transcript: Optional[Union[NormalizedTranscript, str]] = None,
    self_report: Optional[Union[SelfReportQuestionnaire, SelfReportResult, dict]] = None,
    context: Optional[Union[ContextData, dict]] = None,
) -> CrisisResult:
    """Spec M13: Two-layer crisis detection engine.

    Args:
        transcript: Optional transcript text or NormalizedTranscript.
        self_report: Optional SelfReport questionnaire or scored result.
        context: Optional ContextData or context dict.

    Returns:
        CrisisResult with safety_flag, crisis_type, evidence, and rule_triggered status.
    """
    evidence: List[str] = []
    crisis_type: Optional[str] = None
    rule_triggered = False

    # 1. Deterministic Transcript Scan
    text = ""
    if transcript is not None:
        text = transcript.text if isinstance(transcript, NormalizedTranscript) else str(transcript)

    if text:
        # Check suicidal ideation
        for pat in _SUICIDE_PATTERNS:
            match = pat.search(text)
            if match:
                evidence.append(f"suicidal_ideation_phrase: '{match.group(0)}'")
                crisis_type = "suicidal_ideation"
                rule_triggered = True
                break

        # Check lethal / violent threat
        for pat in _LETHAL_THREAT_PATTERNS:
            match = pat.search(text)
            if match:
                evidence.append(f"lethal_threat_phrase: '{match.group(0)}'")
                if not crisis_type:
                    crisis_type = "immediate_threat"
                rule_triggered = True
                break

    # 2. Deterministic Self-Report Scan
    if self_report is not None:
        if isinstance(self_report, SelfReportResult):
            if self_report.safety_flag:
                evidence.append("self_report_safety_flag_active")
                if not crisis_type:
                    crisis_type = "immediate_threat"
                rule_triggered = True
        elif isinstance(self_report, SelfReportQuestionnaire):
            if self_report.q2_safety >= 3:
                evidence.append(f"self_report_danger_level_{self_report.q2_safety}")
                if not crisis_type:
                    crisis_type = "immediate_threat"
                rule_triggered = True
            if self_report.q3_urgency == 4:
                evidence.append("self_report_critical_urgency")
                rule_triggered = True
        elif isinstance(self_report, dict):
            q2 = int(self_report.get("q2_safety", 0))
            q3 = int(self_report.get("q3_urgency", 0))
            if q2 >= 3 or q3 == 4:
                evidence.append("self_report_danger_threshold_exceeded")
                if not crisis_type:
                    crisis_type = "immediate_threat"
                rule_triggered = True

    # 3. Context Scan
    if context is not None:
        ongoing = context.ongoing_threat if isinstance(context, ContextData) else bool(context.get("ongoing_threat", False))
        immediate = context.immediate_support_requested if isinstance(context, ContextData) else bool(context.get("immediate_support_requested", False))
        if ongoing and immediate:
            evidence.append("active_ongoing_threat_with_escalation_request")
            if not crisis_type:
                crisis_type = "acute_threat"
            rule_triggered = True

    safety_flag = rule_triggered
    confidence = 0.99 if rule_triggered else 0.0

    return CrisisResult(
        safety_flag=safety_flag,
        crisis_type=crisis_type,
        confidence=confidence,
        evidence=evidence,
        rule_triggered=rule_triggered,
        model_triggered=False,
    )
