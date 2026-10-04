"""Audio Test Variant Generator.

Takes a clean WAV sample and generates controlled test variants:
1. input_clean.wav        - Normalized baseline clean speech
2. input_noise.wav        - Additive Gaussian background noise (~12 dB SNR)
3. input_traffic.wav      - Low-frequency traffic / rumbling noise (~10 dB SNR)
4. input_low_volume.wav   - Low volume (-18 dB attenuation)
5. input_clipped.wav      - Digital hard clipping / distortion (+12 dB pre-gain, hard-clipped)
6. input_reverb.wav       - Room reverberation (exponential decay impulse response convolution)
7. input_compressed.wav   - Non-linear dynamic range compression + 8-bit quantization artifacts
8. input_bandlimited.wav  - Telephony bandpass filtering (300 Hz - 3400 Hz Butterworth)
9. input_silence.wav      - Silence insertion (leading 1.0s, middle pause 1.5s, trailing 1.0s)
10. input_truncated.wav   - Partial speech truncation (abrupt cutoff at 40% duration)

Usage:
    python -m tools.create_variants <input.wav> [--out-dir <output_directory>]
    python create_test_variants.py <input.wav>
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import signal

from tools.audio_utils import analyze_audio_properties, load_audio, resample_audio, save_wav

Tuple_Audio = Tuple[np.ndarray, str, Dict[str, Any]]


def augment_clean(audio: np.ndarray, target_peak: float = 0.92) -> Tuple_Audio:
    """Normalizes peak amplitude safely."""
    peak = float(np.max(np.abs(audio)))
    if peak > 1e-4:
        scaled = audio * (target_peak / peak)
    else:
        scaled = audio.copy()
    params = {"target_peak": target_peak}
    return scaled, "none", params


def augment_noise(audio: np.ndarray, snr_db: float = 12.0, seed: int = 42) -> Tuple_Audio:
    """Adds white Gaussian background noise at specified SNR."""
    np.random.seed(seed)
    speech_power = np.mean(audio**2)
    if speech_power < 1e-6:
        noise = np.random.randn(len(audio)).astype(np.float32) * 0.05
    else:
        noise_power = speech_power / (10.0 ** (snr_db / 10.0))
        noise = np.random.randn(len(audio)).astype(np.float32) * np.sqrt(noise_power)

    augmented = np.clip(audio + noise, -1.0, 1.0)
    params = {"noise_type": "gaussian_white", "target_snr_db": snr_db, "seed": seed}
    return augmented, "additive_noise", params


def augment_traffic(audio: np.ndarray, sr: int = 16000, snr_db: float = 10.0, seed: int = 101) -> Tuple_Audio:
    """Generates low-frequency ambient/traffic rumble filtered below 350 Hz."""
    np.random.seed(seed)
    raw_noise = np.random.randn(len(audio)).astype(np.float32)
    # Lowpass filter at 350 Hz to simulate distant traffic/engine rumble
    sos = signal.butter(4, 350, btype="low", fs=sr, output="sos")
    traffic_noise = signal.sosfilt(sos, raw_noise)

    speech_power = np.mean(audio**2)
    noise_power = np.mean(traffic_noise**2) + 1e-9
    target_noise_power = speech_power / (10.0 ** (snr_db / 10.0))
    scale = np.sqrt(target_noise_power / noise_power)
    augmented = np.clip(audio + traffic_noise * scale, -1.0, 1.0)

    params = {"noise_type": "traffic_rumble", "lowpass_cutoff_hz": 350, "target_snr_db": snr_db}
    return augmented, "traffic_noise", params


def augment_low_volume(audio: np.ndarray, attenuation_db: float = -18.0) -> Tuple_Audio:
    """Attenuates signal to test sensitivity on faint speech or low mic gain."""
    linear_factor = 10.0 ** (attenuation_db / 20.0)
    augmented = audio * linear_factor
    params = {"attenuation_db": attenuation_db, "linear_factor": round(linear_factor, 4)}
    return augmented, "low_volume", params


def augment_clipping(audio: np.ndarray, pre_gain: float = 3.8, clip_threshold: float = 0.95) -> Tuple_Audio:
    """Simulates harsh digital clipping from overloaded microphone gain."""
    boosted = audio * pre_gain
    augmented = np.clip(boosted, -clip_threshold, clip_threshold)
    params = {"pre_gain": pre_gain, "clip_threshold": clip_threshold}
    return augmented, "clipping", params


def augment_reverb(
    audio: np.ndarray,
    sr: int = 16000,
    rt60_sec: float = 0.45,
    decay_rate: float = 6.0,
    mix: float = 0.38,
    seed: int = 77,
) -> Tuple_Audio:
    """Simulates room acoustics / reverberation via synthetic room impulse response."""
    np.random.seed(seed)
    ir_len = int(sr * rt60_sec)
    t = np.linspace(0, rt60_sec, ir_len)
    # Exponentially decaying noise impulse response
    decay = np.exp(-decay_rate * t)
    ir = (np.random.randn(ir_len).astype(np.float32) * decay)
    # Early reflections
    for reflection_time, amp in [(0.015, 0.4), (0.035, 0.25), (0.065, 0.15)]:
        idx = int(reflection_time * sr)
        if idx < ir_len:
            ir[idx] += amp

    ir = ir / (np.max(np.abs(ir)) + 1e-6)
    reverb_tail = signal.fftconvolve(audio, ir, mode="full")[: len(audio)]
    # Wet/dry mix
    augmented = (1.0 - mix) * audio + mix * reverb_tail
    peak = np.max(np.abs(augmented))
    if peak > 0.95:
        augmented = augmented * (0.95 / peak)

    params = {"rt60_seconds": rt60_sec, "wet_dry_mix": mix, "reflections": 3}
    return augmented.astype(np.float32), "reverberation", params


def augment_compression(audio: np.ndarray, quant_bits: int = 8, comp_ratio: float = 3.5) -> Tuple_Audio:
    """Simulates VoIP / telephony dynamic range compression and low-bit quantization."""
    # Dynamic range compression (tanh curve)
    threshold = 0.25
    compressed = np.where(
        np.abs(audio) > threshold,
        np.sign(audio) * (threshold + (np.abs(audio) - threshold) / comp_ratio),
        audio,
    )
    # Bit-depth quantization (e.g. 8-bit PCM equivalent)
    steps = 2 ** quant_bits
    quantized = np.round((compressed + 1.0) * 0.5 * (steps - 1)) / (steps - 1) * 2.0 - 1.0
    params = {"quantization_bits": quant_bits, "compression_ratio": comp_ratio, "threshold": threshold}
    return quantized.astype(np.float32), "compression_artifacts", params


def augment_bandlimited(audio: np.ndarray, sr: int = 16000, low_hz: float = 300.0, high_hz: float = 3400.0) -> Tuple_Audio:
    """Applies G.711 / PSTN telephony bandpass filter (300 Hz - 3400 Hz)."""
    sos = signal.butter(4, [low_hz, high_hz], btype="band", fs=sr, output="sos")
    filtered = signal.sosfilt(sos, audio)
    peak = np.max(np.abs(filtered))
    if peak > 0.95:
        filtered = filtered * (0.95 / peak)
    params = {"filter_type": "butterworth_bandpass", "order": 4, "low_cutoff_hz": low_hz, "high_cutoff_hz": high_hz}
    return filtered.astype(np.float32), "reduced_bandwidth", params


def augment_silence(
    audio: np.ndarray,
    sr: int = 16000,
    lead_sec: float = 1.0,
    mid_sec: float = 1.5,
    trail_sec: float = 1.0,
) -> Tuple_Audio:
    """Inserts leading, middle, and trailing silence to test VAD and streaming boundary detection."""
    lead = np.zeros(int(sr * lead_sec), dtype=np.float32)
    mid = np.zeros(int(sr * mid_sec), dtype=np.float32)
    trail = np.zeros(int(sr * trail_sec), dtype=np.float32)

    half = len(audio) // 2
    part1 = audio[:half]
    part2 = audio[half:]

    combined = np.concatenate([lead, part1, mid, part2, trail])
    params = {"leading_silence_s": lead_sec, "middle_pause_s": mid_sec, "trailing_silence_s": trail_sec}
    return combined.astype(np.float32), "silence_insertion", params


def augment_truncated(audio: np.ndarray, keep_ratio: float = 0.40) -> Tuple_Audio:
    """Truncates the audio midway to test incomplete utterance handling."""
    cut_idx = max(int(len(audio) * keep_ratio), 1000)
    truncated = audio[:cut_idx].copy()
    params = {"keep_ratio": keep_ratio, "original_length": len(audio), "truncated_length": cut_idx}
    return truncated, "partial_truncation", params


# Type alias helper
Tuple_Audio = tuple[np.ndarray, str, Dict[str, Any]]

VARIANT_GENERATORS = [
    ("clean", augment_clean),
    ("noise", augment_noise),
    ("traffic", augment_traffic),
    ("low_volume", augment_low_volume),
    ("clipped", augment_clipping),
    ("reverb", augment_reverb),
    ("compressed", augment_compression),
    ("bandlimited", augment_bandlimited),
    ("silence_inserted", augment_silence),
    ("truncated", augment_truncated),
]


def generate_variants(
    input_path: str,
    output_dir: Optional[str] = None,
    prefix: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generates all 10 standard audio test variants from an input audio file.

    Returns a list of variant metadata records.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    audio, orig_sr = load_audio(input_path)
    if orig_sr != 16000:
        audio = resample_audio(audio, orig_sr, 16000)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_dir = output_dir or os.path.dirname(os.path.abspath(input_path))
    os.makedirs(out_dir, exist_ok=True)

    results = []
    file_prefix = prefix or base_name

    for suffix, func in VARIANT_GENERATORS:
        variant_audio, aug_name, aug_params = func(audio)
        out_filename = f"{file_prefix}_{suffix}.wav"
        out_filepath = os.path.join(out_dir, out_filename)

        save_wav(out_filepath, variant_audio, sample_rate=16000)
        props = analyze_audio_properties(variant_audio, sample_rate=16000)

        record = {
            "variant_suffix": suffix,
            "filename": out_filename,
            "filepath": out_filepath,
            "augmentation": aug_name,
            "augmentation_parameters": json.dumps(aug_params),
            "duration_seconds": props["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "clipping_ratio": props["clipping_ratio"],
            "estimated_snr": props["estimated_snr"],
            "silence_ratio": props["silence_ratio"],
        }
        results.append(record)

    return results


def main():
    parser = argparse.ArgumentParser(description="Create audio test variants from a clean WAV sample")
    parser.add_argument("input_wav", type=str, help="Path to clean WAV input file")
    parser.add_argument("--out-dir", "-o", type=str, default=None, help="Directory to save generated variants")
    parser.add_argument("--prefix", "-p", type=str, default=None, help="Filename prefix for variants")
    parser.add_argument("--json", action="store_true", help="Print output as JSON")
    args = parser.parse_args()

    try:
        variants = generate_variants(args.input_wav, output_dir=args.out_dir, prefix=args.prefix)
        if args.json:
            print(json.dumps(variants, indent=2))
        else:
            print("\n" + "=" * 70)
            print(f"Generated {len(variants)} Test Variants for: {os.path.basename(args.input_wav)}")
            print("=" * 70)
            for v in variants:
                print(f"  * {v['filename']:<30} | {v['augmentation']:<22} | Dur: {v['duration_seconds']:>5.2f}s | SNR: {v['estimated_snr']:>4.1f} dB")
            print("=" * 70 + "\n")
    except Exception as e:
        print(f"Error generating variants: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
