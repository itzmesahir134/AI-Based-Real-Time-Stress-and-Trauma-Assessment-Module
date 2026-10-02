import io
import os
import urllib.request
import wave
import numpy as np


def download_file(url: str, dest_path: str):
    """Downloads a public audio sample if not present."""
    if not os.path.exists(dest_path):
        print(f"Downloading {url} to {dest_path}...")
        urllib.request.urlretrieve(url, dest_path)
        print("Download complete.")


def create_noisy_variation(source_path: str, dest_path: str, noise_level: float = 0.15):
    """Mixes realistic background noise into clean audio."""
    with wave.open(source_path, "rb") as wf:
        params = wf.getparams()
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)
        audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

    # Generate shaped noise
    np.random.seed(42)
    noise = np.random.normal(0, noise_level, len(audio)).astype(np.float32)
    noisy_audio = np.clip(audio + noise, -1.0, 1.0)
    noisy_int16 = (noisy_audio * 32767.0).astype(np.int16)

    with wave.open(dest_path, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(noisy_int16.tobytes())
    print(f"Created noisy variation: {dest_path}")


def create_clipped_variation(source_path: str, dest_path: str, gain: float = 3.5):
    """Creates an over-amplified, clipped version of the audio."""
    with wave.open(source_path, "rb") as wf:
        params = wf.getparams()
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)
        audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

    # Heavy amplification causing hard digital clipping
    clipped_audio = np.clip(audio * gain, -0.999, 0.999)
    clipped_int16 = (clipped_audio * 32767.0).astype(np.int16)

    with wave.open(dest_path, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(clipped_int16.tobytes())
    print(f"Created clipped variation: {dest_path}")


def main():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)

    # 1. Download benchmark English speech recording (11s JFK quote: "Ask not what your country...")
    jfk_url = "https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav"
    clean_en_path = os.path.join(fixtures_dir, "sample_english_clean.wav")
    download_file(jfk_url, clean_en_path)

    # 2. Create noisy and clipped variations
    create_noisy_variation(
        clean_en_path,
        os.path.join(fixtures_dir, "sample_english_noisy.wav"),
        noise_level=0.18,
    )
    create_clipped_variation(
        clean_en_path,
        os.path.join(fixtures_dir, "sample_english_clipped.wav"),
        gain=4.0,
    )

    # 3. Create Hindi spoken distress audio using gTTS if installed
    try:
        from gtts import gTTS
        from pydub import AudioSegment

        hindi_text = "नमस्ते, मुझे तत्काल सहायता चाहिए, कृपया मेरी मदद करें।"
        mp3_path = os.path.join(fixtures_dir, "temp_hindi.mp3")
        wav_path = os.path.join(fixtures_dir, "sample_hindi_clean.wav")
        tts = gTTS(text=hindi_text, lang="hi")
        tts.save(mp3_path)
        print("Generated Hindi speech audio via gTTS.")
    except Exception as e:
        print(f"Note: gTTS/pydub generation note: {e}")

    print("Audio fixtures setup finished.")


if __name__ == "__main__":
    main()
