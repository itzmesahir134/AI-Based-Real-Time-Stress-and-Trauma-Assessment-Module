# SAATHI-AI Audio Test Sample Collection & Management Utilities

This directory contains the curated benchmark audio collection and dataset management utilities built specifically to evaluate and stress-test the **SAATHI-AI Phase 1 Audio Processing Pipeline** (`services.audio_worker`).

---

## Important Dataset Rule

> [!IMPORTANT]
> **DO NOT call these "trauma samples".**
> Emotion, fear, sadness, anger, acoustic stress, and vocal agitation are **NOT equivalent to psychological trauma**.
> Use each benchmark dataset strictly for the capability it actually supports (acoustic diagnostics, emotion classification, language recognition, noise robustness, VAD segmentation). Never convert or map emotion labels into trauma flags.

---

## Directory Structure

```text
test_audio/
├── original/                   # Original downloaded audio files (untouched in native format)
│   ├── crema_d/                # 32 clips (16kHz mono WAV, 6 actors, 6 emotions)
│   ├── ravdess/                # 16 clips (48kHz stereo WAV, 2 actors, 8 emotions)
│   ├── iemocap/                # Drop-in folder for USC SAIL EULA-cleared conversational clips
│   ├── msp_podcast/            # Drop-in folder for UT Dallas MSP EULA-cleared podcast clips
│   └── indicvoices/            # 19 clips (48kHz/16kHz crowdsourced & prompt speech across 7 languages)
│
├── curated/                    # Normalized testing format (WAV, 16,000 Hz, Mono, 16-bit PCM)
│   ├── clean/                  # Baseline speech (male/female, diverse accents, speaking speeds)
│   ├── emotional/              # Affective vocalizations (neutral, calm, happy, sad, fear, anger, disgust)
│   ├── conversational/         # Spontaneous speech, conversational turns, natural pauses
│   ├── indian_languages/       # Multilingual Indian speech (Hindi, Marathi, Tamil, Telugu, Kannada, Punjabi, Gujarati)
│   └── edge_cases/             # Short bursts (<1s), extended speech (>10s), faint whisper, digital silence
│
├── augmented/                  # Controlled acoustic quality variants derived from clean baselines
│   ├── noise/                  # Additive Gaussian background noise (12 dB SNR) & low-freq traffic rumble (10 dB SNR)
│   ├── low_volume/             # Attenuated signal (-18 dB attenuation)
│   ├── clipping/               # Harsh digital clipping (3.8x gain boost, hard-clipped at 0.95)
│   ├── reverb/                 # Room acoustic reverberation (RT60 = 0.45s exponential decay convolution)
│   ├── compression/            # Dynamic range compression (tanh) + 8-bit quantization artifacts
│   ├── bandwidth/              # Telephony G.711 bandpass filtering (300 Hz - 3400 Hz 4th-order Butterworth)
│   ├── silence/                # Silence insertion (1.0s leading, 1.5s middle pause, 1.0s trailing)
│   └── truncated/              # Abrupt mid-utterance truncation (40% cutoff)
│
├── metadata/                   # Comprehensive machine-readable registries & test matrix
│   ├── samples.csv             # Full metadata registry (sample ID, speaker, language, label, parameters)
│   ├── sources.csv             # Specifications for the 5 benchmark sources (license, citations, formats)
│   ├── test_matrix.csv         # Matrix mapping each sample to tested pipeline capabilities
│   └── test_matrix.md          # Formatted Markdown test matrix table
│
├── DATASET_GUIDE.md            # Detailed acquisition, licensing, and ethical guidelines
└── README.md                   # This usage guide
```

---

## Normalized Sample Format

All test samples in `curated/` and `augmented/` are strictly normalized to:
- **Container / Codec:** WAV (uncompressed RIFF header)
- **Channels:** 1 (Mono)
- **Sampling Rate:** 16,000 Hz (16 kHz standard for Whisper ASR and VAD models)
- **Bit Depth:** 16-bit PCM signed integer

> [!NOTE]
> The source files in `test_audio/original/` remain completely untouched in their native format (whether 48 kHz stereo, 24-bit, or raw container format).

---

## Dataset Catalog Overview

| Dataset | Official Source | License | Access Method | Languages | Speakers |
|---|---|---|---|---|---|
| **CREMA-D** | [Cheyney GitHub](https://github.com/CheyneyComputerScience/CREMA-D) | ODbL v1.0 | Open Access / Direct HTTP | English | 91 (Diverse) |
| **RAVDESS** | [Zenodo 1188976](https://zenodo.org/records/1188976) | CC BY-NC-SA 4.0 | Open Mirror Range Fetch | English | 24 (Actors) |
| **IndicVoices / AI4Bharat** | [AI4Bharat IIT Madras](https://ai4bharat.iitm.ac.in/indicvoices/) / [OpenSLR](https://www.openslr.org) | CC BY 4.0 / CC BY-SA 4.0 | Open Access / Range Fetch | 7+ Indian Langs | >22,000 |
| **IEMOCAP** | [USC SAIL Lab](https://sail.usc.edu/iemocap/) | USC Academic EULA | Gated Academic Request | English | 10 (Dyads) |
| **MSP-Podcast** | [UT Dallas MSP Lab](https://ecs.utdallas.edu/research/researchlabs/msp-lab/) | UT Dallas EULA | Gated Academic Request | English | >1,200 |

Detailed citations, terms, and EULA application steps are in [DATASET_GUIDE.md](file:///c:/Projects/SaathiAI/test_audio/DATASET_GUIDE.md).

---

## Workflow Commands

### 1. List Benchmark Datasets
Inspect specifications, licenses, speaker counts, and local sample availability:
```bash
python -m tools.list_datasets
python -m tools.list_datasets --dataset crema_d
python -m tools.list_datasets --json
```

### 2. Download Curated Subsets
Download representative audio files without downloading massive multi-gigabyte corpora:
```bash
python -m tools.download_dataset crema_d
python -m tools.download_dataset ravdess
python -m tools.download_dataset indicvoices
python -m tools.download_dataset iemocap        # Prints EULA steps & checks drop-in folder
python -m tools.download_dataset msp_podcast    # Prints EULA steps & checks drop-in folder
python -m tools.download_dataset all
```

### 3. Generate Audio Test Variants
Generate controlled quality variants (noise, clipping, reverb, bandpass, etc.) from any clean WAV file:
```bash
python -m tools.create_variants test_audio/curated/clean/CLEAN_001_male_normal.wav --out-dir scratch/variants
# Or via convenience script:
python create_test_variants.py test_audio/curated/clean/CLEAN_001_male_normal.wav
```

### 4. Build Test Collection
Processes downloaded files, normalizes to 16kHz mono WAV, generates augmented variants, and updates `samples.csv` and `test_matrix.csv`:
```bash
python -m tools.build_test_set
```

### 5. Validate Test Audio Files
Runs comprehensive checks on all audio files (WAV validity, 16kHz, mono, duration, clipping, silence, duplicate hashes, metadata completeness):
```bash
python -m tools.validate_test_audio
python -m tools.validate_test_audio --verbose
```

### 6. Test the Existing Phase 1 Audio Pipeline
Feeds test samples into the existing `services.audio_worker` modules (M04 Quality Diagnostics, M05 VAD, M07 ASR):
```bash
# Test 5 representative samples
python -m tools.test_pipeline --limit 5

# Test specific categories
python -m tools.test_pipeline --category clean
python -m tools.test_pipeline --category emotional
python -m tools.test_pipeline --category indian_languages
python -m tools.test_pipeline --category augmented
python -m tools.test_pipeline --category edge_cases

# Test an individual sample
python -m tools.test_pipeline --sample-id CLEAN_001
python -m tools.test_pipeline --sample-id IND_001
python -m tools.test_pipeline --sample-id AUG_004
python -m tools.test_pipeline --sample-id EDGE_002
```

---

## Feeding Test Samples into Phase 1 Pipeline

### Method A: Direct Python Integration
```python
from services.audio_worker import (
    bytes_to_pcm_array,
    preprocess_audio,
    analyze_audio_quality,
    detect_voice_activity,
    Transcriber
)

# Load test sample
with open("test_audio/curated/clean/CLEAN_001_male_normal.wav", "rb") as f:
    audio_bytes = f.read()

# 1. Decode to PCM array
audio, sr = bytes_to_pcm_array(audio_bytes)

# 2. Analyze Audio Quality (M04)
quality = analyze_audio_quality(audio, sample_rate=sr)
print("Quality Score:", quality.quality_score)
print("SNR Estimate:", quality.snr_estimate, "dB")
print("Clipping Ratio:", quality.clipping_ratio)
print("Distortion Flags:", quality.distortion_flags)

# 3. Voice Activity Detection (M05)
segments = detect_voice_activity(audio, sample_rate=sr)
print("Speech bursts detected:", len(segments))

# 4. Neural Speech-to-Text (M07)
transcriber = Transcriber(model_size="tiny")
cleaned_audio, cleaned_sr = preprocess_audio(audio, orig_sr=sr)
transcript = transcriber.transcribe(cleaned_audio, sample_rate=cleaned_sr)
print("Detected Language:", transcript.language)
print("Full Text:", transcript.full_text)
```

### Method B: REST API Endpoints
When running the SAATHI-AI backend (`npm run dev:api` or `uvicorn services.api.main:app --port 8000`):

1. **Quality Check Endpoint (`POST /api/v1/audio/quality`):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/audio/quality" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio/curated/clean/CLEAN_001_male_normal.wav"
   ```

2. **Transcription Endpoint (`POST /api/v1/audio/transcribe`):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/audio/transcribe?language=en" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio/curated/clean/CLEAN_001_male_normal.wav"
   ```

3. **Indian Language Transcription (`POST /api/v1/audio/transcribe`):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/audio/transcribe?language=mr" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio/curated/indian_languages/IND_001_mr_MAR_F_HAPPY_00001.wav"
   ```
