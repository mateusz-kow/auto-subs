from pydantic import TypeAdapter

from autosubs.models.settings import AssSettings, AssStyleSettings
from autosubs.models.subtitles import (
    AssSubtitles,
    AssSubtitleSegment,
    AssSubtitleWord,
    Subtitles,
    SubtitleSegment,
    SubtitleWord,
    WordStyleRange,
)
from autosubs.models.transcription import TranscriptionModel

TRANSCRIPTION_ADAPTER: TypeAdapter[TranscriptionModel] = TypeAdapter(TranscriptionModel)

__all__ = [
    "SubtitleWord",
    "SubtitleSegment",
    "Subtitles",
    "AssSettings",
    "AssStyleSettings",
    "TranscriptionModel",
    "TRANSCRIPTION_ADAPTER",
    "AssSubtitles",
    "AssSubtitleSegment",
    "AssSubtitleWord",
    "WordStyleRange",
]
