"""Auto-Subs: A powerful, local-first library for video transcription and subtitle generation."""

from autosubs.api import generate, load, transcribe
from autosubs.core import to_ass, to_json, to_srt, to_vtt

__version__ = "0.6.2"

__all__ = [
    "__version__",
    "generate",
    "transcribe",
    "load",
    "to_json",
    "to_srt",
    "to_vtt",
    "to_ass",
]
