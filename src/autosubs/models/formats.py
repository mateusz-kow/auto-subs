from enum import StrEnum, auto


class SubtitleFormat(StrEnum):
    """Enumeration for the supported subtitle output formats.
    The enum's value should always be the subtitle file extension.
    """

    ASS = auto()
    SRT = auto()
    VTT = auto()
    JSON = auto()
    MICRODVD = "sub"
    MPL2 = "txt"
