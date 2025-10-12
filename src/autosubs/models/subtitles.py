from __future__ import annotations

import logging
from dataclasses import dataclass, field

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
        self.words.sort(key=lambda w: w.start)
        self.start = self.words[0].start
        self.end = self.words[-1].end

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

    @property
    def text(self) -> str:
        """Returns the segment text by concatenating the words."""
        return "\n".join(segment.text for segment in self.segments)
