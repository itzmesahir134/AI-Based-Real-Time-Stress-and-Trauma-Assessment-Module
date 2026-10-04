# Audio Data Aggregation & Module Pipeline I/O Foundation — Implementation Plan

> **For agentic workers:** Use `executing-plans` skill to implement task-by-task.

**Goal:** Aggregate all available + downloadable audio datasets into correctly structured module input folders, run Phase 1 modules (M04→M06→M05→M07) in batch, and produce structured JSON output per file.

**Architecture:** A `pipeline_config.py` module is the single source of truth for all I/O paths. `populate_inputs.py` copies audio files from data sources into module input directories. `run_pipeline_batch.py` runs each module in dependency order and writes results to output directories.

**Tech Stack:** Python 3.11+, numpy, scipy, faster-whisper, Pydantic, kaggle CLI, huggingface `datasets`

**Spec:** `SAATHI_AI_IMPLEMENTATION_SPEC.md` — Modules M04, M05, M06, M07

## Global Constraints

- Pipeline expects **16kHz, mono, float32** WAV for M05 and M07
- M06 is the canonical resampler — all external audio (8kHz, 44.1kHz) goes through M06 first
- Quality gate: `quality_score < 0.15` → skip M05/M07 for that file
- Do NOT modify any code in `services/audio_worker/` — these are existing Phase 1 modules
- All output JSON must match Pydantic schemas in `packages/schemas/audio.py`
- License compliance: only use CC0 / CC-BY / CC-BY-NC datasets

## Review Focus

1. **8kHz telephone audio through M06** → resampler must produce 16kHz output without alias artifacts
2. **Empty/silent files through M04** → must return `NEAR_SILENCE` flag and `quality_score ≤ 0.10`
3. **M05 on 911 call audio** → panicked speech may have unusual energy; VAD must not miss short bursts
4. **M07 on Hindi 8kHz audio** → after resampling, Whisper must detect `language=hi` and produce non-empty transcript
5. **Missing input folders** → `run_pipeline_batch.py` must print actionable message and continue, not crash

---

## Folder Structure (After Plan)

```
test_audio/
├── curated/              ← Existing 53 WAVs
├── augmented/            ← Existing 36 augmented WAVs
├── incoming/
│   └── external/
│       ├── 911_calls/    ← DS06 (CC0, kaggle) — DOWNLOAD NOW
│       ├── axondata/     ← DS04 (CC BY-NC, HuggingFace) — DOWNLOAD NOW
│       ├── shemo/        ← DS11 (academic, GitHub) — DOWNLOAD NOW
│       ├── hindi_calls/  ← DS05 (CC BY-NC-ND, kaggle) — DOWNLOAD NOW
│       ├── callhome/     ← DS02 (TalkBank free account) — REGISTER
│       ├── daic_woz/     ← DS08 (USC ICT gated) — APPLY
│       └── vaani/        ← DS09 (IISc HuggingFace gated) — REGISTER
└── pipeline_io/
    ├── PIPELINE_IO_MAP.yaml       ← Authoritative I/O definition ✅
    ├── m04_quality_check/
    │   ├── input/                 ← Raw WAVs fed to M04
    │   └── output/                ← *_quality.json
    ├── m06_preprocessor/
    │   ├── input/                 ← Raw WAVs (any SR) fed to M06
    │   └── output/                ← *_16k_mono.wav
    ├── m05_vad/
    │   ├── input/                 ← 16kHz WAVs fed to M05
    │   └── output/                ← *_vad.json
    └── m07_asr/
        ├── input/                 ← 16kHz WAVs fed to M07
        └── output/                ← *_transcript.json
```

---

## Task 1: Foundation Layer (ALREADY DONE ✅)

**Files already created:**

| File | Purpose |
|---|---|
| [`tools/pipeline_config.py`](file:///c:/Projects/SaathiAI/tools/pipeline_config.py) | Central I/O registry — single source of truth for all paths |
| [`test_audio/pipeline_io/PIPELINE_IO_MAP.yaml`](file:///c:/Projects/SaathiAI/test_audio/pipeline_io/PIPELINE_IO_MAP.yaml) | Human-readable I/O map with all data sources |
| [`tools/populate_inputs.py`](file:///c:/Projects/SaathiAI/tools/populate_inputs.py) | Copies audio files into module input folders |
| [`tools/run_pipeline_batch.py`](file:///c:/Projects/SaathiAI/tools/run_pipeline_batch.py) | Runs M04→M06→M05→M07 batch with quality gating |

- [ ] **Step 1.1: Verify pipeline_config imports cleanly**

```bash
cd c:\Projects\SaathiAI
python -c "from tools.pipeline_config import get_config; cfg = get_config(); print([m.module_id for m in cfg.all_modules()])"
```
Expected: `['m04_quality_check', 'm06_preprocessor', 'm05_vad', 'm07_asr']`

- [ ] **Step 1.2: Verify all pipeline directories exist**

```bash
python -c "from tools.pipeline_config import get_config; get_config().ensure_all_dirs(); print('dirs OK')"
```
Expected: `dirs OK`

- [ ] **Step 1.3: Verify available sources are found**

```bash
python -c "from tools.pipeline_config import get_config; [print(s.source_id, s.location.exists()) for s in get_config().available_sources()]"
```
Expected: All lines show `True`

---

## Task 2: Download Immediately Available Datasets

### 2A — DS06: 911 Recordings (CC0, WAV, no account)

- [ ] **Step 2.1: Install kaggle CLI**

```bash
pip install kaggle --quiet
```
Place `kaggle.json` (API key from kaggle.com → Account → API) at `C:\Users\itzme\.kaggle\kaggle.json`

- [ ] **Step 2.2: Download 911 recordings**

```bash
kaggle datasets download -d louisteitelbaum/911-recordings-first-6-seconds -p test_audio/incoming/external/911_calls --unzip
```
Expected: `~700 WAV files` in destination

- [ ] **Step 2.3: Verify count**

```powershell
(Get-ChildItem -Recurse -Filter "*.wav" "test_audio\incoming\external\911_calls").Count
```
Expected: `> 500`

### 2B — DS11: ShEMO Persian Emotional Speech (Academic free)

- [ ] **Step 2.4: Clone ShEMO**

```bash
git clone https://github.com/mansourehk/ShEMO test_audio/incoming/external/shemo
```
Expected: `~3,000 WAV files` cloned into destination

### 2C — DS05: Hindi Phone Calls Sample (CC BY-NC-ND, kaggle)

- [ ] **Step 2.5: Download Hindi call sample**

```bash
kaggle datasets download -d simaongraves/760h-hindi-phone-calls-dataset -p test_audio/incoming/external/hindi_calls --unzip
```

### 2D — DS04: AxonData Call Center (HuggingFace, CC BY-NC)

- [ ] **Step 2.6: Create and run AxonData fetch script**

Create `tools/fetch_axondata_sample.py`:

```python
"""Stream 50 files from AxonData HuggingFace dataset and save as WAV."""
import sys, wave
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DEST = Path("test_audio/incoming/external/axondata")
DEST.mkdir(parents=True, exist_ok=True)
N_SAMPLES = 50

from datasets import load_dataset
ds = load_dataset(
    "AxonData/english-contact-center-audio-dataset",
    streaming=True, split="train"
)
for i, row in enumerate(ds):
    if i >= N_SAMPLES:
        break
    audio_arr = np.array(row["audio"]["array"], dtype=np.float32)
    sr = row["audio"]["sampling_rate"]
    out = DEST / f"axon_{i:04d}.wav"
    int16 = (np.clip(audio_arr, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(int16.tobytes())
    print(f"  Saved {out.name}  sr={sr}")
print(f"\n✓ Saved {N_SAMPLES} samples to {DEST}")
```

```bash
pip install datasets soundfile --quiet
python tools/fetch_axondata_sample.py
```
Expected: `✓ Saved 50 samples to test_audio/incoming/external/axondata`

---

## Task 3: Populate Module Input Folders

- [ ] **Step 3.1: Dry-run verify**

```bash
python tools/populate_inputs.py --dry-run
```
Expected: Prints list of files that would be copied per module

- [ ] **Step 3.2: Populate all module inputs**

```bash
python tools/populate_inputs.py
```

- [ ] **Step 3.3: Verify M04 input count**

```powershell
(Get-ChildItem -Recurse -Filter "*.wav" "test_audio\pipeline_io\m04_quality_check\input").Count
```
Expected: `≥ 89` (existing), more if external datasets downloaded

---

## Task 4: Run Full Pipeline Batch

- [ ] **Step 4.1: M04 sanity check (5 files)**

```bash
python tools/run_pipeline_batch.py --module m04_quality_check --limit 5
```
Expected: 5 `*_quality.json` in `pipeline_io/m04_quality_check/output/`

- [ ] **Step 4.2: Spot-check M04 output JSON**

```bash
python -c "import json,glob; f=sorted(glob.glob('test_audio/pipeline_io/m04_quality_check/output/*.json'))[0]; print(json.dumps(json.load(open(f)), indent=2))"
```
Expected: JSON with `quality_score`, `snr_estimate`, `clipping_ratio`, `distortion_flags`

- [ ] **Step 4.3: Run M06 (preprocessor)**

```bash
python tools/run_pipeline_batch.py --module m06_preprocessor
```
Expected: `*_16k_mono.wav` files in `pipeline_io/m06_preprocessor/output/`

- [ ] **Step 4.4: Copy M06 output → M05 and M07 inputs**

```powershell
Copy-Item "test_audio\pipeline_io\m06_preprocessor\output\*.wav" "test_audio\pipeline_io\m05_vad\input\"
Copy-Item "test_audio\pipeline_io\m06_preprocessor\output\*.wav" "test_audio\pipeline_io\m07_asr\input\"
```

- [ ] **Step 4.5: Run M05 (VAD)**

```bash
python tools/run_pipeline_batch.py --module m05_vad
```
Expected: `*_vad.json` per file with speech segment timestamps

- [ ] **Step 4.6: Run M07 (ASR)**

```bash
python tools/run_pipeline_batch.py --module m07_asr
```
Expected: `*_transcript.json` per file with `full_text`, `segments`, `language`

- [ ] **Step 4.7: Full pipeline end-to-end**

```bash
python tools/run_pipeline_batch.py
```
Expected: All 4 modules run, all outputs written without errors

---

## Task 5: Register for Gated Datasets (Human Action Required)

Do while Task 4 runs:

| Dataset | Action | Time |
|---|---|---|
| **CALLHOME (DS02)** | Register at https://talkbank.org → CABank → CALLHOME English → download audio | ~5 min |
| **DAIC-WOZ (DS08)** | Submit form at https://dcapswoz.ict.usc.edu/ with institutional email | ~3–5 days |
| **Project Vaani (DS09)** | Accept terms at https://huggingface.co/ARTPARK-IISc (HF account required) | ~5 min |

Place downloaded files in the `test_audio/incoming/external/<dataset>/` folder, then:
```bash
python tools/populate_inputs.py
python tools/run_pipeline_batch.py
```

---

## Task 6: Pipeline Report & Commit

- [ ] **Step 6.1: Create `tools/pipeline_report.py`**

Script reads all output JSONs and prints:
- Files processed per module
- Quality score distribution (min/mean/max)
- Flag frequency breakdown
- Languages detected by M07
- Files that hit quality gate

- [ ] **Step 6.2: Run report**

```bash
python tools/pipeline_report.py
```

- [ ] **Step 6.3: Commit**

```bash
git add tools/pipeline_config.py tools/populate_inputs.py tools/run_pipeline_batch.py
git add tools/fetch_axondata_sample.py tools/pipeline_report.py
git add test_audio/pipeline_io/PIPELINE_IO_MAP.yaml
git commit -m "feat(test): add pipeline I/O foundation layer and audio data aggregation tools"
```
