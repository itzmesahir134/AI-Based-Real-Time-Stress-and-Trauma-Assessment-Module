import json
import os
import sys
import wave
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.audio_worker import (
    Transcriber,
    analyze_audio_quality,
    bytes_to_pcm_array,
    detect_voice_activity,
)


def run_test_on_file(file_path: str, forced_language: str = None):
    print("\n" + "=" * 60)
    print(f"Testing real audio sample: {os.path.basename(file_path)}")
    print("=" * 60)

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    # 1. Decode to PCM
    audio, sr = bytes_to_pcm_array(audio_bytes)
    duration = len(audio) / float(sr)
    print(f"  • Sample Rate: {sr} Hz")
    print(f"  • Duration: {duration:.2f} seconds")
    print(f"  • Total Samples: {len(audio)}")

    # 2. Audio Quality Analysis (M04)
    quality = analyze_audio_quality(audio, sample_rate=sr)
    print("\n  [M04: Audio Quality Diagnostics]")
    print(f"  • Quality Score: {quality.quality_score:.3f} (0.0 to 1.0)")
    print(f"  • Estimated SNR: {quality.snr_estimate} dB")
    print(f"  • Clipping Ratio: {quality.clipping_ratio * 100:.2f}%")
    print(f"  • Speech Activity Ratio: {quality.speech_ratio * 100:.1f}%")
    print(f"  • Distortion Flags: {quality.distortion_flags}")

    # 3. Voice Activity Detection (M05)
    segments = detect_voice_activity(audio, sample_rate=sr)
    print(f"\n  [M05: Voice Activity Detection (VAD)]")
    print(f"  • Detected Speech Bursts: {len(segments)}")
    for i, seg in enumerate(segments[:3]):
        print(f"    - Segment {i+1}: {seg.start_time:.2f}s -> {seg.end_time:.2f}s (conf: {seg.confidence})")
    if len(segments) > 3:
        print(f"    - ... and {len(segments)-3} more speech segments")

    # 4. Neural Speech-to-Text (M07) via faster-whisper (tiny model for fast local verification)
    print(f"\n  [M07: Speech-to-Text ASR (faster-whisper)]")
    transcriber = Transcriber(model_size="tiny")
    transcript = transcriber.transcribe(audio, sample_rate=sr, language=forced_language)
    print(f"  • Detected Language: {transcript.language}")
    print(f"  • Recognized Full Text: \"{transcript.full_text}\"")
    print(f"  • Segments Generated: {len(transcript.segments)}")
    for i, seg in enumerate(transcript.segments[:3]):
        print(f"    - [{seg.start_time:.2f}s - {seg.end_time:.2f}s]: \"{seg.text}\" (confidence: {seg.confidence})")

    return {
        "file": os.path.basename(file_path),
        "quality_score": quality.quality_score,
        "snr": quality.snr_estimate,
        "clipping": quality.clipping_ratio,
        "flags": quality.distortion_flags,
        "text": transcript.full_text,
    }


def main():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")

    samples = [
        ("sample_english_clean.wav", "en"),
        ("sample_english_noisy.wav", "en"),
        ("sample_english_clipped.wav", "en"),
        ("sample_hindi_clean.wav", "hi"),
    ]

    results = []
    for filename, lang in samples:
        path = os.path.join(fixtures_dir, filename)
        if os.path.exists(path):
            res = run_test_on_file(path, forced_language=lang)
            results.append(res)
        else:
            print(f"File not found: {path}")

    print("\n" + "#" * 60)
    print("SUMMARY OF REAL AUDIO PIPELINE TESTS")
    print("#" * 60)
    for r in results:
        print(f"File: {r['file']}")
        print(f"  Quality: {r['quality_score']} | SNR: {r['snr']} dB | Flags: {r['flags']}")
        print(f"  Recognized Text: {r['text']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
