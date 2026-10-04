"""
fetch_vaani_sample.py — Extract diverse regional Indian speech samples from Project Vaani
========================================================================================

Extracts a curated subset of 50 samples from the cached Project Vaani dataset (IISc / ARTPARK)
into `test_audio/incoming/external/vaani` covering diverse Indian regional dialects and accents.
"""

from __future__ import annotations

import io
import sys
import wave
from pathlib import Path
import numpy as np

# Ensure project root in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

DEST = _PROJECT_ROOT / "test_audio" / "incoming" / "external" / "vaani"
DEST.mkdir(parents=True, exist_ok=True)
N_SAMPLES = 50


def main() -> None:
    try:
        import pandas as pd
        import soundfile as sf
    except ImportError as e:
        print(f"Error: Missing dependency ({e}). Run: pip install soundfile pandas")
        sys.exit(1)

    print("Loading Project Vaani sample dataset (IISc / ARTPARK)...")
    dataset_url = "hf://datasets/SujithPulikodan/Vaani-sample-data/audio/train-00000-of-00001.parquet"
    try:
        df = pd.read_parquet(dataset_url)
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        sys.exit(1)

    print(f"Found {len(df)} total recordings in Vaani dataset.")
    saved_count = 0

    # Step through rows to get a representative distribution
    stride = max(1, len(df) // N_SAMPLES)
    indices = [i * stride for i in range(N_SAMPLES)]

    for idx in indices:
        if idx >= len(df) or saved_count >= N_SAMPLES:
            break
        row = df.iloc[idx]
        audio_info = row.get("audio")
        if not audio_info or not audio_info.get("bytes"):
            continue

        raw_bytes = audio_info["bytes"]
        try:
            data, sr = sf.read(io.BytesIO(raw_bytes))
            if data.ndim > 1:
                data = data.mean(axis=1)

            # Skip ultra-short clips (< 1s)
            if len(data) < int(1.0 * sr):
                continue

            # Normalize amplitude
            chunk = data.astype(np.float32)
            peak = np.max(np.abs(chunk))
            if peak > 0:
                chunk = chunk / peak * 0.85

            int16 = (np.clip(chunk, -1.0, 1.0) * 32767).astype(np.int16)

            lang = str(row.get("language", "ind")).lower()[:3]
            district = str(row.get("district", "reg")).lower()[:6].replace(" ", "_")
            out_file = DEST / f"vaani_{saved_count:03d}_{lang}_{district}.wav"

            with wave.open(str(out_file), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(int16.tobytes())

            dur = len(int16) / sr
            print(f"  [{saved_count + 1}/{N_SAMPLES}] Saved {out_file.name} (sr={sr}Hz, dur={dur:.2f}s, lang={row.get('language')})")
            saved_count += 1
        except Exception as err:
            print(f"  [WARN] Skipping record {idx}: {err}")

    print(f"\n[OK] Saved {saved_count} Project Vaani samples to {DEST}")


if __name__ == "__main__":
    main()
