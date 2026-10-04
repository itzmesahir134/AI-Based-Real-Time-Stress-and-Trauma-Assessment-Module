"""Dataset Download and Acquisition Utility for SAATHI-AI.

Downloads curated, small representative subsets (50-150 samples total)
directly from official sources and open mirrors.

Does NOT download massive multi-gigabyte corpora.
For gated datasets (IEMOCAP, MSP-Podcast), prints official EULA instructions
and scans local drop-in folders.

Usage:
    python -m tools.download_dataset crema_d
    python -m tools.download_dataset ravdess
    python -m tools.download_dataset indicvoices
    python -m tools.download_dataset iemocap
    python -m tools.download_dataset msp_podcast
    python -m tools.download_dataset all
"""

import argparse
import io
import json
import os
import sys
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional

# Re-usable HTTP Range stream reader for remote zip archives
class HTTPRangeIO(io.RawIOBase):
    def __init__(self, url: str):
        self.url = url
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            self.length = int(resp.headers.get("Content-Length", 0))
        self.pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.length + offset
        return self.pos

    def tell(self) -> int:
        return self.pos

    def readinto(self, b) -> int:
        size = len(b)
        if self.pos >= self.length or size == 0:
            return 0
        end = min(self.pos + size, self.length)
        req = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Range": f"bytes={self.pos}-{end - 1}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


# ---------------------------------------------------------------------------
# 1. CREMA-D Downloader
# ---------------------------------------------------------------------------
# Selected diverse actor IDs covering gender and ethnic diversity:
# 1001: Male, 51, Caucasian
# 1002: Female, 26, Caucasian
# 1003: Female, 22, African American
# 1004: Female, 48, Hispanic
# 1005: Male, 31, Caucasian
# 1010: Female, 40, Asian
# 1011: Male, 46, African American
# 1035: Male, 25, Asian

CREMA_TARGET_SAMPLES = [
    # Actor 1001 (Male, 51, Caucasian)
    "1001_DFA_NEU_XX.wav",
    "1001_DFA_ANG_XX.wav",
    "1001_DFA_FEA_XX.wav",
    "1001_DFA_HAP_XX.wav",
    "1001_DFA_SAD_XX.wav",
    "1001_DFA_DIS_XX.wav",
    # Actor 1002 (Female, 26, Caucasian)
    "1002_IEO_NEU_XX.wav",
    "1002_IEO_ANG_HI.wav",
    "1002_IEO_FEA_MD.wav",
    "1002_IEO_HAP_LO.wav",
    "1002_IEO_SAD_HI.wav",
    "1002_IEO_DIS_MD.wav",
    # Actor 1003 (Female, 22, African American)
    "1003_TSI_NEU_XX.wav",
    "1003_IEO_ANG_LO.wav",
    "1003_IEO_FEA_LO.wav",
    "1003_IEO_HAP_LO.wav",
    "1003_IEO_SAD_LO.wav",
    # Actor 1004 (Female, 48, Hispanic)
    "1004_IWW_NEU_XX.wav",
    "1004_IEO_ANG_LO.wav",
    "1004_IEO_FEA_LO.wav",
    "1004_IEO_HAP_LO.wav",
    "1004_IEO_SAD_LO.wav",
    # Actor 1005 (Male, 31, Caucasian)
    "1005_MTI_NEU_XX.wav",
    "1005_IEO_ANG_LO.wav",
    "1005_IEO_FEA_LO.wav",
    "1005_IEO_HAP_LO.wav",
    "1005_IEO_SAD_LO.wav",
    # Actor 1010 (Female, 40, Asian)
    "1010_IEO_NEU_XX.wav",
    "1010_IEO_ANG_LO.wav",
    "1010_IEO_FEA_LO.wav",
    "1010_IEO_HAP_LO.wav",
    "1010_IEO_SAD_LO.wav",
]


def download_crema_d(target_dir: str = "test_audio/original/crema_d") -> List[str]:
    """Downloads curated CREMA-D samples directly from official GitHub repository."""
    os.makedirs(target_dir, exist_ok=True)
    base_url = "https://media.githubusercontent.com/media/CheyneyComputerScience/CREMA-D/master/AudioWAV/"

    print("\n" + "=" * 70)
    print("DOWNLOADING CURATED CREMA-D SUBSET")
    print("Official Source: https://github.com/CheyneyComputerScience/CREMA-D")
    print("License: ODbL v1.0 | Target Directory:", target_dir)
    print("=" * 70)

    downloaded = []
    for fn in CREMA_TARGET_SAMPLES:
        out_path = os.path.join(target_dir, fn)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            downloaded.append(out_path)
            print(f"  [cached] {fn}")
            continue

        url = base_url + fn
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(out_path, "wb") as f:
                        f.write(data)
                    downloaded.append(out_path)
                    print(f"  [downloaded] {fn} ({len(data)} bytes)")
                else:
                    print(f"  [skip pointer] {fn}")
        except Exception as e:
            print(f"  [error] {fn}: {e}")

    print(f"CREMA-D: {len(downloaded)}/{len(CREMA_TARGET_SAMPLES)} files ready in {target_dir}")
    return downloaded


# ---------------------------------------------------------------------------
# 2. RAVDESS Downloader
# ---------------------------------------------------------------------------
# Selected RAVDESS files:
# Actor 01 (Male):
# 03-01-01-01-01-01-01: Neutral normal
# 03-01-02-01-01-01-01: Calm normal
# 03-01-03-01-01-01-01: Happy normal
# 03-01-04-01-01-01-01: Sad normal
# 03-01-05-01-01-01-01: Angry normal
# 03-01-06-01-01-01-01: Fearful normal
# 03-01-05-02-01-01-01: Angry strong
# 03-01-06-02-01-01-01: Fearful strong
# Actor 02 (Female):
# 03-01-01-01-01-01-02: Neutral normal
# 03-01-02-01-01-01-02: Calm normal
# 03-01-03-01-01-01-02: Happy normal
# 03-01-04-01-01-01-02: Sad normal
# 03-01-05-01-01-01-02: Angry normal
# 03-01-06-01-01-01-02: Fearful normal
# 03-01-05-02-01-01-02: Angry strong
# 03-01-06-02-01-01-02: Fearful strong

RAVDESS_TARGET_FILES = [
    # Actor 01 (Male)
    "Actor_01/03-01-01-01-01-01-01.wav",
    "Actor_01/03-01-02-01-01-01-01.wav",
    "Actor_01/03-01-03-01-01-01-01.wav",
    "Actor_01/03-01-04-01-01-01-01.wav",
    "Actor_01/03-01-05-01-01-01-01.wav",
    "Actor_01/03-01-06-01-01-01-01.wav",
    "Actor_01/03-01-05-02-01-01-01.wav",
    "Actor_01/03-01-06-02-01-01-01.wav",
    # Actor 02 (Female)
    "Actor_02/03-01-01-01-01-01-02.wav",
    "Actor_02/03-01-02-01-01-01-02.wav",
    "Actor_02/03-01-03-01-01-01-02.wav",
    "Actor_02/03-01-04-01-01-01-02.wav",
    "Actor_02/03-01-05-01-01-01-02.wav",
    "Actor_02/03-01-06-01-01-01-02.wav",
    "Actor_02/03-01-05-02-01-01-02.wav",
    "Actor_02/03-01-06-02-01-01-02.wav",
]


def download_ravdess(target_dir: str = "test_audio/original/ravdess") -> List[str]:
    """Downloads curated RAVDESS samples via fast HTTP range extraction from official zip."""
    os.makedirs(target_dir, exist_ok=True)
    zip_url = "https://huggingface.co/datasets/HoangPhuc7679/RAVDESS/resolve/main/Audio_Speech_Actors_01-24.zip"

    print("\n" + "=" * 70)
    print("DOWNLOADING CURATED RAVDESS SUBSET")
    print("Official Source: Zenodo Record 1188976 / Open Mirror")
    print("License: CC BY-NC-SA 4.0 | Target Directory:", target_dir)
    print("=" * 70)

    # Check which files already exist
    needed = []
    downloaded = []
    for entry in RAVDESS_TARGET_FILES:
        fn = os.path.basename(entry)
        out_path = os.path.join(target_dir, fn)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            downloaded.append(out_path)
            print(f"  [cached] {fn}")
        else:
            needed.append(entry)

    if not needed:
        print(f"All {len(RAVDESS_TARGET_FILES)} RAVDESS files already present in {target_dir}")
        return downloaded

    print(f"Fetching {len(needed)} files from remote archive using HTTP Range requests...")
    try:
        rio = HTTPRangeIO(zip_url)
        with zipfile.ZipFile(rio) as zf:
            for entry in needed:
                fn = os.path.basename(entry)
                out_path = os.path.join(target_dir, fn)
                try:
                    data = zf.read(entry)
                    with open(out_path, "wb") as f:
                        f.write(data)
                    downloaded.append(out_path)
                    print(f"  [extracted] {fn} ({len(data)} bytes)")
                except Exception as e:
                    print(f"  [error extracting] {entry}: {e}")
    except Exception as e:
        print(f"Error accessing remote RAVDESS archive: {e}")

    print(f"RAVDESS: {len(downloaded)}/{len(RAVDESS_TARGET_FILES)} files ready in {target_dir}")
    return downloaded


# ---------------------------------------------------------------------------
# 3. IndicVoices / AI4Bharat Downloader
# ---------------------------------------------------------------------------
# We fetch genuine Indian language samples:
# - AI4Bharat official prompts repository:
#   * Kannada (KAN_F_HAPPY_00001.wav)
#   * Marathi (MAR_F_HAPPY_00001.wav, MAR_F_WIKI_00001.wav, MAR_M_WIKI_00001.wav)
#   * Punjabi (PAN_F_HAPPY_00001.wav, PAN_F_HAPPY_00002.wav)
#   * Tamil (TAM_F_HAPPY_00001.wav)
# - OpenSLR range extraction for native speech:
#   * Marathi (SLR64 female native speaker)
#   * Tamil (SLR65 female native speaker)
#   * Telugu (SLR66 female native speaker)
#   * Gujarati (SLR78 female native speaker)

AI4BHARAT_FILES = [
    ("KAN_F_HAPPY_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/KAN_F_HAPPY_00001.wav", "kn", "Kannada", "Female"),
    ("MAR_F_HAPPY_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/MAR_F_HAPPY_00001.wav", "mr", "Marathi", "Female"),
    ("MAR_F_WIKI_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/MAR_F_WIKI_00001.wav", "mr", "Marathi", "Female"),
    ("MAR_M_WIKI_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/MAR_M_WIKI_00001.wav", "mr", "Marathi", "Male"),
    ("PAN_F_HAPPY_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/PAN_F_HAPPY_00001.wav", "pa", "Punjabi", "Female"),
    ("PAN_F_HAPPY_00002.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/PAN_F_HAPPY_00002.wav", "pa", "Punjabi", "Female"),
    ("TAM_F_HAPPY_00001.wav", "https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/prompts/TAM_F_HAPPY_00001.wav", "ta", "Tamil", "Female"),
]

OPENSLR_RESOURCES = [
    # (res_id, zip_name, lang_code, lang_name, num_samples)
    ("64", "mr_in_female.zip", "mr", "Marathi", 3),
    ("65", "ta_in_female.zip", "ta", "Tamil", 3),
    ("66", "te_in_female.zip", "te", "Telugu", 3),
    ("78", "gu_in_female.zip", "gu", "Gujarati", 3),
]


def download_indicvoices(target_dir: str = "test_audio/original/indicvoices") -> List[str]:
    """Downloads curated Indian-language speech samples across multiple languages."""
    os.makedirs(target_dir, exist_ok=True)
    downloaded = []

    print("\n" + "=" * 70)
    print("DOWNLOADING CURATED INDIAN-LANGUAGE SPEECH SUBSET")
    print("Official Sources: AI4Bharat (IIT Madras) & OpenSLR Crowdsourced Corpora")
    print("License: CC BY 4.0 / CC BY-SA 4.0 | Target Directory:", target_dir)
    print("=" * 70)

    # 1. Fetch AI4Bharat prompts
    for fn, url, lang_code, lang_name, gender in AI4BHARAT_FILES:
        out_path = os.path.join(target_dir, fn)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            downloaded.append(out_path)
            print(f"  [cached] {fn} ({lang_name}, {gender})")
            continue

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                with open(out_path, "wb") as f:
                    f.write(data)
                downloaded.append(out_path)
                print(f"  [downloaded] {fn} ({lang_name}, {gender}, {len(data)} bytes)")
        except Exception as e:
            print(f"  [error] {fn}: {e}")

    # 2. Extract OpenSLR samples via HTTP Range
    for res_id, zip_name, lang_code, lang_name, n_extract in OPENSLR_RESOURCES:
        url = f"https://openslr.elda.org/resources/{res_id}/{zip_name}"
        try:
            rio = HTTPRangeIO(url)
            with zipfile.ZipFile(rio) as zf:
                wavs = [w for w in zf.namelist() if w.endswith(".wav")][:n_extract]
                for w in wavs:
                    base_w = os.path.basename(w)
                    out_name = f"slr{res_id}_{lang_code}_{base_w}"
                    out_path = os.path.join(target_dir, out_name)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                        downloaded.append(out_path)
                        print(f"  [cached] {out_name} ({lang_name})")
                        continue
                    data = zf.read(w)
                    with open(out_path, "wb") as f:
                        f.write(data)
                    downloaded.append(out_path)
                    print(f"  [extracted] {out_name} ({lang_name}, {len(data)} bytes)")
        except Exception as e:
            print(f"  [warning] Could not range-fetch OpenSLR {res_id} ({lang_name}): {e}")

    print(f"IndicVoices / Indian Languages: {len(downloaded)} files ready in {target_dir}")
    return downloaded


# ---------------------------------------------------------------------------
# 4. IEMOCAP Instructions
# ---------------------------------------------------------------------------
def instruct_iemocap(target_dir: str = "test_audio/original/iemocap") -> None:
    """Explains IEMOCAP academic license, acquisition steps, and checks drop-in folder."""
    os.makedirs(target_dir, exist_ok=True)
    existing = [f for f in os.listdir(target_dir) if f.lower().endswith((".wav", ".flac"))]

    print("\n" + "=" * 70)
    print("IEMOCAP DATASET ACQUISITION INSTRUCTIONS")
    print("=" * 70)
    print("IEMOCAP (Interactive Emotional Dyadic Motion Capture) is a restricted-access")
    print("research corpus hosted by the SAIL Lab at University of Southern California (USC).")
    print("\nLicense & Terms:")
    print("  * License: USC SAIL Academic Research End-User License Agreement (EULA)")
    print("  * Redistribution: PROHIBITED. Automated direct scraping is strictly forbidden.")
    print("  * Permitted Use: Academic research and non-commercial internal evaluation.")
    print("\nHow to acquire and integrate:")
    print("  1. Visit the official registration portal:")
    print("     https://sail.usc.edu/iemocap/release_form.php")
    print("  2. Submit your academic/research affiliation and sign the electronic agreement.")
    print("  3. Once approved, download the session archive (e.g. Session1.tar.gz).")
    print("  4. Extract representative conversational WAV files into:")
    print(f"     {os.path.abspath(target_dir)}")
    print("\nDirectory Status:")
    if existing:
        print(f"  * Status: READY - Found {len(existing)} audio files in {target_dir}")
        for f in existing[:5]:
            print(f"    - {f}")
        if len(existing) > 5:
            print(f"    - ... and {len(existing) - 5} more files")
    else:
        print(f"  * Status: EMPTY - No files currently in {target_dir}")
        print("  * Once you place WAV files here, 'python -m tools.build_test_set' will")
        print("    automatically normalize and index them into the conversational test suite.")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# 5. MSP-Podcast Instructions
# ---------------------------------------------------------------------------
def instruct_msp_podcast(target_dir: str = "test_audio/original/msp_podcast") -> None:
    """Explains MSP-Podcast academic license, acquisition steps, and checks drop-in folder."""
    os.makedirs(target_dir, exist_ok=True)
    existing = [f for f in os.listdir(target_dir) if f.lower().endswith((".wav", ".flac"))]

    print("\n" + "=" * 70)
    print("MSP-PODCAST DATASET ACQUISITION INSTRUCTIONS")
    print("=" * 70)
    print("MSP-Podcast is a large-scale corpus of spontaneous conversational speech")
    print("collected in the wild, hosted by the MSP Lab at the University of Texas at Dallas.")
    print("\nLicense & Terms:")
    print("  * License: UT Dallas MSP-Podcast Academic License Agreement")
    print("  * Redistribution: PROHIBITED without written institutional approval.")
    print("  * Permitted Use: Non-commercial academic research.")
    print("\nHow to acquire and integrate:")
    print("  1. Visit the official MSP Lab portal:")
    print("     https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html")
    print("  2. Fill out and submit the academic license request form.")
    print("  3. Follow the secure download link provided by UT Dallas.")
    print("  4. Place representative spontaneous speech WAV clips into:")
    print(f"     {os.path.abspath(target_dir)}")
    print("\nDirectory Status:")
    if existing:
        print(f"  * Status: READY - Found {len(existing)} audio files in {target_dir}")
        for f in existing[:5]:
            print(f"    - {f}")
        if len(existing) > 5:
            print(f"    - ... and {len(existing) - 5} more files")
    else:
        print(f"  * Status: EMPTY - No files currently in {target_dir}")
        print("  * Once you place WAV files here, 'python -m tools.build_test_set' will")
        print("    automatically normalize and index them into the conversational test suite.")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Download curated test speech datasets for SAATHI-AI")
    parser.add_argument(
        "dataset",
        choices=["crema_d", "ravdess", "indicvoices", "iemocap", "msp_podcast", "all"],
        help="Dataset to download or acquire instructions for",
    )
    args = parser.parse_args()

    ds = args.dataset.lower()
    if ds in ("crema_d", "all"):
        download_crema_d()
    if ds in ("ravdess", "all"):
        download_ravdess()
    if ds in ("indicvoices", "all"):
        download_indicvoices()
    if ds in ("iemocap", "all"):
        instruct_iemocap()
    if ds in ("msp_podcast", "all"):
        instruct_msp_podcast()


if __name__ == "__main__":
    main()
