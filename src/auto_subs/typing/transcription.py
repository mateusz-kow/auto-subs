from typing import NotRequired, TypedDict


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
    seek: NotRequired[int]
    tokens: NotRequired[list[int]]
    temperature: NotRequired[float]
    avg_logprob: NotRequired[float]
    compression_ratio: NotRequired[float]
    no_speech_prob: NotRequired[float]


class TranscriptionDict(TypedDict):
    """TypedDict representing a full Whisper transcription output."""

    text: str
    segments: list[SegmentDict]
    language: str
