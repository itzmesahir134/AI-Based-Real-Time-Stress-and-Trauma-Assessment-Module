# SAATHI-AI Audio Pipeline Test Matrix

This matrix maps each audio sample in the test collection to its testing capability.

> [!IMPORTANT]
> **Dataset Rule:** Emotional labels (fear, anger, sadness, etc.) represent acoustic and affective
> vocalizations. They are **NOT** equivalent to trauma. Never map emotion signals into 'trauma'.

| Sample | Dataset | Language | Category | Quality | Purpose |
|---|---|---|---|---|---|
| CLEAN_001 | CREMA-D | English | clean | clean | Baseline pipeline testing (Male, normal speed) |
| CLEAN_002 | CREMA-D | English | clean | clean | Baseline pipeline testing (Female, normal speed) |
| CLEAN_003 | CREMA-D | English | clean | clean | Baseline pipeline testing (Female, normal speed) |
| CLEAN_004 | CREMA-D | English | clean | clean | Baseline pipeline testing (Female, deliberate speed) |
| CLEAN_005 | CREMA-D | English | clean | clean | Baseline pipeline testing (Male, moderate speed) |
| CLEAN_006 | CREMA-D | English | clean | clean | Baseline pipeline testing (Female, fast speed) |
| CLEAN_007 | RAVDESS | English | clean | clean | Baseline pipeline testing (Male, normal speed) |
| CLEAN_008 | RAVDESS | English | clean | clean | Baseline pipeline testing (Female, normal speed) |
| EMO_001 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (neutral, normal) |
| EMO_002 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (calm, normal) |
| EMO_003 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (calm, normal) |
| EMO_004 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (happiness, normal) |
| EMO_005 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (happiness, low) |
| EMO_006 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (happiness, normal) |
| EMO_007 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (sadness, normal) |
| EMO_008 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (sadness, high) |
| EMO_009 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (sadness, normal) |
| EMO_010 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (fear, normal) |
| EMO_011 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (fear, medium) |
| EMO_012 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (fear, normal) |
| EMO_013 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (fear, strong) |
| EMO_014 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (anger, normal) |
| EMO_015 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (anger, high) |
| EMO_016 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (anger, normal) |
| EMO_017 | RAVDESS | English | emotional | clean | Acoustic/emotion testing (anger, strong) |
| EMO_018 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (disgust, normal) |
| EMO_019 | CREMA-D | English | emotional | clean | Acoustic/emotion testing (disgust, medium) |
| CONV_001 | AI4Bharat | Marathi | conversational | clean | Conversational/spontaneous condition (Marathi, Female) |
| CONV_002 | AI4Bharat | Marathi | conversational | clean | Conversational/spontaneous condition (Marathi, Male) |
| CONV_003 | AI4Bharat | Punjabi | conversational | clean | Conversational/spontaneous condition (Punjabi, Female) |
| CONV_004 | CREMA-D | English | conversational | clean | Conversational/spontaneous condition (English, Female) |
| CONV_005 | CREMA-D | English | conversational | clean | Conversational/spontaneous condition (English, Male) |
| CONV_006 | CREMA-D | English | conversational | clean | Conversational/spontaneous condition (English, Female) |
| IND_001 | IndicVoices / AI4Bharat | Marathi | indian_languages | clean | Indian-language speech handling & ASR (Marathi) |
| IND_002 | IndicVoices / AI4Bharat | Marathi | indian_languages | clean | Indian-language speech handling & ASR (Marathi) |
| IND_003 | IndicVoices / AI4Bharat | Marathi | indian_languages | clean | Indian-language speech handling & ASR (Marathi) |
| IND_004 | IndicVoices / AI4Bharat | Marathi | indian_languages | clean | Indian-language speech handling & ASR (Marathi) |
| IND_005 | IndicVoices / AI4Bharat | Marathi | indian_languages | clean | Indian-language speech handling & ASR (Marathi) |
| IND_006 | IndicVoices / AI4Bharat | Tamil | indian_languages | clean | Indian-language speech handling & ASR (Tamil) |
| IND_007 | IndicVoices / AI4Bharat | Tamil | indian_languages | clean | Indian-language speech handling & ASR (Tamil) |
| IND_008 | IndicVoices / AI4Bharat | Tamil | indian_languages | clean | Indian-language speech handling & ASR (Tamil) |
| IND_009 | IndicVoices / AI4Bharat | Telugu | indian_languages | clean | Indian-language speech handling & ASR (Telugu) |
| IND_010 | IndicVoices / AI4Bharat | Telugu | indian_languages | clean | Indian-language speech handling & ASR (Telugu) |
| IND_011 | IndicVoices / AI4Bharat | Kannada | indian_languages | clean | Indian-language speech handling & ASR (Kannada) |
| IND_012 | IndicVoices / AI4Bharat | Punjabi | indian_languages | clean | Indian-language speech handling & ASR (Punjabi) |
| IND_013 | IndicVoices / AI4Bharat | Punjabi | indian_languages | clean | Indian-language speech handling & ASR (Punjabi) |
| IND_014 | IndicVoices / AI4Bharat | Gujarati | indian_languages | clean | Indian-language speech handling & ASR (Gujarati) |
| IND_015 | IndicVoices / AI4Bharat | Gujarati | indian_languages | clean | Indian-language speech handling & ASR (Gujarati) |
| IND_016 | Standard Hindi | Hindi | indian_languages | clean | Indian-language speech handling & ASR (Hindi) |
| EDGE_001 | CREMA-D | English | edge_cases | clean | Very short speech burst handling (< 1.0s) |
| EDGE_002 | Synthetic_Reference | None | edge_cases | silence | Pipeline silence rejection and zero-VAD test |
| EDGE_003 | CREMA-D | English | edge_cases | clean | Extended long-speech handling (> 10s) |
| EDGE_004 | CREMA-D | English | edge_cases | low_snr | Faint whisper and low-SNR detection robustness |
| AUG_001 | CREMA-D | English | augmented | noise | Acoustic robustness test: additive_noise (noise) |
| AUG_002 | CREMA-D | English | augmented | traffic | Acoustic robustness test: traffic_noise (traffic) |
| AUG_003 | CREMA-D | English | augmented | low_volume | Acoustic robustness test: low_volume (low_volume) |
| AUG_004 | CREMA-D | English | augmented | clipped | Acoustic robustness test: clipping (clipped) |
| AUG_005 | CREMA-D | English | augmented | reverb | Acoustic robustness test: reverberation (reverb) |
| AUG_006 | CREMA-D | English | augmented | compressed | Acoustic robustness test: compression_artifacts (compressed) |
| AUG_007 | CREMA-D | English | augmented | bandlimited | Acoustic robustness test: reduced_bandwidth (bandlimited) |
| AUG_008 | CREMA-D | English | augmented | silence_inserted | Acoustic robustness test: silence_insertion (silence_inserted) |
| AUG_009 | CREMA-D | English | augmented | truncated | Acoustic robustness test: partial_truncation (truncated) |
| AUG_010 | CREMA-D | English | augmented | noise | Acoustic robustness test: additive_noise (noise) |
| AUG_011 | CREMA-D | English | augmented | traffic | Acoustic robustness test: traffic_noise (traffic) |
| AUG_012 | CREMA-D | English | augmented | low_volume | Acoustic robustness test: low_volume (low_volume) |
| AUG_013 | CREMA-D | English | augmented | clipped | Acoustic robustness test: clipping (clipped) |
| AUG_014 | CREMA-D | English | augmented | reverb | Acoustic robustness test: reverberation (reverb) |
| AUG_015 | CREMA-D | English | augmented | compressed | Acoustic robustness test: compression_artifacts (compressed) |
| AUG_016 | CREMA-D | English | augmented | bandlimited | Acoustic robustness test: reduced_bandwidth (bandlimited) |
| AUG_017 | CREMA-D | English | augmented | silence_inserted | Acoustic robustness test: silence_insertion (silence_inserted) |
| AUG_018 | CREMA-D | English | augmented | truncated | Acoustic robustness test: partial_truncation (truncated) |
| AUG_019 | CREMA-D | English | augmented | noise | Acoustic robustness test: additive_noise (noise) |
| AUG_020 | CREMA-D | English | augmented | traffic | Acoustic robustness test: traffic_noise (traffic) |
| AUG_021 | CREMA-D | English | augmented | low_volume | Acoustic robustness test: low_volume (low_volume) |
| AUG_022 | CREMA-D | English | augmented | clipped | Acoustic robustness test: clipping (clipped) |
| AUG_023 | CREMA-D | English | augmented | reverb | Acoustic robustness test: reverberation (reverb) |
| AUG_024 | CREMA-D | English | augmented | compressed | Acoustic robustness test: compression_artifacts (compressed) |
| AUG_025 | CREMA-D | English | augmented | bandlimited | Acoustic robustness test: reduced_bandwidth (bandlimited) |
| AUG_026 | CREMA-D | English | augmented | silence_inserted | Acoustic robustness test: silence_insertion (silence_inserted) |
| AUG_027 | CREMA-D | English | augmented | truncated | Acoustic robustness test: partial_truncation (truncated) |
| AUG_028 | IndicVoices | Marathi | augmented | noise | Acoustic robustness test: additive_noise (noise) |
| AUG_029 | IndicVoices | Marathi | augmented | traffic | Acoustic robustness test: traffic_noise (traffic) |
| AUG_030 | IndicVoices | Marathi | augmented | low_volume | Acoustic robustness test: low_volume (low_volume) |
| AUG_031 | IndicVoices | Marathi | augmented | clipped | Acoustic robustness test: clipping (clipped) |
| AUG_032 | IndicVoices | Marathi | augmented | reverb | Acoustic robustness test: reverberation (reverb) |
| AUG_033 | IndicVoices | Marathi | augmented | compressed | Acoustic robustness test: compression_artifacts (compressed) |
| AUG_034 | IndicVoices | Marathi | augmented | bandlimited | Acoustic robustness test: reduced_bandwidth (bandlimited) |
| AUG_035 | IndicVoices | Marathi | augmented | silence_inserted | Acoustic robustness test: silence_insertion (silence_inserted) |
| AUG_036 | IndicVoices | Marathi | augmented | truncated | Acoustic robustness test: partial_truncation (truncated) |
