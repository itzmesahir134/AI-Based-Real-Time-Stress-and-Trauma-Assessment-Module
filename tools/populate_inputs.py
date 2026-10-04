"""
populate_inputs.py — Populate grouped pipeline input folders with zero duplication
===================================================================================

This script links audio files from each data source into the shared pipeline folders:
- `test_audio/pipeline_io/shared_raw/`: Grouped input for M04 (Quality) and M06 (Preprocessor)
- `test_audio/pipeline_io/shared_16k/`: Grouped input for M05 (VAD) and M07 (ASR)

Uses NTFS hardlinks by default (os.link) so audio files take 0 MB of extra disk space.
Falls back to copy only if cross-device linking is not supported.

Usage:
    python tools/populate_inputs.py
    python tools/populate_inputs.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Allow running from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from tools.pipeline_config import (
    SHARED_RAW_DIR,
    SHARED_16K_DIR,
    get_config,
)

# ── Source → Grouped Target Mapping ──────────────────────────────
# raw: files needing raw quality check / resampling (feeds shared_raw)
# 16k: files that are already 16kHz and directly usable by VAD/ASR (feeds shared_16k)
SOURCE_TARGET_MAP: dict[str, list[str]] = {
    # Curated (16kHz mono) -> both raw (for quality testing) and 16k (direct VAD/ASR)
    "curated_clean":            ["raw", "16k"],
    "curated_emotional":        ["raw", "16k"],
    "curated_conversational":   ["raw", "16k"],
    "curated_edge_cases":       ["raw", "16k"],
    "curated_indian_languages": ["raw", "16k"],
    "augmented_variants":       ["raw"],

    # External datasets
    "ds06_911_recordings":      ["raw"],
    "ds04_axondata":            ["raw"],
    "ds11_shemo":               ["raw"],
    "ds05_hindi_calls":         ["raw"],
    "ds02_callhome":            ["raw"],
    "ds08_daic_woz":            ["raw", "16k"],
    "ds09_vaani":               ["raw", "16k"],  # Vaani is already 16kHz mono
}


def link_or_copy(src: Path, dest: Path) -> str:
    """Link file using NTFS hardlink (0 extra bytes) or copy if hardlink unsupported."""
    if dest.exists():
        return "EXISTS"
    try:
        os.link(src, dest)
        return "LINKED"
    except (OSError, NotImplementedError):
        shutil.copy2(src, dest)
        return "COPIED"


def populate(dry_run: bool) -> None:
    cfg = get_config()
    cfg.ensure_all_dirs()

    print("\n=== SAATHI-AI Minimal-Storage Input Populator ===\n")
    print(f"  Target Shared Raw : {SHARED_RAW_DIR}")
    print(f"  Target Shared 16k : {SHARED_16K_DIR}\n")

    total_added = 0
    total_skipped = 0

    for source_id, targets in SOURCE_TARGET_MAP.items():
        try:
            src = cfg.source(source_id)
        except KeyError:
            print(f"  [WARN] Unknown source '{source_id}' - skipping")
            continue

        if not src.is_available:
            status_detail = (
                f"download: {src.download_cmd[:50]}..."
                if src.needs_download
                else f"register at: {src.registration_url}"
            )
            print(f"  [SKIP] {source_id} - {src.status} - {status_detail}")
            continue

        wav_files = sorted(src.location.glob("**/*.wav"))
        if not wav_files:
            print(f"  [WARN] {source_id} - 0 WAV files found in {src.location}")
            continue

        dest_dirs = []
        if "raw" in targets:
            dest_dirs.append(SHARED_RAW_DIR)
        if "16k" in targets:
            dest_dirs.append(SHARED_16K_DIR)

        print(f"  [{source_id}] -> {', '.join(targets)} ({len(wav_files)} files)")

        for wav in wav_files:
            for dest_dir in dest_dirs:
                dest = dest_dir / wav.name
                if dest.exists():
                    total_skipped += 1
                    continue
                if not dry_run:
                    action = link_or_copy(wav, dest)
                    if action in ("LINKED", "COPIED"):
                        total_added += 1
                else:
                    total_added += 1

    action_label = "Would add" if dry_run else "Added"
    print(f"\n[OK] {action_label} {total_added} entries ({total_skipped} already present).")
    print(f"  Files in {SHARED_RAW_DIR.name}: {len(list(SHARED_RAW_DIR.glob('*.wav')))}")
    print(f"  Files in {SHARED_16K_DIR.name}: {len(list(SHARED_16K_DIR.glob('*.wav')))}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate shared grouped pipeline input folders")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added without making changes")
    args = parser.parse_args()

    populate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
