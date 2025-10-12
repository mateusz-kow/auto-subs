from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from autosubs.core.word_segmenter import segment_words
from autosubs.models.transcription import TranscriptionModel
from autosubs.typing.transcription import TranscriptionDict, WordDict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubtitleWord:
    """Represents a single word with its text and timing."""

    text: str
    start: float
    end: float

    def __post_init__(self) -> None:
        """Validates the timestamps after initialization."""
        if self.start > self.end:
            raise ValueError(f"SubtitleWord has invalid timestamp: start ({self.start}) > end ({self.end})")

    @classmethod
    def from_dict(cls, data: WordDict) -> SubtitleWord:
        """Creates a SubtitleWord instance from a dictionary.

        Args:
            data: A dictionary with 'word', 'start', and 'end' keys.

        Returns:
            A new SubtitleWord instance.
        """
        return cls(text=data["word"].strip(), start=data["start"], end=data["end"])

    def to_dict(self) -> WordDict:
        """Converts the instance to a dictionary."""
        return {"word": self.text, "start": self.start, "end": self.end}


@dataclass
class SubtitleSegment:
    """Represents a segment of subtitles containing one or more words."""

    words: list[SubtitleWord]
    start: float = field(init=False)
    end: float = field(init=False)

    def __post_init__(self) -> None:
        """Calculates start and end times after initialization."""
        if not self.words:
            raise ValueError("SubtitleSegment must contain at least one word.")
        self.start = self.words[0].start
        self.end = self.words[-1].end
        if self.start >= self.end:
            raise ValueError(f"SubtitleSegment has invalid timestamp: start ({self.start}) >= end ({self.end})")

    def __str__(self) -> str:
        """Returns the segment as a string of concatenated word texts."""
        return " ".join(word.text for word in self.words)

    def to_dict(self) -> dict[str, Any]:
        """Converts the instance to a dictionary."""
        return {"start": self.start, "end": self.end, "text": str(self), "words": [w.to_dict() for w in self.words]}


@dataclass
class Subtitles:
    """Represents a collection of subtitle segments for a piece of media."""

    segments: list[SubtitleSegment]

    def __post_init__(self) -> None:
        """Sorts segments and checks for overlaps after initialization."""
        self.segments.sort(key=lambda s: s.start)
        for i in range(len(self.segments) - 1):
            if self.segments[i].end > self.segments[i + 1].start:
                logger.warning(
                    f"Overlapping subtitle segments detected: "
                    f"Segment {i} ends at {self.segments[i].end}, "
                    f"but segment {i + 1} starts at {self.segments[i + 1].start}."
                )

    @classmethod
    def from_dict(cls, transcription_dict: dict[str, Any], **kwargs: Any) -> Subtitles:
        """Creates a Subtitles instance from a transcription dictionary.

        Args:
            transcription_dict: The raw transcription dictionary.
            **kwargs: Additional arguments for the word segmenter (e.g., max_chars).

        Returns:
            A new Subtitles instance.

        Raises:
            ValueError: If the transcription data fails validation.
        """
        try:
            transcription = TranscriptionModel.model_validate(transcription_dict)
        except ValidationError as e:
            raise ValueError("Transcription data failed validation.") from e

        dict_segments = segment_words(transcription.to_dict(), **kwargs)
        segments: list[SubtitleSegment] = []
        for dict_segment in dict_segments:
            words = [SubtitleWord.from_dict(w) for w in dict_segment.get("words", [])]
            if words:
                segments.append(SubtitleSegment(words))
        return cls(segments)

    def to_transcription_dict(self) -> TranscriptionDict:
        """Converts the subtitles object to a Whisper-compatible dictionary."""
        segments_as_dicts = []
        for i, segment in enumerate(self.segments):
            seg_dict = segment.to_dict()
            seg_dict["id"] = i
            segments_as_dicts.append(seg_dict)

        return {
            "text": str(self),
            "segments": segments_as_dicts,
            "language": "unknown",  # Language info is lost during this conversion
        }

    def __str__(self) -> str:
        """Returns the full transcription as a single string."""
        return "\n".join(str(segment) for segment in self.segments)
