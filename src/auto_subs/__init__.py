"""Auto-Subs: A powerful, local-first library for video transcription and subtitle generation."""

from auto_subs.api import generate, load, transcribe

__version__ = "0.3.2"

__all__ = ["__version__", "generate", "transcribe", "load"]
