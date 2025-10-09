from typing import TypedDict


class WordDict(TypedDict):
    """TypedDict representing a single word in a transcription segment."""

    word: str
    start: float
    end: float


class SegmentDict(TypedDict):
    """TypedDict representing a single segment in a transcription."""

    id: int
    start: float
    end: float
    text: str
    words: list[WordDict]
    seek: int | None
    tokens: list[int] | None
    temperature: float | None
    avg_logprob: float | None
    compression_ratio: float | None
    no_speech_prob: float | None


class Transcription(TypedDict):
    """TypedDict representing a full Whisper transcription output."""

    text: str
    segments: list[SegmentDict]
    language: str
