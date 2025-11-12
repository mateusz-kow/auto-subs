from pydantic import TypeAdapter

from autosubs.models.styles import WordStyleRange
from autosubs.models.subtitles import (
    AssSubtitles,
    AssSubtitleSegment,
    AssSubtitleWord,
    Subtitles,
    SubtitleSegment,
    SubtitleWord,
)
from autosubs.models.transcription import TranscriptionModel

TRANSCRIPTION_ADAPTER: TypeAdapter[TranscriptionModel] = TypeAdapter(TranscriptionModel)

__all__ = [
    "SubtitleWord",
    "SubtitleSegment",
    "Subtitles",
    "TranscriptionModel",
    "TRANSCRIPTION_ADAPTER",
    "AssSubtitles",
    "AssSubtitleSegment",
    "AssSubtitleWord",
    "WordStyleRange",
]
