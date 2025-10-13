from pydantic import TypeAdapter

from autosubs.models.settings import AssSettings, AssStyleSettings
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord
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
]
