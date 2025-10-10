from typing import cast

from pydantic import BaseModel, Field

from auto_subs.typing.transcription import TranscriptionDict


class WordModel(BaseModel):
    """Pydantic model for a single word in a Whisper transcription.

    Ensures that each word object has the required fields and correct types.
    """

    word: str
    start: float
    end: float


class SegmentModel(BaseModel):
    """Pydantic model for a segment of a Whisper transcription.

    A segment typically represents a sentence or a continuous chunk of speech.
    """

    id: int
    start: float
    end: float
    text: str
    words: list[WordModel]
    # The following fields are often present but are not critical for subtitles.
    seek: int | None = None
    tokens: list[int] | None = None
    temperature: float | None = None
    avg_logprob: float | None = Field(None, alias="avg_logprob")
    compression_ratio: float | None = Field(None, alias="compression_ratio")
    no_speech_prob: float | None = Field(None, alias="no_speech_prob")


class TranscriptionModel(BaseModel):
    """Pydantic model for the entire Whisper transcription JSON output.

    This model serves as the primary validation layer for the raw input data,
    ensuring it conforms to the expected structure before any processing occurs.
    """

    text: str
    segments: list[SegmentModel]
    language: str

    def to_dict(self) -> TranscriptionDict:
        """Converts the Pydantic model back to a dictionary.

        This is useful for compatibility with functions that still expect dicts.

        Returns:
            The model's data as a dictionary.
        """
        return cast(TranscriptionDict, self.model_dump(by_alias=True))
