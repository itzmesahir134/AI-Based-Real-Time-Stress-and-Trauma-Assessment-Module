"""Stream/download real call center audio from AxonData HuggingFace repository and save as WAV."""
import sys
import wave
from pathlib import Path
import numpy as np

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

DEST = _PROJECT_ROOT / "test_audio" / "incoming" / "external" / "axondata"
DEST.mkdir(parents=True, exist_ok=True)
N_SAMPLES = 50

def main():
    try:
        from huggingface_hub import HfApi, hf_hub_download
        import soundfile as sf
    except ImportError as e:
        print(f"Error: Required package missing ({e}). Run: pip install soundfile huggingface_hub")
        sys.exit(1)

    print("Querying AxonData/english-contact-center-audio-dataset on HuggingFace...")
    api = HfApi()
    repo_id = "AxonData/english-contact-center-audio-dataset"
    audio_files = [
        f for f in api.list_repo_files(repo_id, repo_type="dataset")
        if f.lower().endswith((".mp3", ".wav"))
    ]
    print(f"Found {len(audio_files)} call center recording(s) in dataset.")

    saved_count = 0
    clip_duration_s = 15.0  # 15-second realistic dialogue segments
    samples_per_file = int(np.ceil(N_SAMPLES / max(len(audio_files), 1)))

    for file_idx, rel_path in enumerate(audio_files):
        if saved_count >= N_SAMPLES:
            break
        print(f"Fetching {rel_path}...")
        local_path = hf_hub_download(repo_id=repo_id, filename=rel_path, repo_type="dataset")
        audio_data, sr = sf.read(local_path)
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        total_duration = len(audio_data) / sr
        print(f"  Loaded call: {total_duration:.1f}s at {sr}Hz")

        # Step through the recording with 20s stride to get diverse segments
        stride_s = (total_duration - clip_duration_s) / max(samples_per_file, 1)
        for seg_idx in range(samples_per_file):
            if saved_count >= N_SAMPLES:
                break
            start_s = max(5.0, seg_idx * stride_s)  # skip intro silence if any
            end_s = start_s + clip_duration_s
            start_sample = int(start_s * sr)
            end_sample = int(end_s * sr)

            if end_sample > len(audio_data):
                break

            segment = audio_data[start_sample:end_sample].astype(np.float32)
            # Normalize to avoid extreme loudness/clipping
            peak = np.max(np.abs(segment))
            if peak > 0:
                segment = segment / peak * 0.85

            int16 = (np.clip(segment, -1.0, 1.0) * 32767).astype(np.int16)
            out_file = DEST / f"axon_{saved_count:04d}.wav"
            with wave.open(str(out_file), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(int16.tobytes())

            print(f"  [{saved_count + 1}/{N_SAMPLES}] Saved {out_file.name} (sr={sr}, start={start_s:.1f}s, dur={clip_duration_s:.1f}s)")
            saved_count += 1

    print(f"\n[OK] Saved {saved_count} samples to {DEST}")

if __name__ == "__main__":
    main()
