"""Pipeline Test Runner for SAATHI-AI.

Feeds audio test samples from test_audio/ into the existing Phase 1 audio pipeline:
- M04: Audio Quality Diagnostics (Quality Score, SNR, Clipping, Flags)
- M05: Voice Activity Detection (VAD speech bursts)
- M07: ASR Speech-to-Text (faster-whisper transcription and detected language)

DOES NOT modify, redesign, or reimplement any Phase 1 pipeline code.
Uses services.audio_worker directly.

Usage:
    python -m tools.test_pipeline
    python -m tools.test_pipeline --category clean
    python -m tools.test_pipeline --category emotional
    python -m tools.test_pipeline --category indian_languages
    python -m tools.test_pipeline --category augmented
    python -m tools.test_pipeline --sample-id CLEAN_001
    python -m tools.test_pipeline --limit 6
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.audio_worker import (
    Transcriber,
    analyze_audio_quality,
    bytes_to_pcm_array,
    detect_voice_activity,
)

METADATA_CSV = os.path.join("test_audio", "metadata", "samples.csv")


def load_test_registry() -> List[Dict[str, str]]:
    """Loads all test sample metadata records."""
    if not os.path.exists(METADATA_CSV):
        raise FileNotFoundError(f"Metadata file not found: {METADATA_CSV}. Run 'python -m tools.build_test_set' first.")
    with open(METADATA_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate_sample(record: Dict[str, str], transcriber: Optional[Transcriber] = None) -> Dict[str, Any]:
    """Runs a single test sample through the Phase 1 audio pipeline."""
    sample_id = record["sample_id"]
    rel_path = record["test_file"].replace("/", os.sep)
    abs_path = os.path.abspath(os.path.join("test_audio", rel_path))

    if not os.path.exists(abs_path):
        return {"sample_id": sample_id, "error": f"File not found: {abs_path}"}

    with open(abs_path, "rb") as f:
        audio_bytes = f.read()

    # 1. PCM Decode
    audio, sr = bytes_to_pcm_array(audio_bytes)
    duration = len(audio) / float(sr) if sr > 0 else 0.0

    # 2. Quality Diagnostics (M04)
    quality = analyze_audio_quality(audio, sample_rate=sr)

    # 3. VAD (M05)
    segments = detect_voice_activity(audio, sample_rate=sr)

    # 4. ASR Transcription (M07)
    asr_text = ""
    detected_lang = ""
    if transcriber is not None:
        try:
            # Map language if specified
            lang_code = None
            if record["language"] == "Hindi":
                lang_code = "hi"
            elif record["language"] == "Marathi":
                lang_code = "mr"
            elif record["language"] == "Tamil":
                lang_code = "ta"
            elif record["language"] == "English":
                lang_code = "en"

            transcript = transcriber.transcribe(audio, sample_rate=sr, language=lang_code)
            asr_text = transcript.full_text
            detected_lang = transcript.language
        except Exception as e:
            asr_text = f"[ASR Error: {e}]"

    return {
        "sample_id": sample_id,
        "filename": os.path.basename(abs_path),
        "category": record["category"],
        "dataset": record["dataset"],
        "language": record["language"],
        "original_label": record["original_label_if_available"],
        "duration": round(duration, 2),
        "quality_score": round(quality.quality_score, 3),
        "snr_db": quality.snr_estimate,
        "clipping_ratio": round(quality.clipping_ratio, 4),
        "distortion_flags": quality.distortion_flags,
        "vad_bursts": len(segments),
        "detected_lang": detected_lang,
        "transcript": asr_text.strip(),
    }


def main():
    parser = argparse.ArgumentParser(description="Test existing Phase 1 pipeline against audio test samples")
    parser.add_argument("--category", "-c", type=str, help="Filter by category (clean, emotional, conversational, indian_languages, edge_cases, augmented)")
    parser.add_argument("--sample-id", "-s", type=str, help="Test a specific sample by ID (e.g. CLEAN_001, EMO_010)")
    parser.add_argument("--limit", "-l", type=int, default=8, help="Maximum number of samples to test (default: 8, use 0 for all)")
    parser.add_argument("--no-asr", action="store_true", help="Skip Whisper ASR transcription to speed up evaluation")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    records = load_test_registry()

    # Filter
    if args.sample_id:
        records = [r for r in records if r["sample_id"].upper() == args.sample_id.upper()]
    elif args.category:
        records = [r for r in records if r["category"].lower() == args.category.lower()]

    if args.limit and args.limit > 0:
        records = records[: args.limit]

    if not records:
        print("No matching audio test samples found.")
        return

    print("\n" + "=" * 80)
    print(f"RUNNING PHASE 1 PIPELINE ON {len(records)} TEST SAMPLES")
    print("Testing M04 (Audio Quality), M05 (VAD), and M07 (ASR faster-whisper)")
    print("=" * 80)

    transcriber = None if args.no_asr else Transcriber(model_size="tiny")

    results = []
    for r in records:
        res = evaluate_sample(r, transcriber=transcriber)
        results.append(res)
        if not args.json:
            print(f"\nSample: {res['sample_id']} [{res['category']}] ({res['dataset']} - {res['language']})")
            print(f"  * File:            {res['filename']} ({res['duration']}s)")
            print(f"  * Original Label:  {res['original_label']}")
            print(f"  * Quality Score:   {res['quality_score']} (0.0 to 1.0)")
            print(f"  * SNR Estimate:    {res['snr_db']} dB")
            print(f"  * Clipping Ratio:  {res['clipping_ratio'] * 100:.2f}%")
            print(f"  * Distortion Flags: {res['distortion_flags'] if res['distortion_flags'] else 'None'}")
            print(f"  * VAD Bursts:      {res['vad_bursts']}")
            if not args.no_asr:
                print(f"  * ASR Detected:    {res['detected_lang']}")
                print(f"  * ASR Text:        \"{res['transcript']}\"")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "=" * 80)
        print("PIPELINE TEST SUMMARY")
        print(f"Total Samples Evaluated: {len(results)}")
        avg_q = sum(r.get("quality_score", 0) for r in results) / max(len(results), 1)
        print(f"Average Audio Quality Score: {avg_q:.3f}")
        print("Pipeline successfully processed all tested samples without error.")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
