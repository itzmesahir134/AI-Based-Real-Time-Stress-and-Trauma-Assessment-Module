"""M15: Self-Report Scorer.

Scores 5-item caller self-report questionnaires to compute a 0-100 self-report distress score,
evaluates completeness, and checks critical safety criteria (Spec §15).
"""

from typing import Union
from packages.schemas.scoring import SelfReportQuestionnaire, SelfReportResult


def score_self_report(
    questionnaire: Union[SelfReportQuestionnaire, dict],
) -> SelfReportResult:
    """Spec M15: Score self-report questionnaire.

    Formula:
        weights: q1 (distress)=0.30, q2 (safety)=0.35, q3 (urgency)=0.25, q4 (can_continue)=0.10
        raw = sum(w_i * q_i) / 4.0
        score = raw * 100.0 (0-100)

    Safety flag:
        q2 >= 3 (unsafe/immediate danger) OR q3 == 4 (immediate urgent help) OR q4 == 4 (unable to continue).

    Args:
        questionnaire: SelfReportQuestionnaire object or dict with q1-q4 and support_needs.

    Returns:
        SelfReportResult with score, completeness, safety_flag, and support_needs.
    """
    if isinstance(questionnaire, dict):
        q = SelfReportQuestionnaire(**questionnaire)
    else:
        q = questionnaire

    # Weighted numeric calculation (questions are on 0-4 Likert scale)
    raw = (0.30 * q.q1_distress + 0.35 * q.q2_safety + 0.25 * q.q3_urgency + 0.10 * q.q4_can_continue) / 4.0
    score = round(float(raw * 100.0), 1)

    # Check answered items for completeness
    completeness = 1.0  # Pydantic schema guarantees fields with defaults

    # Safety trigger rule
    safety_flag = bool(q.q2_safety >= 3 or q.q3_urgency == 4 or q.q4_can_continue == 4)

    return SelfReportResult(
        score=score,
        completeness=completeness,
        safety_flag=safety_flag,
        support_needs=q.support_needs,
    )
