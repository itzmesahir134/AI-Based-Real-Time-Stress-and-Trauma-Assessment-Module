# Model Card: M09 Voice Distress Indicator

## Model Overview
- **Model Name:** SaathiAI Voice Distress Indicator (M09)
- **Model Version:** `v1.1.0-gb-ensemble`
- **Architecture:** 26-dimensional acoustic & prosodic feature extractor paired with a Gradient Boosting Regressor ensembled with rule-calibrated prosodic dynamics.
- **Primary Domain:** Helpline audio triage for psychological distress, panic, and acute vocal instability.
- **Intended Use:** Assist emergency responders by highlighting non-verbal vocal distress signals (pitch jitter, tremor, abrupt pauses, speech rate spikes) to prioritize intake queues.

---

## Model Inputs & Outputs

### Inputs
- **Sampling Rate:** 16,000 Hz mono PCM audio.
- **Acoustic Features (M08):**
  - Pitch Dynamics: `pitch_mean`, `pitch_std`, `pitch_range` (via Yin / autocorrelation).
  - Perturbation: `jitter` (pitch variation), `shimmer` (amplitude variation).
  - Energy & Spectral: `energy_mean`, `energy_std`, `spectral_centroid_mean`, `zcr_mean`.
  - Temporal & Prosodic: `speech_rate_syl_per_sec`, `pause_ratio`, `pause_count`, `voiced_fraction`.
  - Cepstral: 13 Mel-Frequency Cepstral Coefficients (`mfcc_0` .. `mfcc_12`).

### Outputs
- **Voice Distress Score:** Continuous index from `0.0` (calm/baseline) to `100.0` (acute vocal panic/agitation).
- **Calibrated Confidence:** Range `0.0` to `1.0`, scaled by audio quality and voiced speech fraction.
- **Evidence Tags:** Up to 4 top contributing prosodic factors (e.g. `elevated_pitch_variability`, `vocal_perturbation_tremor`, `speech_disruptions_and_pauses`).
- **Abstention Flag:** `True` if audio quality is below threshold (`quality_score < 0.15`) or unvoiced.

---

## Ethical Considerations & Bias Mitigation

1. **Dialect and Accent Diversity:** Pitch base levels naturally vary across biological sex, age, and regional dialects. M09 standardizes pitch metrics against dynamic dynamic ranges rather than absolute fixed pitch cutoffs.
2. **Quality Gating & Abstention:** M09 explicitly abstains rather than producing hallucinated high-distress scores on low SNR, clipped, or distorted phone line audio.
3. **Non-Diagnostic Disclaimer:** This model is not a clinical diagnostic tool for psychiatric trauma. It measures real-time vocal arousal and distress indicators strictly for triage prioritization.
