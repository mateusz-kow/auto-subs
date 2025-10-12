from enum import StrEnum, auto


class SubtitleFormat(StrEnum):
    """Enumeration for the supported subtitle output formats."""

    ASS = auto()
    SRT = auto()
    VTT = auto()
    JSON = auto()
