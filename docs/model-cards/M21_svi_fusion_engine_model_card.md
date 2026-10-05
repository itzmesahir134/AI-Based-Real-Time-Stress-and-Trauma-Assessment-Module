# Model Card: M21 SVI (Stress & Vulnerability Index) Fusion Engine

## Model Overview
- **Model Name:** SaathiAI Multi-Modal SVI Fusion Engine (M21)
- **Model Version:** `v1.0.0`
- **Architecture:** Quality-adjusted, coverage-calibrated weighted fusion algorithm combining Acoustic, Linguistic, Self-Report, Contextual, and Session Interaction evidence.
- **Intended Use:** Compute a unified, explainable 0–100 triage score representing caller urgency and vulnerability for emergency help services.

---

## Mathematical Formulation

Given modalities $m \in \{\text{voice}, \text{text}, \text{self\_report}, \text{context}, \text{interaction}\}$, with configured weights $w_m$, quality metrics $q_m \in [0, 1]$, and individual scores $s_m \in [0, 100]$:

$$\text{SVI} = \frac{\sum_{m} w_m \cdot q_m \cdot s_m}{\sum_{m} w_m \cdot q_m}$$

$$\text{Coverage} = \frac{\sum_{m, q_m > 0} w_m}{\sum_{m} w_m}$$

### Evidence Coverage Status
- **COMPLETE ($\ge 75\%$):** Comprehensive multi-modal evidence across speech, text, and caller survey.
- **PARTIAL ($45\% \le \text{Coverage} < 75\%$):** Subset of modalities available (e.g., audio without self-report).
- **INSUFFICIENT_EVIDENCE ($< 45\%$):** Heavy degradation, unvoiced audio, or missing inputs; flagged for manual responder intake.

---

## Risk Band Classification & Override
- **LOW:** `0 – 24`
- **MODERATE:** `25 – 49`
- **HIGH:** `50 – 74`
- **CRITICAL:** `75 – 100` (or elevated by M23 Safety Override when `safety_flag = True`).
