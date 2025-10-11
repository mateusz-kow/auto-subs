"""Models related to the Whisper transcription process."""

from enum import StrEnum, auto


class WhisperModel(StrEnum):
    """Enumeration for the supported Whisper model sizes."""

    TINY = auto()
    BASE = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    TURBO = auto()
