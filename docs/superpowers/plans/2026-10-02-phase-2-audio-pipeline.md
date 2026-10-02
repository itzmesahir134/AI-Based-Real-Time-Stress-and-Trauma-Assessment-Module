# Phase 2: Audio Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the complete audio ingestion, quality verification, speech activity segmentation (VAD), and speech-to-text (ASR) pipeline for SAATHI-AI (Spec M04, M05, M06, M07), plus LiveKit agent integration and API endpoints.

---

## Architecture & File Map

```
c:\Projects\SaathiAI/
├── packages/
│   └── schemas/
│       └── audio.py                 # AudioQualityResult, SpeechSegment, TranscriptSegment
├── services/
│   ├── audio-worker/
│   │   ├── __init__.py
│   │   ├── quality.py               # M04 Audio Quality Analyzer (SNR, clipping, distortion)
│   │   ├── vad.py                   # M05 Voice Activity Detector (Silero/Energy-based)
│   │   ├── preprocessor.py          # M06 Audio normalizer (16kHz mono, safe peak scaling)
│   │   └── asr.py                   # M07 Speech-to-Text engine (faster-whisper pipeline)
│   └── api/
│       └── routers/
│           └── audio.py             # POST /api/v1/audio/quality, POST /api/v1/audio/transcribe
├── apps/
│   └── realtime-agent/
│       ├── __init__.py
│       └── agent.py                 # LiveKit WebRTC worker bridge (subscribes to audio stream)
└── tests/
    ├── unit/
    │   ├── test_audio_quality.py    # SNR, clipping ratio, distortion flag tests
    │   └── test_vad.py              # Speech segment boundary & silence trimming tests
    └── integration/
        └── test_audio_api.py        # /api/v1/audio/quality and /api/v1/audio/transcribe tests
```

---

## Tasks

### Task 1: Audio Contracts & Schemas (`packages/schemas/audio.py`)
- [ ] Define `AudioQualityResult` with `quality_score` (0..1), `snr_estimate`, `clipping_ratio`, `speech_ratio`, `packet_loss`, `distortion_flags` per Spec M04.
- [ ] Define `SpeechSegment` with `start_time`, `end_time`, `confidence` per Spec M05.
- [ ] Define `TranscriptSegment` and `TranscriptResponse` with timestamped segments, detected language, and full text per Spec M07.
- [ ] Export audio schemas from `packages/schemas/__init__.py`.

### Task 2: Audio Quality Analyzer (M04) (`services/audio-worker/quality.py`)
- [ ] Implement `analyze_audio_quality(audio_data, sample_rate)` using NumPy.
- [ ] Compute clipping ratio (samples near ±1.0 amplitude).
- [ ] Compute estimated SNR (ratio of active signal power to estimated noise floor).
- [ ] Compute distortion flags (`CLIPPING_DETECTED`, `HIGH_NOISE_FLOOR`, `LOW_AMPLITUDE`).
- [ ] Calculate composite `quality_score` (0.0 to 1.0) where degraded audio penalizes downstream voice weighting.

### Task 3: Voice Activity Detection (M05) & Normalization (M06) (`services/audio-worker/vad.py`, `services/audio-worker/preprocessor.py`)
- [ ] Implement `preprocess_audio(audio_data, sample_rate, target_sr=16000)` ensuring 16kHz mono format and non-destructive peak normalization.
- [ ] Implement `detect_voice_activity(audio_data, sample_rate)` returning timestamped `SpeechSegment` list.

### Task 4: Speech-to-Text Engine (M07) (`services/audio-worker/asr.py`)
- [ ] Implement `Transcriber` class wrapping `faster-whisper` with automatic language detection (supporting Hindi, Tamil, Telugu, English) and model fallback.
- [ ] Produce structured `TranscriptResponse` with word/phrase timestamps and segment confidence.

### Task 5: Audio API Endpoints (`services/api/routers/audio.py`)
- [ ] Create `POST /api/v1/audio/quality` endpoint accepting WAV/PCM binary payload.
- [ ] Create `POST /api/v1/audio/transcribe` endpoint returning transcript and quality report.
- [ ] Register `audio_router` in `services/api/main.py`.

### Task 6: LiveKit Real-Time Agent Bridge (`apps/realtime-agent/agent.py`)
- [ ] Implement LiveKit agent entrypoint that connects to configured room URL and dispatches audio frames to `AudioWorker`.

### Task 7: Unit & Integration Tests & Verification
- [ ] Write unit tests for audio quality (synthetic clear vs noisy vs clipped audio).
- [ ] Write unit tests for VAD speech segmentation.
- [ ] Write integration tests for `/api/v1/audio/quality` and `/api/v1/audio/transcribe`.
- [ ] Run full test suite with pytest and verify all tests pass.
- [ ] Commit and push Phase 2 deliverables to GitHub.
