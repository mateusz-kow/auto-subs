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
    text_override: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Calculates start and end times after initialization."""
        if not self.words:
            raise ValueError("SubtitleSegment must contain at least one word.")
        self.words.sort(key=lambda w: w.start)
        self.start = self.words[0].start
        self.end = self.words[-1].end

    @property
    def text(self) -> str:
        """Returns the segment text.

        If `text_override` is set, it returns that value. Otherwise, it
        concatenates the words with spaces.
        """
        if self.text_override is not None:
            return self.text_override
        return " ".join(word.text for word in self.words)


@dataclass
class Subtitles:
    """Represents a collection of subtitle segments for a piece of media."""

    segments: list[SubtitleSegment]

    def __post_init__(self) -> None:
        """Sorts segments and checks for overlaps after initialization."""
        self.segments.sort(key=lambda s: s.start)
        for i in range(len(self.segments) - 1):
            current_seg = self.segments[i]
            next_seg = self.segments[i + 1]
            if current_seg.end > next_seg.start:
                logger.warning(
                    f"Overlap detected: Segment ending at {current_seg.end:.3f}s overlaps with "
                    f"segment starting at {next_seg.start:.3f}s."
                )

    @property
    def text(self) -> str:
        """Returns the segment text by concatenating the words."""
        return "\n".join(segment.text for segment in self.segments)
