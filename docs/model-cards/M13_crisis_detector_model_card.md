# Model Card: M13 Crisis Detector & Safety Guard

## Model Overview
- **Model Name:** SaathiAI Deterministic Crisis & Immediate Threat Detector (M13)
- **Model Version:** `v1.0.0-zero-miss-rule-engine`
- **Architecture:** Dual-layer zero-suppression safety detector combining high-priority regular expression token scanning with structured self-report question triggers.
- **Intended Use:** Instantly flag life-threatening emergencies (suicide/self-harm ideation, domestic violence with weapons, ongoing physical attacks) to trigger immediate human escalation, overriding statistical scoring.

---

## Crisis Categories Monitored
1. **Immediate Violence / Weapon Threat:** Active physical attacks, weapons drawn, home invasion.
2. **Suicide & Self-Harm Ideation:** Explicit intentions to end life, overdose, self-injury.
3. **Severe Medical Emergency:** Loss of consciousness, severe bleeding, choking, overdose.
4. **Child & Vulnerable Person Endangerment:** Minors trapped, physical abuse of vulnerable dependents.

---

## Core Safety Invariant
> **"Zero Model Silent Suppression":** The deterministic rule layer executes unconditionally before any ML scoring. If a critical keyword or safety answer (`q2 >= 3` or `q3 == 4`) is present, `safety_flag = True` is triggered unconditionally with `1.0` confidence, regardless of network or downstream ML model latency.
