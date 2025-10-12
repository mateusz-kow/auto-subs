"""Models related to the Whisper transcription process."""

from enum import StrEnum


class WhisperModel(StrEnum):
    """Enumeration for the supported Whisper model sizes."""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
