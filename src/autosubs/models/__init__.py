from pydantic import TypeAdapter

from autosubs.models.ass import AssSubtitles, AssSubtitleSegment, AssSubtitleWord
from autosubs.models.ass_styles import AssStyle, WordStyleRange
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
    "AssSubtitles",
    "AssSubtitleSegment",
    "AssStyle",
    "WordStyleRange",
    "AssSubtitleWord",
]
