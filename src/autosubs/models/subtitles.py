from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubtitleWord:
    """Represents a single word with its text and timing."""

    text: str
    start: float
    end: float

    def __post_init__(self) -> None:
        """Validates the word's timestamps after initialization."""
        if self.start > self.end:
            raise ValueError(f"SubtitleWord has invalid timestamp: start ({self.start}) > end ({self.end})")

    def to_dict(self) -> dict[str, Any]:
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

    def to_dict(self, segment_id: int) -> dict[str, Any]:
        """Converts the instance to a dictionary compatible with TranscriptionDict.

        Args:
            segment_id: The sequential ID to assign to this segment.

        Returns:
            A SegmentDict representing the segment.
        """
        return {
            "id": segment_id,
            "start": self.start,
            "end": self.end,
            "text": str(self),
            "words": [w.to_dict() for w in self.words],
        }

    @property
    def text(self) -> str:
        """Returns the segment text by concatenating the words."""
        return " ".join(word.text for word in self.words)


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

    def to_transcription_dict(self) -> dict[str, Any]:
        """Converts the subtitles object to a Whisper-compatible dictionary."""
        return {
            "text": str(self),
            "segments": [segment.to_dict(i) for i, segment in enumerate(self.segments)],
            "language": "unknown",  # Language info is lost during this conversion
        }

    def __str__(self) -> str:
        """Returns the full transcription as a single string."""
        return "\n".join(str(segment) for segment in self.segments)
