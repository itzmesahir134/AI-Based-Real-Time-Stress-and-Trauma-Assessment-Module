"""Test Collection Builder for SAATHI-AI.

Curates and standardizes a balanced test collection (50-150 audio files)
to evaluate the Phase 1 audio pipeline under diverse conditions:
1. Clean speech (male, female, various speaking rates)
2. Emotional speech (neutral, calm, happiness, sadness, fear, anger, disgust)
3. Natural conversational audio (spontaneous turns, extempore speech)
4. Indian-language audio (Hindi, Marathi, Tamil, Telugu, Kannada, Punjabi, Gujarati)
5. Edge cases (very short bursts, extended speech, whisper, pure silence)
6. Derived audio quality variants (noise, low volume, clipping, reverb, compression, bandwidth, silence, truncation)

CRITICAL RULE:
  Original emotion labels (fear, anger, sadness, etc.) are strictly affective/acoustic signals.
  DO NOT map or convert them into 'trauma'.

Usage:
    python -m tools.build_test_set
"""

import csv
import json
import os
import shutil
import sys
from typing import Any, Dict, List, Optional
import numpy as np

from tools.audio_utils import analyze_audio_properties, load_audio, resample_audio, save_wav, standardize_audio
from tools.create_variants import VARIANT_GENERATORS
from tools.list_datasets import DATASET_CATALOG, export_sources_csv

TEST_AUDIO_ROOT = "test_audio"
ORIGINAL_DIR = os.path.join(TEST_AUDIO_ROOT, "original")
CURATED_DIR = os.path.join(TEST_AUDIO_ROOT, "curated")
AUGMENTED_DIR = os.path.join(TEST_AUDIO_ROOT, "augmented")
METADATA_DIR = os.path.join(TEST_AUDIO_ROOT, "metadata")


def ensure_directories():
    """Creates the full directory hierarchy."""
    for sub in [
        os.path.join(ORIGINAL_DIR, "crema_d"),
        os.path.join(ORIGINAL_DIR, "ravdess"),
        os.path.join(ORIGINAL_DIR, "iemocap"),
        os.path.join(ORIGINAL_DIR, "msp_podcast"),
        os.path.join(ORIGINAL_DIR, "indicvoices"),
        os.path.join(CURATED_DIR, "clean"),
        os.path.join(CURATED_DIR, "emotional"),
        os.path.join(CURATED_DIR, "conversational"),
        os.path.join(CURATED_DIR, "indian_languages"),
        os.path.join(CURATED_DIR, "edge_cases"),
        os.path.join(AUGMENTED_DIR, "noise"),
        os.path.join(AUGMENTED_DIR, "low_volume"),
        os.path.join(AUGMENTED_DIR, "clipping"),
        os.path.join(AUGMENTED_DIR, "reverb"),
        os.path.join(AUGMENTED_DIR, "compression"),
        os.path.join(AUGMENTED_DIR, "bandwidth"),
        os.path.join(AUGMENTED_DIR, "silence"),
        os.path.join(AUGMENTED_DIR, "truncated"),
        METADATA_DIR,
    ]:
        os.makedirs(sub, exist_ok=True)


# Mapping of CREMA-D sentences
CREMA_SENTENCES = {
    "DFA": "Don't forget a jacket",
    "IEO": "It's eleven o'clock",
    "IWW": "I wonder what this is about",
    "MTI": "More to it than meets the eye",
    "TSI": "The surface is slick",
    "WVO": "We've got to find the way out",
}

CREMA_EMOTIONS = {
    "NEU": "neutral",
    "ANG": "anger",
    "DIS": "disgust",
    "FEA": "fear",
    "HAP": "happiness",
    "SAD": "sadness",
}

CREMA_ACTOR_INFO = {
    "1001": {"gender": "Male", "age": 51, "ethnicity": "Caucasian"},
    "1002": {"gender": "Female", "age": 26, "ethnicity": "Caucasian"},
    "1003": {"gender": "Female", "age": 22, "ethnicity": "African American"},
    "1004": {"gender": "Female", "age": 48, "ethnicity": "Hispanic"},
    "1005": {"gender": "Male", "age": 31, "ethnicity": "Caucasian"},
    "1010": {"gender": "Female", "age": 40, "ethnicity": "Asian"},
}

RAVDESS_EMOTIONS = {
    "01": "neutral",
    "02": "calm",
    "03": "happiness",
    "04": "sadness",
    "05": "anger",
    "06": "fear",
    "07": "disgust",
    "08": "surprise",
}


def build_curated_clean(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Curates clean speech samples across genders, accents, and speaking speeds."""
    print("Building curated clean speech set...")
    out_dir = os.path.join(CURATED_DIR, "clean")

    clean_specs = [
        # (filename, sample_id, speaker_id, gender, speed_desc, notes)
        ("1001_DFA_NEU_XX.wav", "CLEAN_001", "CREMA_1001", "Male", "normal", "CREMA-D clean male Caucasian speech, neutral tone"),
        ("1002_IEO_NEU_XX.wav", "CLEAN_002", "CREMA_1002", "Female", "normal", "CREMA-D clean female Caucasian speech, neutral tone"),
        ("1003_TSI_NEU_XX.wav", "CLEAN_003", "CREMA_1003", "Female", "normal", "CREMA-D clean female African American speech, neutral tone"),
        ("1004_IWW_NEU_XX.wav", "CLEAN_004", "CREMA_1004", "Female", "deliberate", "CREMA-D clean female Hispanic speech, deliberate pace"),
        ("1005_MTI_NEU_XX.wav", "CLEAN_005", "CREMA_1005", "Male", "moderate", "CREMA-D clean male speech, moderate pace"),
        ("1010_IEO_NEU_XX.wav", "CLEAN_006", "CREMA_1010", "Female", "fast", "CREMA-D clean female Asian speech, brisk pace"),
        ("03-01-01-01-01-01-01.wav", "CLEAN_007", "RAVDESS_01", "Male", "normal", "RAVDESS clean North American male speech, neutral statement 1"),
        ("03-01-01-01-01-01-02.wav", "CLEAN_008", "RAVDESS_02", "Female", "normal", "RAVDESS clean North American female speech, neutral statement 1"),
    ]

    for orig_fn, sample_id, spk, gender, speed, notes in clean_specs:
        if orig_fn.startswith("03-"):
            orig_path = os.path.join(ORIGINAL_DIR, "ravdess", orig_fn)
            dataset = "RAVDESS"
            source_url = DATASET_CATALOG["ravdess"]["official_source"]
            license_str = DATASET_CATALOG["ravdess"]["license"]
        else:
            orig_path = os.path.join(ORIGINAL_DIR, "crema_d", orig_fn)
            dataset = "CREMA-D"
            source_url = DATASET_CATALOG["crema_d"]["official_source"]
            license_str = DATASET_CATALOG["crema_d"]["license"]

        if not os.path.exists(orig_path):
            print(f"  Warning: original clean file not found: {orig_path}")
            continue

        test_fn = f"{sample_id}_{gender.lower()}_{speed}.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        record = {
            "sample_id": sample_id,
            "dataset": dataset,
            "source_url": source_url,
            "license": license_str,
            "speaker_id_if_available": spk,
            "language": "English",
            "original_label_if_available": "neutral",
            "category": "clean",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": notes,
        }
        records.append(record)
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": dataset,
            "Language": "English",
            "Category": "clean",
            "Quality": "clean",
            "Purpose": f"Baseline pipeline testing ({gender}, {speed} speed)",
        })


def build_curated_emotional(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Curates emotional speech samples (neutral, calm, happiness, sadness, fear, anger, disgust)."""
    print("Building curated emotional speech set...")
    out_dir = os.path.join(CURATED_DIR, "emotional")

    emo_specs = [
        # (orig_fn, sample_id, ds, spk, emotion, intensity, notes)
        ("1001_DFA_NEU_XX.wav", "EMO_001", "crema_d", "CREMA_1001", "neutral", "normal", "Neutral emotional baseline"),
        ("03-01-02-01-01-01-01.wav", "EMO_002", "ravdess", "RAVDESS_01", "calm", "normal", "Calm vocalization male"),
        ("03-01-02-01-01-01-02.wav", "EMO_003", "ravdess", "RAVDESS_02", "calm", "normal", "Calm vocalization female"),
        ("1001_DFA_HAP_XX.wav", "EMO_004", "crema_d", "CREMA_1001", "happiness", "normal", "Happy expression male"),
        ("1002_IEO_HAP_LO.wav", "EMO_005", "crema_d", "CREMA_1002", "happiness", "low", "Happy expression female low intensity"),
        ("03-01-03-01-01-01-01.wav", "EMO_006", "ravdess", "RAVDESS_01", "happiness", "normal", "Happy vocalization male normal intensity"),
        ("1001_DFA_SAD_XX.wav", "EMO_007", "crema_d", "CREMA_1001", "sadness", "normal", "Sad expression male"),
        ("1002_IEO_SAD_HI.wav", "EMO_008", "crema_d", "CREMA_1002", "sadness", "high", "Sad expression female high intensity"),
        ("03-01-04-01-01-01-02.wav", "EMO_009", "ravdess", "RAVDESS_02", "sadness", "normal", "Sad vocalization female"),
        ("1001_DFA_FEA_XX.wav", "EMO_010", "crema_d", "CREMA_1001", "fear", "normal", "Fearful expression male. NOT trauma."),
        ("1002_IEO_FEA_MD.wav", "EMO_011", "crema_d", "CREMA_1002", "fear", "medium", "Fearful expression female. NOT trauma."),
        ("03-01-06-01-01-01-01.wav", "EMO_012", "ravdess", "RAVDESS_01", "fear", "normal", "Fear vocalization male. NOT trauma."),
        ("03-01-06-02-01-01-01.wav", "EMO_013", "ravdess", "RAVDESS_01", "fear", "strong", "Fear vocalization male high intensity. NOT trauma."),
        ("1001_DFA_ANG_XX.wav", "EMO_014", "crema_d", "CREMA_1001", "anger", "normal", "Anger expression male. NOT trauma."),
        ("1002_IEO_ANG_HI.wav", "EMO_015", "crema_d", "CREMA_1002", "anger", "high", "Anger expression female high intensity. NOT trauma."),
        ("03-01-05-01-01-01-02.wav", "EMO_016", "ravdess", "RAVDESS_02", "anger", "normal", "Anger vocalization female normal intensity."),
        ("03-01-05-02-01-01-02.wav", "EMO_017", "ravdess", "RAVDESS_02", "anger", "strong", "Anger vocalization female high intensity."),
        ("1001_DFA_DIS_XX.wav", "EMO_018", "crema_d", "CREMA_1001", "disgust", "normal", "Disgust expression male."),
        ("1002_IEO_DIS_MD.wav", "EMO_019", "crema_d", "CREMA_1002", "disgust", "medium", "Disgust expression female medium intensity."),
    ]

    for orig_fn, sample_id, ds_key, spk, emotion, intensity, notes in emo_specs:
        ds_info = DATASET_CATALOG[ds_key]
        orig_path = os.path.join(ORIGINAL_DIR, ds_key, orig_fn)

        if not os.path.exists(orig_path):
            print(f"  Warning: original emotional file not found: {orig_path}")
            continue

        test_fn = f"{sample_id}_{emotion}_{intensity}.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        record = {
            "sample_id": sample_id,
            "dataset": ds_info["name"],
            "source_url": ds_info["official_source"],
            "license": ds_info["license"],
            "speaker_id_if_available": spk,
            "language": "English",
            "original_label_if_available": f"{emotion} ({intensity})",
            "category": "emotional",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": f"{notes} (Acoustic emotion test; not trauma)",
        }
        records.append(record)
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": ds_info["name"],
            "Language": "English",
            "Category": "emotional",
            "Quality": "clean",
            "Purpose": f"Acoustic/emotion testing ({emotion}, {intensity})",
        })


def build_curated_conversational(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Curates natural conversational, spontaneous speech, and turn-taking audio."""
    print("Building curated conversational speech set...")
    out_dir = os.path.join(CURATED_DIR, "conversational")

    # First check if user placed files in iemocap or msp_podcast
    iemocap_files = [
        f for f in os.listdir(os.path.join(ORIGINAL_DIR, "iemocap"))
        if f.lower().endswith((".wav", ".flac"))
    ]
    msp_files = [
        f for f in os.listdir(os.path.join(ORIGINAL_DIR, "msp_podcast"))
        if f.lower().endswith((".wav", ".flac"))
    ]

    conv_count = 0

    # 1. Process IEMOCAP if available
    for i, fn in enumerate(iemocap_files[:4]):
        conv_count += 1
        sample_id = f"CONV_{conv_count:03d}"
        orig_path = os.path.join(ORIGINAL_DIR, "iemocap", fn)
        test_fn = f"{sample_id}_iemocap_turn_{i+1}.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        records.append({
            "sample_id": sample_id,
            "dataset": "IEMOCAP",
            "source_url": DATASET_CATALOG["iemocap"]["official_source"],
            "license": DATASET_CATALOG["iemocap"]["license"],
            "speaker_id_if_available": f"IEMOCAP_Turn_{i+1}",
            "language": "English",
            "original_label_if_available": "conversational_turn",
            "category": "conversational",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": "Natural dyadic dialogue from IEMOCAP",
        })
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": "IEMOCAP",
            "Language": "English",
            "Category": "conversational",
            "Quality": "clean",
            "Purpose": "Natural conversational dyadic dialogue & turn-taking",
        })

    # 2. Process MSP-Podcast if available
    for i, fn in enumerate(msp_files[:4]):
        conv_count += 1
        sample_id = f"CONV_{conv_count:03d}"
        orig_path = os.path.join(ORIGINAL_DIR, "msp_podcast", fn)
        test_fn = f"{sample_id}_msp_podcast_{i+1}.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        records.append({
            "sample_id": sample_id,
            "dataset": "MSP-Podcast",
            "source_url": DATASET_CATALOG["msp_podcast"]["official_source"],
            "license": DATASET_CATALOG["msp_podcast"]["license"],
            "speaker_id_if_available": f"MSP_Speaker_{i+1}",
            "language": "English",
            "original_label_if_available": "spontaneous_podcast",
            "category": "conversational",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": "In-the-wild spontaneous podcast recording",
        })
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": "MSP-Podcast",
            "Language": "English",
            "Category": "conversational",
            "Quality": "clean",
            "Purpose": "Real-world conversational flow from MSP-Podcast",
        })

    # 3. Add spontaneous / extempore speech from IndicVoices & conversational samples
    extempore_specs = [
        ("MAR_F_WIKI_00001.wav", "AI4Bharat", "mr", "Marathi", "Female", "Spontaneous extempore reading with natural pauses"),
        ("MAR_M_WIKI_00001.wav", "AI4Bharat", "mr", "Marathi", "Male", "Continuous conversational speech flow"),
        ("PAN_F_HAPPY_00002.wav", "AI4Bharat", "pa", "Punjabi", "Female", "Spontaneous expressive speech segment"),
        ("1004_IEO_FEA_LO.wav", "CREMA-D", "en", "English", "Female", "Spontaneous low-intensity sentence with breathing pause"),
        ("1005_IEO_ANG_LO.wav", "CREMA-D", "en", "English", "Male", "Conversational statement with emphatic stress"),
        ("1010_IEO_HAP_LO.wav", "CREMA-D", "en", "English", "Female", "Conversational upbeat cadence with natural inflection"),
    ]

    for orig_fn, ds_name, lang_code, lang_name, gender, notes in extempore_specs:
        conv_count += 1
        sample_id = f"CONV_{conv_count:03d}"
        if ds_name == "CREMA-D":
            orig_path = os.path.join(ORIGINAL_DIR, "crema_d", orig_fn)
            source_url = DATASET_CATALOG["crema_d"]["official_source"]
            license_str = DATASET_CATALOG["crema_d"]["license"]
        else:
            orig_path = os.path.join(ORIGINAL_DIR, "indicvoices", orig_fn)
            source_url = DATASET_CATALOG["indicvoices"]["official_source"]
            license_str = DATASET_CATALOG["indicvoices"]["license"]

        if not os.path.exists(orig_path):
            continue

        test_fn = f"{sample_id}_{lang_code}_{gender.lower()}_spontaneous.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        records.append({
            "sample_id": sample_id,
            "dataset": ds_name,
            "source_url": source_url,
            "license": license_str,
            "speaker_id_if_available": f"{ds_name}_{gender}",
            "language": lang_name,
            "original_label_if_available": "spontaneous_extempore",
            "category": "conversational",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": notes,
        })
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": ds_name,
            "Language": lang_name,
            "Category": "conversational",
            "Quality": "clean",
            "Purpose": f"Conversational/spontaneous condition ({lang_name}, {gender})",
        })


def build_curated_indian_languages(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Curates Indian language speech samples (Hindi, Marathi, Tamil, Telugu, Kannada, Punjabi, Gujarati)."""
    print("Building curated Indian-language speech set...")
    out_dir = os.path.join(CURATED_DIR, "indian_languages")

    indic_specs = [
        # (fn, sample_id, lang_code, lang_name, spk_id, notes)
        ("MAR_F_HAPPY_00001.wav", "IND_001", "mr", "Marathi", "AI4B_MAR_F", "Marathi female speech (AI4Bharat IndicVoices)"),
        ("MAR_F_WIKI_00001.wav", "IND_002", "mr", "Marathi", "AI4B_MAR_F2", "Marathi female reading (AI4Bharat)"),
        ("MAR_M_WIKI_00001.wav", "IND_003", "mr", "Marathi", "AI4B_MAR_M", "Marathi male continuous speech (AI4Bharat)"),
        ("slr64_mr_mrt_01523_00028548203.wav", "IND_004", "mr", "Marathi", "SLR64_1523", "Marathi crowdsourced native speaker 1 (OpenSLR 64)"),
        ("slr64_mr_mrt_01523_00029882518.wav", "IND_005", "mr", "Marathi", "SLR64_1523", "Marathi crowdsourced native speaker 2 (OpenSLR 64)"),
        ("TAM_F_HAPPY_00001.wav", "IND_006", "ta", "Tamil", "AI4B_TAM_F", "Tamil female speech (AI4Bharat IndicVoices)"),
        ("slr65_ta_taf_00008_00072928033.wav", "IND_007", "ta", "Tamil", "SLR65_0008", "Tamil crowdsourced native speaker 1 (OpenSLR 65)"),
        ("slr65_ta_taf_00008_00083252668.wav", "IND_008", "ta", "Tamil", "SLR65_0008", "Tamil crowdsourced native speaker 2 (OpenSLR 65)"),
        ("slr66_te_tef_01033_00007107192.wav", "IND_009", "te", "Telugu", "SLR66_1033", "Telugu crowdsourced native speaker 1 (OpenSLR 66)"),
        ("slr66_te_tef_01033_00010179612.wav", "IND_010", "te", "Telugu", "SLR66_1033", "Telugu crowdsourced native speaker 2 (OpenSLR 66)"),
        ("KAN_F_HAPPY_00001.wav", "IND_011", "kn", "Kannada", "AI4B_KAN_F", "Kannada female speech (AI4Bharat IndicVoices)"),
        ("PAN_F_HAPPY_00001.wav", "IND_012", "pa", "Punjabi", "AI4B_PAN_F", "Punjabi female speech (AI4Bharat IndicVoices)"),
        ("PAN_F_HAPPY_00002.wav", "IND_013", "pa", "Punjabi", "AI4B_PAN_F2", "Punjabi female speech statement 2 (AI4Bharat)"),
        ("slr78_gu_guf_01063_00076624578.wav", "IND_014", "gu", "Gujarati", "SLR78_1063", "Gujarati crowdsourced native speaker 1 (OpenSLR 78)"),
        ("slr78_gu_guf_01063_00102147911.wav", "IND_015", "gu", "Gujarati", "SLR78_1063", "Gujarati crowdsourced native speaker 2 (OpenSLR 78)"),
    ]

    for orig_fn, sample_id, lang_code, lang_name, spk_id, notes in indic_specs:
        orig_path = os.path.join(ORIGINAL_DIR, "indicvoices", orig_fn)
        if not os.path.exists(orig_path):
            print(f"  Warning: original Indic file not found: {orig_path}")
            continue

        test_fn = f"{sample_id}_{lang_code}_{os.path.basename(orig_fn)}"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(orig_path, test_path, target_sr=16000)

        record = {
            "sample_id": sample_id,
            "dataset": "IndicVoices / AI4Bharat",
            "source_url": DATASET_CATALOG["indicvoices"]["official_source"],
            "license": DATASET_CATALOG["indicvoices"]["license"],
            "speaker_id_if_available": spk_id,
            "language": lang_name,
            "original_label_if_available": "native_speech",
            "category": "indian_languages",
            "original_file": os.path.relpath(orig_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": notes,
        }
        records.append(record)
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": "IndicVoices / AI4Bharat",
            "Language": lang_name,
            "Category": "indian_languages",
            "Quality": "clean",
            "Purpose": f"Indian-language speech handling & ASR ({lang_name})",
        })

    # Also include existing fixture Hindi speech if present
    fixtures_hindi = os.path.join("tests", "fixtures", "sample_hindi_clean.wav")
    if os.path.exists(fixtures_hindi):
        sample_id = "IND_016"
        test_fn = f"{sample_id}_hi_clean.wav"
        test_path = os.path.join(out_dir, test_fn)
        stats = standardize_audio(fixtures_hindi, test_path, target_sr=16000)

        record = {
            "sample_id": sample_id,
            "dataset": "IndicVoices / Standard Hindi",
            "source_url": "local_fixtures",
            "license": "CC BY 4.0",
            "speaker_id_if_available": "HINDI_SPK_01",
            "language": "Hindi",
            "original_label_if_available": "clean_speech",
            "category": "indian_languages",
            "original_file": os.path.relpath(fixtures_hindi, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "none",
            "augmentation_parameters": json.dumps({"normalized": True, "target_sr": 16000}),
            "notes": "Standard clean Hindi speech utterance",
        }
        records.append(record)
        matrix_rows.append({
            "Sample": sample_id,
            "Dataset": "Standard Hindi",
            "Language": "Hindi",
            "Category": "indian_languages",
            "Quality": "clean",
            "Purpose": "Indian-language speech handling & ASR (Hindi)",
        })


def build_curated_edge_cases(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Curates extreme edge cases: very short speech, long speech, pure silence, whisper."""
    print("Building curated edge cases set...")
    out_dir = os.path.join(CURATED_DIR, "edge_cases")

    # 1. Very short speech (< 1.2s)
    short_src = os.path.join(ORIGINAL_DIR, "crema_d", "1001_DFA_HAP_XX.wav")
    if os.path.exists(short_src):
        audio, sr = load_audio(short_src)
        audio_16k = resample_audio(audio, sr, 16000)
        # Take first 0.9 seconds
        short_audio = audio_16k[: int(16000 * 0.9)]
        test_path = os.path.join(out_dir, "EDGE_001_very_short_burst.wav")
        save_wav(test_path, short_audio, 16000)
        stats = analyze_audio_properties(short_audio, 16000)

        records.append({
            "sample_id": "EDGE_001",
            "dataset": "CREMA-D",
            "source_url": DATASET_CATALOG["crema_d"]["official_source"],
            "license": DATASET_CATALOG["crema_d"]["license"],
            "speaker_id_if_available": "CREMA_1001",
            "language": "English",
            "original_label_if_available": "short_burst",
            "category": "edge_cases",
            "original_file": os.path.relpath(short_src, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "short_slice",
            "augmentation_parameters": json.dumps({"target_duration_s": 0.9}),
            "notes": "Very short speech burst (< 1 second) to test VAD sensitivity and minimum frame handling",
        })
        matrix_rows.append({
            "Sample": "EDGE_001",
            "Dataset": "CREMA-D",
            "Language": "English",
            "Category": "edge_cases",
            "Quality": "clean",
            "Purpose": "Very short speech burst handling (< 1.0s)",
        })

    # 2. Pure silence (3.0 seconds of digital zero)
    silence_audio = np.zeros(16000 * 3, dtype=np.float32)
    test_path_silence = os.path.join(out_dir, "EDGE_002_pure_silence.wav")
    save_wav(test_path_silence, silence_audio, 16000)
    stats_silence = analyze_audio_properties(silence_audio, 16000)

    records.append({
        "sample_id": "EDGE_002",
        "dataset": "Synthetic_Reference",
        "source_url": "internal_test",
        "license": "CC0",
        "speaker_id_if_available": "none",
        "language": "None",
        "original_label_if_available": "pure_silence",
        "category": "edge_cases",
        "original_file": "none",
        "test_file": os.path.relpath(test_path_silence, TEST_AUDIO_ROOT).replace("\\", "/"),
        "duration_seconds": stats_silence["duration_seconds"],
        "sample_rate": 16000,
        "channels": 1,
        "augmentation": "pure_silence",
        "augmentation_parameters": json.dumps({"duration_s": 3.0}),
        "notes": "3 seconds of pure digital silence to verify pipeline quality gate and VAD zero-burst response",
    })
    matrix_rows.append({
        "Sample": "EDGE_002",
        "Dataset": "Synthetic_Reference",
        "Language": "None",
        "Category": "edge_cases",
        "Quality": "silence",
        "Purpose": "Pipeline silence rejection and zero-VAD test",
    })

    # 3. Extended long speech (> 12 seconds concatenated multi-sentence)
    src1 = os.path.join(ORIGINAL_DIR, "crema_d", "1001_DFA_NEU_XX.wav")
    src2 = os.path.join(ORIGINAL_DIR, "crema_d", "1001_DFA_ANG_XX.wav")
    src3 = os.path.join(ORIGINAL_DIR, "crema_d", "1001_DFA_SAD_XX.wav")
    src4 = os.path.join(ORIGINAL_DIR, "crema_d", "1001_DFA_FEA_XX.wav")
    if all(os.path.exists(s) for s in [src1, src2, src3, src4]):
        chunks = []
        for s in [src1, src2, src3, src4]:
            a, sr = load_audio(s)
            chunks.append(resample_audio(a, sr, 16000))
            chunks.append(np.zeros(int(16000 * 0.4), dtype=np.float32))  # 400ms pause
        long_audio = np.concatenate(chunks)
        test_path_long = os.path.join(out_dir, "EDGE_003_extended_speech_multi_turn.wav")
        save_wav(test_path_long, long_audio, 16000)
        stats_long = analyze_audio_properties(long_audio, 16000)

        records.append({
            "sample_id": "EDGE_003",
            "dataset": "CREMA-D",
            "source_url": DATASET_CATALOG["crema_d"]["official_source"],
            "license": DATASET_CATALOG["crema_d"]["license"],
            "speaker_id_if_available": "CREMA_1001",
            "language": "English",
            "original_label_if_available": "long_speech",
            "category": "edge_cases",
            "original_file": os.path.relpath(src1, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path_long, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats_long["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "concatenation",
            "augmentation_parameters": json.dumps({"num_segments": 4, "pause_ms": 400}),
            "notes": "Extended utterance (> 10s) testing long-audio memory footprint and multi-segment ASR decoding",
        })
        matrix_rows.append({
            "Sample": "EDGE_003",
            "Dataset": "CREMA-D",
            "Language": "English",
            "Category": "edge_cases",
            "Quality": "clean",
            "Purpose": "Extended long-speech handling (> 10s)",
        })

    # 4. Faint whisper / very low SNR speech
    if os.path.exists(short_src):
        a, sr = load_audio(short_src)
        a_16k = resample_audio(a, sr, 16000)
        # Attenuate heavily and add faint noise floor
        whisper_audio = a_16k * 0.04 + np.random.randn(len(a_16k)).astype(np.float32) * 0.003
        test_path_whisper = os.path.join(out_dir, "EDGE_004_faint_whisper_low_snr.wav")
        save_wav(test_path_whisper, whisper_audio, 16000)
        stats_whisper = analyze_audio_properties(whisper_audio, 16000)

        records.append({
            "sample_id": "EDGE_004",
            "dataset": "CREMA-D",
            "source_url": DATASET_CATALOG["crema_d"]["official_source"],
            "license": DATASET_CATALOG["crema_d"]["license"],
            "speaker_id_if_available": "CREMA_1001",
            "language": "English",
            "original_label_if_available": "whisper_low_snr",
            "category": "edge_cases",
            "original_file": os.path.relpath(short_src, TEST_AUDIO_ROOT).replace("\\", "/"),
            "test_file": os.path.relpath(test_path_whisper, TEST_AUDIO_ROOT).replace("\\", "/"),
            "duration_seconds": stats_whisper["duration_seconds"],
            "sample_rate": 16000,
            "channels": 1,
            "augmentation": "whisper_attenuation",
            "augmentation_parameters": json.dumps({"attenuation_factor": 0.04, "noise_floor": 0.003}),
            "notes": "Faint whisper / low SNR test for audio quality diagnostics and ASR thresholding",
        })
        matrix_rows.append({
            "Sample": "EDGE_004",
            "Dataset": "CREMA-D",
            "Language": "English",
            "Category": "edge_cases",
            "Quality": "low_snr",
            "Purpose": "Faint whisper and low-SNR detection robustness",
        })


def build_augmented_variants(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Derives controlled acoustic variants from selected curated base samples."""
    print("Building derived augmented test variants...")

    # We select 4 diverse clean base samples to generate full variant suites:
    # 1. CLEAN_001 (English Male)
    # 2. CLEAN_002 (English Female)
    # 3. EMO_010 (Fearful speech - testing noise robustness on emotional vocalization)
    # 4. IND_001 (Marathi speech - testing noise and degradation on Indian language)
    base_samples = [
        ("CLEAN_001", "curated/clean/CLEAN_001_male_normal.wav", "CREMA-D", "English", "Male"),
        ("CLEAN_002", "curated/clean/CLEAN_002_female_normal.wav", "CREMA-D", "English", "Female"),
        ("EMO_010", "curated/emotional/EMO_010_fear_normal.wav", "CREMA-D", "English", "Male"),
        ("IND_001", "curated/indian_languages/IND_001_mr_MAR_F_HAPPY_00001.wav", "IndicVoices", "Marathi", "Female"),
    ]

    aug_count = 0
    # Directory mapping for variants
    dir_mapping = {
        "noise": os.path.join(AUGMENTED_DIR, "noise"),
        "traffic": os.path.join(AUGMENTED_DIR, "noise"),
        "low_volume": os.path.join(AUGMENTED_DIR, "low_volume"),
        "clipped": os.path.join(AUGMENTED_DIR, "clipping"),
        "reverb": os.path.join(AUGMENTED_DIR, "reverb"),
        "compressed": os.path.join(AUGMENTED_DIR, "compression"),
        "bandlimited": os.path.join(AUGMENTED_DIR, "bandwidth"),
        "silence_inserted": os.path.join(AUGMENTED_DIR, "silence"),
        "truncated": os.path.join(AUGMENTED_DIR, "truncated"),
    }

    for base_id, rel_path, ds_name, lang, gender in base_samples:
        full_base_path = os.path.join(TEST_AUDIO_ROOT, rel_path)
        if not os.path.exists(full_base_path):
            print(f"  Warning: Base file for augmentation not found: {full_base_path}")
            continue

        audio, sr = load_audio(full_base_path)
        if sr != 16000:
            audio = resample_audio(audio, sr, 16000)

        for suffix, func in VARIANT_GENERATORS:
            if suffix == "clean":
                continue  # Clean baseline is already in curated/clean

            aug_count += 1
            aug_id = f"AUG_{aug_count:03d}"
            variant_audio, aug_name, aug_params = func(audio)

            target_sub_dir = dir_mapping.get(suffix, AUGMENTED_DIR)
            out_filename = f"{aug_id}_{base_id}_{suffix}.wav"
            out_filepath = os.path.join(target_sub_dir, out_filename)

            save_wav(out_filepath, variant_audio, 16000)
            stats = analyze_audio_properties(variant_audio, 16000)

            record = {
                "sample_id": aug_id,
                "dataset": ds_name,
                "source_url": DATASET_CATALOG.get(ds_name.lower().replace("-", "_"), {}).get("official_source", "local"),
                "license": DATASET_CATALOG.get(ds_name.lower().replace("-", "_"), {}).get("license", "CC BY 4.0"),
                "speaker_id_if_available": f"{base_id}_{gender}",
                "language": lang,
                "original_label_if_available": f"derived_from_{base_id}",
                "category": "augmented",
                "original_file": rel_path.replace("\\", "/"),
                "test_file": os.path.relpath(out_filepath, TEST_AUDIO_ROOT).replace("\\", "/"),
                "duration_seconds": stats["duration_seconds"],
                "sample_rate": 16000,
                "channels": 1,
                "augmentation": aug_name,
                "augmentation_parameters": json.dumps(aug_params),
                "notes": f"Augmented variant '{suffix}' derived from {base_id} ({lang}, {gender})",
            }
            records.append(record)

            matrix_rows.append({
                "Sample": aug_id,
                "Dataset": ds_name,
                "Language": lang,
                "Category": "augmented",
                "Quality": suffix,
                "Purpose": f"Acoustic robustness test: {aug_name} ({suffix})",
            })


def write_metadata_csvs(records: List[Dict[str, Any]], matrix_rows: List[Dict[str, str]]):
    """Writes samples.csv, sources.csv, test_matrix.csv, and test_matrix.md."""
    # 1. samples.csv
    samples_csv_path = os.path.join(METADATA_DIR, "samples.csv")
    fieldnames = [
        "sample_id",
        "dataset",
        "source_url",
        "license",
        "speaker_id_if_available",
        "language",
        "original_label_if_available",
        "category",
        "original_file",
        "test_file",
        "duration_seconds",
        "sample_rate",
        "channels",
        "augmentation",
        "augmentation_parameters",
        "notes",
    ]

    with open(samples_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
    print(f"Generated metadata: {samples_csv_path} ({len(records)} records)")

    # 2. sources.csv
    sources_csv_path = os.path.join(METADATA_DIR, "sources.csv")
    export_sources_csv(sources_csv_path)

    # 3. test_matrix.csv
    matrix_csv_path = os.path.join(METADATA_DIR, "test_matrix.csv")
    matrix_fields = ["Sample", "Dataset", "Language", "Category", "Quality", "Purpose"]
    with open(matrix_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=matrix_fields)
        writer.writeheader()
        for m in matrix_rows:
            writer.writerow(m)
    print(f"Generated test matrix: {matrix_csv_path} ({len(matrix_rows)} rows)")

    # 4. test_matrix.md
    matrix_md_path = os.path.join(METADATA_DIR, "test_matrix.md")
    with open(matrix_md_path, "w", encoding="utf-8") as f:
        f.write("# SAATHI-AI Audio Pipeline Test Matrix\n\n")
        f.write("This matrix maps each audio sample in the test collection to its testing capability.\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Dataset Rule:** Emotional labels (fear, anger, sadness, etc.) represent acoustic and affective\n")
        f.write("> vocalizations. They are **NOT** equivalent to trauma. Never map emotion signals into 'trauma'.\n\n")
        f.write("| Sample | Dataset | Language | Category | Quality | Purpose |\n")
        f.write("|---|---|---|---|---|---|\n")
        for m in matrix_rows:
            f.write(f"| {m['Sample']} | {m['Dataset']} | {m['Language']} | {m['Category']} | {m['Quality']} | {m['Purpose']} |\n")
    print(f"Generated Markdown test matrix: {matrix_md_path}")


def main():
    print("\n" + "=" * 80)
    print("SAATHI-AI AUDIO TEST SET BUILDER")
    print("=" * 80)

    ensure_directories()
    records: List[Dict[str, Any]] = []
    matrix_rows: List[Dict[str, str]] = []

    # 1. Curated Sets
    build_curated_clean(records, matrix_rows)
    build_curated_emotional(records, matrix_rows)
    build_curated_conversational(records, matrix_rows)
    build_curated_indian_languages(records, matrix_rows)
    build_curated_edge_cases(records, matrix_rows)

    # 2. Augmented Variants
    build_augmented_variants(records, matrix_rows)

    # 3. Export Metadata & Matrices
    write_metadata_csvs(records, matrix_rows)

    print("\n" + "=" * 80)
    print("TEST SET GENERATION COMPLETE")
    print(f"Total Test Audio Files: {len(records)}")
    curated_count = sum(1 for r in records if r["category"] != "augmented")
    augmented_count = sum(1 for r in records if r["category"] == "augmented")
    print(f"  * Curated Benchmark Samples: {curated_count}")
    print(f"  * Augmented Quality Variants: {augmented_count}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
