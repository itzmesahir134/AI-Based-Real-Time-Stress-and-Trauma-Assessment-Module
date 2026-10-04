"""
populate_inputs.py — Populate module input folders from data sources
====================================================================

This script copies/symlinks audio files from each data source into
the correct pipeline_io/mXX/input/ folder for each module.

Run this ONCE after downloading new datasets, or when adding new
audio files to the test set.

Usage:
    python tools/populate_inputs.py
    python tools/populate_inputs.py --module m04_quality_check
    python tools/populate_inputs.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Allow running from project root
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from tools.pipeline_config import get_config, PIPELINE_EXECUTION_ORDER

# ── Source → Module input mapping ─────────────────────────────────
# Defines which source folders populate which module input folders.
# A source folder may feed multiple modules.

SOURCE_TO_MODULE_INPUTS: dict[str, list[str]] = {
    # ---- Existing curated data (already 16kHz) ----
    # Goes directly into M04 and M07 (no resampling needed)
    "curated_clean":           ["m04_quality_check", "m05_vad", "m07_asr"],
    "curated_emotional":       ["m04_quality_check", "m05_vad", "m07_asr"],
    "curated_conversational":  ["m04_quality_check", "m05_vad", "m07_asr"],
    "curated_edge_cases":      ["m04_quality_check", "m05_vad"],
    "curated_indian_languages":["m04_quality_check", "m07_asr"],
    # Augmented variants test M04 (quality under degradation) and M06 (resampler robustness)
    "augmented_variants":      ["m04_quality_check", "m06_preprocessor"],

    # ---- External datasets (8kHz or 44.1kHz → need M06 resampling) ----
    # These go into M04 (raw quality assessment) and M06 (for resampling)
    # M05/M07 gets their output via M06 → output is then copied to m05/m07 input
    "ds06_911_recordings":     ["m04_quality_check", "m06_preprocessor"],
    "ds04_axondata":           ["m04_quality_check", "m06_preprocessor"],
    "ds11_shemo":              ["m04_quality_check", "m06_preprocessor"],
    "ds05_hindi_calls":        ["m04_quality_check", "m06_preprocessor"],
    "ds02_callhome":           ["m04_quality_check", "m06_preprocessor"],
    "ds08_daic_woz":           ["m04_quality_check", "m05_vad", "m07_asr"],
    "ds09_vaani":              ["m04_quality_check", "m06_preprocessor"],
}


def populate(module_filter: str | None, dry_run: bool) -> None:
    cfg = get_config()
    cfg.ensure_all_dirs()

    total_copied = 0

    for source_id, target_modules in SOURCE_TO_MODULE_INPUTS.items():
        try:
            src = cfg.source(source_id)
        except KeyError:
            print(f"  [WARN] Unknown source '{source_id}' — skipping")
            continue

        if not src.is_available:
            status_detail = (
                f"download: {src.download_cmd[:60]}..."
                if src.needs_download
                else f"register at: {src.registration_url}"
            )
            print(f"  [SKIP] {source_id} - {src.status} - {status_detail}")
            continue

        wav_files = sorted(src.location.glob("**/*.wav"))
        if not wav_files:
            print(f"  [WARN] {source_id} - 0 WAV files found in {src.location}")
            continue

        for module_id in target_modules:
            if module_filter and module_id != module_filter:
                continue
            try:
                mod = cfg.module(module_id)
            except KeyError:
                continue

            print(f"  [{source_id}] -> [{module_id}] ({len(wav_files)} files)")

            for wav in wav_files:
                dest = mod.input_dir / wav.name
                if dest.exists():
                    continue  # already present, skip
                if not dry_run:
                    shutil.copy2(wav, dest)
                    total_copied += 1
                else:
                    print(f"    DRY: {wav.name} -> {dest}")
                    total_copied += 1

    print(f"\n[OK] {'Would copy' if dry_run else 'Copied'} {total_copied} files total.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate module input folders from data sources")
    parser.add_argument("--module", help="Only populate a specific module (e.g. m04_quality_check)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without doing it")
    args = parser.parse_args()

    print("\n=== SAATHI-AI Pipeline Input Populator ===\n")
    populate(args.module, args.dry_run)


if __name__ == "__main__":
    main()
