"""
run_pipeline_batch.py — Run all Phase 1 modules over the test audio set
=======================================================================

Runs each module in dependency order over all files in its input folder
and writes structured JSON output (or WAV for M06) to the output folder.

Module execution order:
    M04 → quality check (gates downstream processing)
    M06 → preprocessor (resamples/normalizes for M05 and M07)
    M05 → VAD (on M06 output)
    M07 → ASR (on M06 output)

Usage:
    python tools/run_pipeline_batch.py
    python tools/run_pipeline_batch.py --module m04_quality_check
    python tools/run_pipeline_batch.py --module m07_asr --limit 10
    python tools/run_pipeline_batch.py --skip-quality-gate
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any

import numpy as np

# Reconfigure stdout/stderr to avoid Windows cp1252 encoding issues
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from tools.pipeline_config import (
    PIPELINE_EXECUTION_ORDER,
    QUALITY_GATE_THRESHOLD,
    get_config,
)

# Import module functions
from services.audio_worker.preprocessor import bytes_to_pcm_array, preprocess_audio
from services.audio_worker.quality import analyze_audio_quality
from services.audio_worker.vad import detect_voice_activity
from services.audio_worker.asr import Transcriber

_transcriber = None


def get_transcriber() -> Transcriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber(model_size="base")
    return _transcriber


# ── Helpers ───────────────────────────────────────────────────────

def load_wav(path: Path) -> tuple[np.ndarray, int]:
    """Load a WAV file into a float32 numpy array and its sample rate."""
    audio_bytes = path.read_bytes()
    return bytes_to_pcm_array(audio_bytes)


def save_json(data: Any, path: Path) -> None:
    """Serialize a Pydantic model or dict to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "model_dump"):
        out = data.model_dump()
    elif hasattr(data, "dict"):
        out = data.dict()
    elif isinstance(data, list):
        out = [
            (item.model_dump() if hasattr(item, "model_dump") else
             item.dict() if hasattr(item, "dict") else item)
            for item in data
        ]
    else:
        out = data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def save_wav_16k(audio: np.ndarray, path: Path) -> None:
    """Write a 16kHz mono float32 array as a 16-bit PCM WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(int16.tobytes())


# ── Module runners ────────────────────────────────────────────────

def run_m04(wav_path: Path, out_dir: Path, stem: str) -> float:
    """Run M04 quality check. Returns quality_score."""
    audio, sr = load_wav(wav_path)
    result = analyze_audio_quality(audio, sample_rate=sr)
    save_json(result, out_dir / f"{stem}_quality.json")
    print(f"    M04 [OK]  quality={result.quality_score:.3f}  snr={result.snr_estimate:.1f}dB  flags={result.distortion_flags}")
    return result.quality_score


def run_m06(wav_path: Path, out_dir: Path, stem: str) -> tuple[np.ndarray, int] | None:
    """Run M06 preprocessor. Returns (audio_16k, 16000) or None on error."""
    audio, sr = load_wav(wav_path)
    if len(audio) == 0:
        print(f"    M06 [WARN]  empty audio - skipping")
        return None
    audio_16k, sr_out = preprocess_audio(audio, orig_sr=sr, target_sr=16000)
    out_path = out_dir / f"{stem}_16k_mono.wav"
    save_wav_16k(audio_16k, out_path)
    print(f"    M06 [OK]  {sr}Hz -> 16kHz  samples={len(audio_16k)}")
    return audio_16k, sr_out


def run_m05(audio: np.ndarray, sr: int, out_dir: Path, stem: str) -> None:
    """Run M05 VAD on preprocessed audio."""
    segments = detect_voice_activity(audio, sample_rate=sr)
    save_json(segments, out_dir / f"{stem}_vad.json")
    total_speech = sum(s.end_time - s.start_time for s in segments)
    print(f"    M05 [OK]  {len(segments)} segments  total_speech={total_speech:.2f}s")


def run_m07(audio: np.ndarray, sr: int, out_dir: Path, stem: str, language: str | None = None) -> None:
    """Run M07 ASR on preprocessed audio."""
    result = get_transcriber().transcribe(audio, sample_rate=sr, language=language)
    save_json(result, out_dir / f"{stem}_transcript.json")
    preview = result.full_text[:80].replace("\n", " ").encode("ascii", "replace").decode("ascii")
    print(f"    M07 [OK]  lang={result.language}  words={len(result.full_text.split())}  preview='{preview}'")


# ── Main batch runner ─────────────────────────────────────────────

def run_batch(
    module_filter: str | None,
    limit: int | None,
    skip_quality_gate: bool,
) -> None:
    cfg = get_config()
    cfg.ensure_all_dirs()

    order = (
        [module_filter] if module_filter
        else PIPELINE_EXECUTION_ORDER
    )

    for module_id in order:
        mod = cfg.module(module_id)
        wav_files = mod.input_files("*.wav")

        if not wav_files:
            print(f"\n[{module_id.upper()}] [WARN] No WAV files in {mod.input_dir}")
            print(f"  -> Run: python tools/populate_inputs.py --module {module_id}")
            continue

        if limit:
            wav_files = wav_files[:limit]

        print(f"\n{'='*60}")
        print(f"  MODULE: {module_id.upper()} - {len(wav_files)} files")
        print(f"  INPUT : {mod.input_dir}")
        print(f"  OUTPUT: {mod.output_dir}")
        print(f"{'='*60}")

        for wav_path in wav_files:
            stem = wav_path.stem
            print(f"\n  [{stem}]")

            if module_id == "m04_quality_check":
                run_m04(wav_path, mod.output_dir, stem)

            elif module_id == "m06_preprocessor":
                run_m06(wav_path, mod.output_dir, stem)

            elif module_id == "m05_vad":
                # M05 input is already 16kHz (from M06 output or curated)
                audio, sr = load_wav(wav_path)
                if not skip_quality_gate:
                    q = analyze_audio_quality(audio, sample_rate=sr)
                    if q.quality_score < QUALITY_GATE_THRESHOLD:
                        print(f"    M05 [GATE] quality_gate failed (score={q.quality_score:.3f} < {QUALITY_GATE_THRESHOLD})")
                        continue
                run_m05(audio, sr, mod.output_dir, stem)

            elif module_id == "m07_asr":
                audio, sr = load_wav(wav_path)
                if not skip_quality_gate:
                    q = analyze_audio_quality(audio, sample_rate=sr)
                    if q.quality_score < QUALITY_GATE_THRESHOLD:
                        print(f"    M07 [GATE] quality_gate failed (score={q.quality_score:.3f} < {QUALITY_GATE_THRESHOLD})")
                        continue
                # Infer language hint from filename (IND_* → hi, CONV_*_mr → mr, etc.)
                lang = _infer_language(stem)
                run_m07(audio, sr, mod.output_dir, stem, language=lang)

    print(f"\n{'='*60}")
    print(f"  [OK] Batch complete. Outputs in: {_PROJECT_ROOT / 'test_audio' / 'pipeline_io'}")
    print(f"{'='*60}\n")


def _infer_language(stem: str) -> str | None:
    """Heuristic language hint from file stem."""
    stem_lower = stem.lower()
    if "_hi_" in stem_lower or stem_lower.startswith("ind_016"):
        return "hi"
    if "_mr_" in stem_lower or "mar" in stem_lower:
        return "mr"
    if "_ta_" in stem_lower or "tam" in stem_lower:
        return "ta"
    if "_te_" in stem_lower:
        return "te"
    if "_kn_" in stem_lower or "kan" in stem_lower:
        return "kn"
    if "_pa_" in stem_lower or "pan" in stem_lower:
        return "pa"
    if "_gu_" in stem_lower:
        return "gu"
    if "_bn_" in stem_lower:
        return "bn"
    return None  # Let Whisper auto-detect


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SAATHI-AI Phase 1 pipeline batch")
    parser.add_argument("--module", help="Run only one module (e.g. m04_quality_check)")
    parser.add_argument("--limit", type=int, help="Process at most N files per module")
    parser.add_argument("--skip-quality-gate", action="store_true",
                        help="Run M05/M07 even on low-quality audio")
    args = parser.parse_args()

    print("\n=== SAATHI-AI Phase 1 Pipeline Batch Runner ===\n")
    run_batch(
        module_filter=args.module,
        limit=args.limit,
        skip_quality_gate=args.skip_quality_gate,
    )


if __name__ == "__main__":
    main()
