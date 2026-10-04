"""
pipeline_config.py — SAATHI-AI Module Pipeline Configuration
=============================================================

Single source of truth for all module input/output paths.
Every test harness, batch runner, and pipeline script imports
from this module. No path is ever hard-coded elsewhere.

Usage:
    from tools.pipeline_config import PipelineConfig, DataSource

    cfg = PipelineConfig()
    input_dir = cfg.module("m04_quality_check").input_dir
    output_dir = cfg.module("m04_quality_check").output_dir
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ── Resolve paths relative to project root ────────────────────────
_PROJECT_ROOT = Path(__file__).parent.parent
_TEST_AUDIO = _PROJECT_ROOT / "test_audio"
_PIPELINE_IO = _TEST_AUDIO / "pipeline_io"
_INCOMING = _TEST_AUDIO / "incoming"


# ── Module I/O descriptor ─────────────────────────────────────────

@dataclass(frozen=True)
class ModuleIO:
    """Immutable descriptor for one module's input and output folders."""
    module_id: str
    module_callable: str
    input_dir: Path
    output_dir: Path
    output_format: str
    filename_pattern: str
    depends_on: List[str] = field(default_factory=list)

    def input_files(self, glob: str = "*.wav") -> List[Path]:
        """Return sorted list of all input files matching glob."""
        return sorted(self.input_dir.glob(glob))

    def output_path(self, stem: str) -> Path:
        """Return the expected output path for an input file stem."""
        filename = self.filename_pattern.format(stem=stem)
        return self.output_dir / filename

    def ensure_dirs(self) -> None:
        """Create input and output directories if they don't exist."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# ── Data source descriptor ────────────────────────────────────────

@dataclass(frozen=True)
class DataSource:
    """Describes an audio data source and its acquisition status."""
    source_id: str
    status: str          # AVAILABLE | DOWNLOAD_NEEDED | REGISTRATION_NEEDED | PAID
    location: Path
    description: str
    used_by: List[str]
    license: str = ""
    sample_rate: Optional[int] = None
    count_approx: Optional[int] = None
    download_cmd: str = ""
    registration_url: str = ""
    notes: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == "AVAILABLE"

    @property
    def needs_download(self) -> bool:
        return self.status == "DOWNLOAD_NEEDED"

    @property
    def needs_registration(self) -> bool:
        return self.status == "REGISTRATION_NEEDED"


# ── Central pipeline config ───────────────────────────────────────

class PipelineConfig:
    """
    Central registry for all module I/O paths and data sources.

    Example
    -------
    >>> cfg = PipelineConfig()
    >>> cfg.module("m04_quality_check").input_dir
    PosixPath('.../test_audio/pipeline_io/m04_quality_check/input')
    >>> cfg.available_sources()
    [DataSource(source_id='curated_clean', ...), ...]
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleIO] = {}
        self._sources: dict[str, DataSource] = {}
        self._register_modules()
        self._register_sources()

    # ── Module accessors ──────────────────────────────────────────

    def module(self, module_id: str) -> ModuleIO:
        """Return ModuleIO descriptor for the given module ID."""
        if module_id not in self._modules:
            raise KeyError(
                f"Unknown module '{module_id}'. "
                f"Valid IDs: {list(self._modules)}"
            )
        return self._modules[module_id]

    def all_modules(self) -> List[ModuleIO]:
        return list(self._modules.values())

    # ── Source accessors ──────────────────────────────────────────

    def source(self, source_id: str) -> DataSource:
        if source_id not in self._sources:
            raise KeyError(f"Unknown source '{source_id}'.")
        return self._sources[source_id]

    def available_sources(self) -> List[DataSource]:
        """Return only sources that already have audio files on disk."""
        return [s for s in self._sources.values() if s.is_available]

    def pending_downloads(self) -> List[DataSource]:
        """Return sources that need to be downloaded (DOWNLOAD_NEEDED)."""
        return [s for s in self._sources.values() if s.needs_download]

    def pending_registration(self) -> List[DataSource]:
        """Return sources that require account registration first."""
        return [s for s in self._sources.values() if s.needs_registration]

    def sources_for_module(self, module_id: str) -> List[DataSource]:
        """Return all data sources that feed a given module."""
        return [s for s in self._sources.values() if module_id in s.used_by]

    # ── Ensure all dirs exist ─────────────────────────────────────

    def ensure_all_dirs(self) -> None:
        """Create all input/output directories that don't yet exist."""
        for m in self._modules.values():
            m.ensure_dirs()
        _INCOMING.mkdir(parents=True, exist_ok=True)
        (_INCOMING / "external").mkdir(parents=True, exist_ok=True)

    # ── Private registration ──────────────────────────────────────

    def _reg_module(
        self,
        module_id: str,
        callable_path: str,
        filename_pattern: str,
        output_format: str,
        depends_on: Optional[List[str]] = None,
    ) -> None:
        base = _PIPELINE_IO / module_id
        self._modules[module_id] = ModuleIO(
            module_id=module_id,
            module_callable=callable_path,
            input_dir=base / "input",
            output_dir=base / "output",
            output_format=output_format,
            filename_pattern=filename_pattern,
            depends_on=depends_on or [],
        )

    def _reg_source(
        self,
        source_id: str,
        status: str,
        rel_location: str,
        description: str,
        used_by: List[str],
        **kwargs,
    ) -> None:
        self._sources[source_id] = DataSource(
            source_id=source_id,
            status=status,
            location=_PROJECT_ROOT / rel_location,
            description=description,
            used_by=used_by,
            **kwargs,
        )

    def _register_modules(self) -> None:
        self._reg_module(
            "m04_quality_check",
            "services.audio_worker.quality.analyze_audio_quality",
            "{stem}_quality.json",
            "AudioQualityResult (JSON)",
        )
        self._reg_module(
            "m06_preprocessor",
            "services.audio_worker.preprocessor.preprocess_audio",
            "{stem}_16k_mono.wav",
            "WAV 16kHz mono float32",
        )
        self._reg_module(
            "m05_vad",
            "services.audio_worker.vad.detect_voice_activity",
            "{stem}_vad.json",
            "List[SpeechSegment] (JSON)",
            depends_on=["m06_preprocessor"],
        )
        self._reg_module(
            "m07_asr",
            "services.audio_worker.asr.Transcriber.transcribe",
            "{stem}_transcript.json",
            "TranscriptResponse (JSON)",
            depends_on=["m06_preprocessor"],
        )

    def _register_sources(self) -> None:
        # ── Available (already on disk) ───────────────────────────
        for folder, sid, desc, count in [
            ("test_audio/curated/clean",            "curated_clean",            "Clean English speech, 16kHz mono",                                                 8),
            ("test_audio/curated/emotional",         "curated_emotional",         "Acted emotional speech (RAVDESS/CREMA-D), 16kHz",                                  19),
            ("test_audio/curated/conversational",    "curated_conversational",    "Spontaneous conversational speech (Marathi/Punjabi/English)",                       6),
            ("test_audio/curated/edge_cases",        "curated_edge_cases",        "Silence, very short, low-SNR, extended multi-turn",                                 4),
            ("test_audio/curated/indian_languages",  "curated_indian_languages",  "Marathi/Tamil/Telugu/Kannada/Punjabi/Gujarati/Hindi, 16kHz",                       16),
            ("test_audio/augmented",                 "augmented_variants",        "Synthetically degraded: noise/clipping/reverb/compression/bandwidth/silence",      36),
        ]:
            self._reg_source(
                sid, "AVAILABLE", folder, desc,
                used_by=["m04_quality_check", "m06_preprocessor", "m05_vad", "m07_asr"],
                count_approx=count,
                license="Internal test set",
            )

        # ── Download needed (no account required) ─────────────────
        self._reg_source(
            "ds06_911_recordings", "DOWNLOAD_NEEDED",
            "test_audio/incoming/external/911_calls",
            "Real US 911 emergency calls, first 6 seconds, CC0 Public Domain (~700 WAV files)",
            used_by=["m04_quality_check", "m05_vad", "m06_preprocessor", "m07_asr"],
            license="CC0 Public Domain",
            download_cmd="kaggle datasets download -d louisteitelbaum/911-recordings-first-6-seconds",
            notes="Unzip into destination folder. WAV format, variable sample rate.",
        )
        self._reg_source(
            "ds04_axondata", "AVAILABLE",
            "test_audio/incoming/external/axondata",
            "Real English call center audio, 1000+ hours, 8kHz mono (CC BY-NC 4.0)",
            used_by=["m04_quality_check", "m06_preprocessor"],
            license="CC BY-NC 4.0",
            sample_rate=8000,
            download_cmd=(
                "from datasets import load_dataset; "
                "ds = load_dataset('AxonData/english-contact-center-audio-dataset', streaming=True)"
            ),
            notes="Stream and save a 50-file subset. Tests 8kHz→16kHz resampling.",
        )
        self._reg_source(
            "ds11_shemo", "DOWNLOAD_NEEDED",
            "test_audio/incoming/external/shemo",
            "Persian semi-naturalistic emotional speech, 3000 utterances, fear/sadness/anger labels",
            used_by=["m04_quality_check", "m06_preprocessor", "m05_vad", "m07_asr"],
            license="Free for academic use",
            sample_rate=44100,
            download_cmd="git clone https://github.com/mansourehk/ShEMO",
            notes="44.1kHz WAV → resampled to 16kHz by M06. Tests cross-lingual pipeline.",
        )
        self._reg_source(
            "ds05_hindi_calls", "AVAILABLE",
            "test_audio/incoming/external/hindi_calls",
            "Real Hindi telephone dialogues, 8kHz phone quality, 1000+ native speakers",
            used_by=["m04_quality_check", "m06_preprocessor", "m07_asr"],
            license="CC BY-NC-ND 4.0 (Kaggle sample)",
            sample_rate=8000,
            download_cmd="kaggle datasets download -d simaongraves/760h-hindi-phone-calls-dataset",
            notes="8kHz→16kHz resampling required. Tests Hindi ASR on telephone quality.",
        )

        # ── Registration needed (free accounts) ──────────────────
        self._reg_source(
            "ds02_callhome", "AVAILABLE",
            "test_audio/incoming/external/callhome",
            "Real naturalistic telephone conversations, family/friends, 8kHz multilingual",
            used_by=["m04_quality_check", "m06_preprocessor", "m05_vad", "m07_asr"],
            license="TalkBank License (free research)",
            sample_rate=8000,
            registration_url="https://talkbank.org",
        )
        self._reg_source(
            "ds08_daic_woz", "REGISTRATION_NEEDED",
            "test_audio/incoming/external/daic_woz",
            "Clinical distress interviews (DAIC-WOZ), 189 sessions, PHQ-8 scores, WAV",
            used_by=["m04_quality_check", "m05_vad", "m07_asr"],
            license="USC ICT Academic Research License",
            registration_url="https://dcapswoz.ict.usc.edu/",
            notes="Best distress-adjacent labeled dataset. Academic email required.",
        )
        self._reg_source(
            "ds09_vaani", "REGISTRATION_NEEDED",
            "test_audio/incoming/external/vaani",
            "31,000+ hours Indian conversational speech across 100+ languages (IISc/ARTPARK)",
            used_by=["m04_quality_check", "m06_preprocessor", "m07_asr"],
            license="Project Vaani Research License",
            registration_url="https://huggingface.co/ARTPARK-IISc",
            notes="Gated HuggingFace dataset. WAV, variable sample rate.",
        )


# ── Module default config (used by batch runner and pipeline tests) ──

# Execution order: M04 → M06 → (M05 || M07)
PIPELINE_EXECUTION_ORDER = [
    "m04_quality_check",   # Run first: gate on quality
    "m06_preprocessor",    # Normalize to 16kHz mono
    "m05_vad",             # VAD on preprocessed audio
    "m07_asr",             # ASR on preprocessed audio
]

# Quality gate: skip M05/M07 if M04 score falls below this threshold
QUALITY_GATE_THRESHOLD = 0.15


# ── Singleton accessor ────────────────────────────────────────────

_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Return the singleton PipelineConfig instance."""
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config
