"""Dataset discovery, specification, and status reporting tool.

Investigates and catalogs the 5 core speech benchmark datasets:
1. CREMA-D (Crowd-sourced Emotional Multimodal Actors Dataset)
2. RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
3. IEMOCAP (Interactive Emotional Dyadic Motion Capture Database)
4. MSP-Podcast (Multimodal Speech Processing Podcast)
5. IndicVoices / AI4Bharat Speech Datasets

Usage:
    python -m tools.list_datasets
    python -m tools.list_datasets --dataset crema_d
    python -m tools.list_datasets --json
    python -m tools.list_datasets --export-csv test_audio/metadata/sources.csv
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

DATASET_CATALOG: Dict[str, Dict[str, Any]] = {
    "crema_d": {
        "id": "crema_d",
        "name": "CREMA-D",
        "full_title": "Crowd-sourced Emotional Multimodal Actors Dataset",
        "official_source": "https://github.com/CheyneyComputerScience/CREMA-D",
        "download_method": "Direct Git LFS / GitHub CDN (automated small subset fetch supported)",
        "license": "Open Database License (ODbL) v1.0 / Open Data Commons Attribution",
        "attribution_required": True,
        "citation": "Cao et al., 'CREMA-D: Crowd-sourced Emotional Multimodal Actors Dataset', IEEE Transactions on Affective Computing, 2014.",
        "commercial_restrictions": "Permissive with attribution and share-alike (ODbL)",
        "languages": ["English"],
        "num_speakers": 91,
        "speaker_demographics": "48 male, 43 female actors; Caucasian, African American, Asian, Hispanic",
        "native_audio_format": "WAV, 16,000 Hz, 16-bit, Mono",
        "available_labels": [
            "anger (ANG)",
            "disgust (DIS)",
            "fear (FEA)",
            "happiness (HAP)",
            "neutral (NEU)",
            "sadness (SAD)",
            "intensities: low (LO), medium (MD), high (HI), unspecified (XX)",
        ],
        "label_mapping_rule": "Emotions are acoustic/affective states. NEVER map fear/sadness/anger to 'trauma'.",
        "transcripts_available": True,
        "transcript_notes": "12 standard sentences (e.g. 'It's eleven o'clock', 'Don't forget a jacket')",
        "approx_full_size": "~600 MB (audio), ~30 GB (video)",
        "test_subset_size": "~5-15 MB (15-30 audio files)",
        "local_dir": os.path.join("test_audio", "original", "crema_d"),
        "access_type": "Open Access / Automated Download",
    },
    "ravdess": {
        "id": "ravdess",
        "name": "RAVDESS",
        "full_title": "Ryerson Audio-Visual Database of Emotional Speech and Song",
        "official_source": "https://zenodo.org/records/1188976",
        "download_method": "Zenodo Open Access / Hugging Face mirrors (automated subset fetch supported)",
        "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "attribution_required": True,
        "citation": "Livingstone SR, Russo FA (2018) The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS). PLoS ONE 13(5): e0196391.",
        "commercial_restrictions": "Non-commercial only (CC BY-NC-SA 4.0). Internal testing & academic evaluation allowed.",
        "languages": ["North American English"],
        "num_speakers": 24,
        "speaker_demographics": "12 male, 12 female professional actors",
        "native_audio_format": "WAV, 48,000 Hz, 16-bit, Stereo (downmixed to 16kHz mono in test set)",
        "available_labels": [
            "neutral (01)",
            "calm (02)",
            "happy (03)",
            "sad (04)",
            "angry (05)",
            "fearful (06)",
            "disgust (07)",
            "surprised (08)",
            "intensities: normal (01), strong (02)",
        ],
        "label_mapping_rule": "Emotional labels represent vocal acting. NEVER map to trauma.",
        "transcripts_available": True,
        "transcript_notes": "Two standard statements: 'Kids are talking by the door', 'Dogs are sitting by the door'",
        "approx_full_size": "~1.04 GB (audio speech zip)",
        "test_subset_size": "~5-10 MB (10-20 audio files)",
        "local_dir": os.path.join("test_audio", "original", "ravdess"),
        "access_type": "Open Access / Mirror Download",
    },
    "iemocap": {
        "id": "iemocap",
        "name": "IEMOCAP",
        "full_title": "Interactive Emotional Dyadic Motion Capture Database",
        "official_source": "https://sail.usc.edu/iemocap/",
        "download_method": "Gated Academic EULA application via USC SAIL (manual agreement required)",
        "license": "USC SAIL Academic Research End User License Agreement (EULA)",
        "attribution_required": True,
        "citation": "Busso et al., 'IEMOCAP: Interactive emotional dyadic motion capture database', LREC, 2008.",
        "commercial_restrictions": "Strictly Academic / Non-commercial research. Redistribution strictly prohibited.",
        "languages": ["English"],
        "num_speakers": 10,
        "speaker_demographics": "5 male, 5 female actors in dyadic interaction sessions",
        "native_audio_format": "WAV, 16,000 Hz, 16-bit, 2-channel / Mono",
        "available_labels": [
            "natural conversational turns",
            "spontaneous dialogue vs scripted",
            "categorical: angry, happy, sad, neutral, excited, frustration",
            "dimensional: valence, activation, dominance",
        ],
        "label_mapping_rule": "Spontaneous conversational signals. Do NOT equate distress/frustration with trauma.",
        "transcripts_available": True,
        "transcript_notes": "Full time-aligned turn-by-turn dialogue transcripts",
        "approx_full_size": "~2.5 GB (audio + transcripts)",
        "test_subset_size": "~10-25 MB (subset placed by user post-EULA)",
        "local_dir": os.path.join("test_audio", "original", "iemocap"),
        "access_type": "Gated Academic Request (Place in test_audio/original/iemocap/)",
    },
    "msp_podcast": {
        "id": "msp_podcast",
        "name": "MSP-Podcast",
        "full_title": "Multimodal Speech Processing Podcast Database",
        "official_source": "https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html",
        "download_method": "Gated Academic EULA application via UT Dallas MSP Lab (manual approval required)",
        "license": "UT Dallas MSP-Podcast Academic License Agreement",
        "attribution_required": True,
        "citation": "Lotfian R, Busso C, 'Building Natural Emotional Datasets in the Wild: MSP-Podcast', IEEE TAC, 2017.",
        "commercial_restrictions": "Academic research only without explicit commercial license agreement.",
        "languages": ["Natural English (various regional and global accents)"],
        "num_speakers": 1200,
        "speaker_demographics": "Diverse conversational podcast hosts and guests (>1,200 unique speakers)",
        "native_audio_format": "WAV, 16,000 Hz / 44,100 Hz, 16-bit",
        "available_labels": [
            "in-the-wild spontaneous speech",
            "conversational interruptions and backchannels",
            "categorical: anger, sadness, happiness, fear, disgust, neutral",
            "continuous: arousal, valence, dominance",
        ],
        "label_mapping_rule": "Natural podcast acoustics. Real conversational flow; not clinical trauma.",
        "transcripts_available": True,
        "transcript_notes": "Automated and manual transcripts for spontaneous segments",
        "approx_full_size": ">100 GB (full corpus v1.10+)",
        "test_subset_size": "~10-30 MB (curated podcast excerpts)",
        "local_dir": os.path.join("test_audio", "original", "msp_podcast"),
        "access_type": "Gated Academic Request (Place in test_audio/original/msp_podcast/)",
    },
    "indicvoices": {
        "id": "indicvoices",
        "name": "IndicVoices / AI4Bharat",
        "full_title": "IndicVoices: Multilingual Speech Dataset for Indian Languages",
        "official_source": "https://ai4bharat.iitm.ac.in/indicvoices/ & https://www.openslr.org",
        "download_method": "Open Access via AI4Bharat GitHub / OpenSLR mirrors (automated range-fetch supported)",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0) / CC BY-SA 4.0",
        "attribution_required": True,
        "citation": "AI4Bharat, 'IndicVoices: Towards building an inclusive multilingual speech dataset for Indian languages', arXiv:2403.01926, 2024.",
        "commercial_restrictions": "Permissive (CC BY 4.0) with attribution",
        "languages": [
            "Hindi (hi)",
            "Marathi (mr)",
            "Bengali (bn)",
            "Tamil (ta)",
            "Telugu (te)",
            "Kannada (kn)",
            "Gujarati (gu)",
            "Punjabi (pa)",
            "Malayalam (ml)",
        ],
        "num_speakers": 22563,
        "speaker_demographics": "22,500+ native speakers across 208 Indian districts; male & female, diverse age groups",
        "native_audio_format": "WAV / FLAC, 16,000 Hz / 48,000 Hz, 16-bit Mono",
        "available_labels": [
            "spontaneous extempore speech (76%)",
            "conversational dialogue (15%)",
            "read speech (8%)",
            "speaker gender, district, state",
        ],
        "label_mapping_rule": "Multilingual Indian speech acoustics. Used to test language handling and ASR.",
        "transcripts_available": True,
        "transcript_notes": "Native Indic scripts (Devanagari, Tamil, Telugu, etc.) and Latin phonetic text",
        "approx_full_size": ">1.5 TB (12,000 hours across 22 languages)",
        "test_subset_size": "~10-25 MB (15-30 audio files across 7+ Indian languages)",
        "local_dir": os.path.join("test_audio", "original", "indicvoices"),
        "access_type": "Open Access / Range Fetch & Open Repositories",
    },
}


def check_local_samples(dataset_id: str) -> Dict[str, Any]:
    """Inspects local filesystem for existing samples in original/ and curated/ directories."""
    ds = DATASET_CATALOG.get(dataset_id)
    if not ds:
        return {"original_count": 0, "curated_count": 0, "paths": []}

    orig_dir = ds["local_dir"]
    orig_files = []
    if os.path.exists(orig_dir):
        orig_files = [f for f in os.listdir(orig_dir) if f.lower().endswith((".wav", ".flac", ".mp3"))]

    curated_dir = os.path.join("test_audio", "curated")
    curated_count = 0
    if os.path.exists(curated_dir):
        for root, _, files in os.walk(curated_dir):
            for f in files:
                if dataset_id in f.lower() or (dataset_id == "crema_d" and "crema" in f.lower()):
                    curated_count += 1

    return {
        "original_count": len(orig_files),
        "curated_count": curated_count,
        "orig_dir_exists": os.path.exists(orig_dir),
    }


def print_datasets_overview() -> None:
    """Prints a structured summary table of all benchmark speech datasets."""
    print("\n" + "=" * 80)
    print("SAATHI-AI SPEECH TEST DATASET CATALOG & SPECIFICATIONS")
    print("=" * 80)
    print("CRITICAL PRINCIPLE:")
    print("  Emotion, fear, sadness, anger, stress != trauma.")
    print("  These datasets test acoustic stability, emotion handling, noise, and languages.")
    print("  Never map emotion or acoustic distress to 'trauma'.")
    print("=" * 80 + "\n")

    for key, ds in DATASET_CATALOG.items():
        status = check_local_samples(key)
        print(f"[{ds['name']}] - {ds['full_title']}")
        print(f"  * Source:         {ds['official_source']}")
        print(f"  * Access:         {ds['access_type']}")
        print(f"  * License:        {ds['license']}")
        print(f"  * Restrictions:   {ds['commercial_restrictions']}")
        print(f"  * Languages:      {', '.join(ds['languages'][:4])}{'...' if len(ds['languages']) > 4 else ''}")
        print(f"  * Speakers:       {ds['num_speakers']} ({ds['speaker_demographics'][:60]}...)")
        print(f"  * Native Format:  {ds['native_audio_format']}")
        print(f"  * Download Size:  Full: {ds['approx_full_size']} | Test subset: {ds['test_subset_size']}")
        print(f"  * Local Samples:  {status['original_count']} original files in {ds['local_dir']}")
        print(f"  * Purpose:        {ds['available_labels'][0] if ds['available_labels'] else 'Acoustic testing'}")
        print("-" * 80)


def print_single_dataset(dataset_id: str) -> None:
    """Prints comprehensive details for a single dataset."""
    key = dataset_id.lower().replace("-", "_")
    ds = DATASET_CATALOG.get(key)
    if not ds:
        print(f"Error: Unknown dataset '{dataset_id}'. Choose from: {list(DATASET_CATALOG.keys())}")
        return

    status = check_local_samples(key)
    print("\n" + "=" * 80)
    print(f"DATASET SPECIFICATION: {ds['name']} ({ds['full_title']})")
    print("=" * 80)
    print(f"Official Source:         {ds['official_source']}")
    print(f"Access & Download:       {ds['download_method']}")
    print(f"License:                 {ds['license']}")
    print(f"Attribution Required:    {'Yes' if ds['attribution_required'] else 'No'}")
    print(f"Citation:                {ds['citation']}")
    print(f"Restrictions:            {ds['commercial_restrictions']}")
    print(f"Supported Languages:     {', '.join(ds['languages'])}")
    print(f"Number of Speakers:      {ds['num_speakers']}")
    print(f"Demographics:            {ds['speaker_demographics']}")
    print(f"Native Format:           {ds['native_audio_format']}")
    print(f"Transcripts:             {'Available' if ds['transcripts_available'] else 'None'} ({ds['transcript_notes']})")
    print(f"Approx Download Size:    Full: {ds['approx_full_size']} | Curated Test Target: {ds['test_subset_size']}")
    print("\nAvailable Labels & Signal Categories:")
    for lbl in ds["available_labels"]:
        print(f"  - {lbl}")
    print(f"\nLabel Rule:              {ds['label_mapping_rule']}")
    print(f"Local Storage Dir:       {ds['local_dir']}")
    print(f"Local Samples Found:     {status['original_count']} original, {status['curated_count']} curated")
    print("=" * 80 + "\n")


def export_sources_csv(output_path: str = "test_audio/metadata/sources.csv") -> None:
    """Exports dataset catalog to metadata/sources.csv."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fieldnames = [
        "dataset_id",
        "dataset_name",
        "full_title",
        "official_source",
        "license",
        "attribution_required",
        "citation",
        "commercial_restrictions",
        "languages",
        "num_speakers",
        "native_audio_format",
        "transcripts_available",
        "approx_full_size",
        "test_subset_size",
        "access_type",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for k, v in DATASET_CATALOG.items():
            writer.writerow({
                "dataset_id": v["id"],
                "dataset_name": v["name"],
                "full_title": v["full_title"],
                "official_source": v["official_source"],
                "license": v["license"],
                "attribution_required": v["attribution_required"],
                "citation": v["citation"],
                "commercial_restrictions": v["commercial_restrictions"],
                "languages": "; ".join(v["languages"]),
                "num_speakers": v["num_speakers"],
                "native_audio_format": v["native_audio_format"],
                "transcripts_available": v["transcripts_available"],
                "approx_full_size": v["approx_full_size"],
                "test_subset_size": v["test_subset_size"],
                "access_type": v["access_type"],
            })
    print(f"Exported dataset catalog to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Discover and inspect speech benchmark datasets for SAATHI-AI")
    parser.add_argument("--dataset", "-d", type=str, help="Specific dataset to inspect (e.g. crema_d, ravdess, indicvoices)")
    parser.add_argument("--json", action="store_true", help="Output catalog as JSON")
    parser.add_argument("--export-csv", type=str, help="Export catalog to CSV filepath", nargs="?", const="test_audio/metadata/sources.csv")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(DATASET_CATALOG, indent=2))
        return

    if args.export_csv:
        export_sources_csv(args.export_csv)
        return

    if args.dataset:
        print_single_dataset(args.dataset)
    else:
        print_datasets_overview()


if __name__ == "__main__":
    main()
