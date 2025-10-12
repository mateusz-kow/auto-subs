"""Auto-Subs: A powerful, local-first library for video transcription and subtitle generation."""

from autosubs.api import generate, load, transcribe
from autosubs.core.generator import (
    format_ass_timestamp,
    format_srt_timestamp,
    format_vtt_timestamp,
)
from autosubs.core.parser import (
    ass_timestamp_to_seconds,
    srt_timestamp_to_seconds,
    vtt_timestamp_to_seconds,
)

__version__ = "0.4.0"

__all__ = [
    "__version__",
    "generate",
    "transcribe",
    "load",
    "format_srt_timestamp",
    "format_vtt_timestamp",
    "format_ass_timestamp",
    "srt_timestamp_to_seconds",
    "vtt_timestamp_to_seconds",
    "ass_timestamp_to_seconds",
]
