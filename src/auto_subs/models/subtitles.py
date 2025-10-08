from dataclasses import dataclass, field
from typing import Any

from auto_subs.core.word_segmenter import segment_words


@dataclass(eq=True)
class SubtitleWord:
    """Represents a single word with its text and timing."""

    text: str
    start: float
    end: float

    def __post_init__(self) -> None:
        """Strips whitespace from text after initialization."""
        self.text = self.text.strip()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubtitleWord":
        return cls(text=data["text"], start=data["start"], end=data["end"])


@dataclass(eq=True)
class SubtitleSegment:
    """Represents a segment of subtitles containing multiple words."""

    words: list[SubtitleWord] = field(default_factory=list)
    start: float = field(init=False, default=0.0)
    end: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        """Recalculates start and end times after the object is created."""
        self.refresh()

    def refresh(self) -> None:
        """Recalculates start and end times based on the words in the segment."""
        self.words.sort(key=lambda w: w.start)
        if self.words:
            self.start = self.words[0].start
            self.end = self.words[-1].end
        else:
            self.start = self.end = 0

    def __str__(self) -> str:
        """Return the segment as a string of concatenated word texts."""
        return " ".join(word.text for word in self.words)


@dataclass
class Subtitles:
    """Represents a collection of subtitle segments for a piece of media."""

    segments: list[SubtitleSegment] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.segments.sort(key=lambda s: s.start)

    @classmethod
    def from_transcription(cls, transcription: dict[str, Any], **kwargs) -> "Subtitles":
        """Creates a Subtitles instance from a transcription dictionary.

        Args:
            transcription: The transcription data from a speech-to-text model.
            **kwargs: Additional arguments to pass to the word segmenter
                      (e.g., max_chars).
        """
        dict_segments = segment_words(transcription, **kwargs)
        segments = [
            SubtitleSegment([SubtitleWord.from_dict(w) for w in dict_segment["words"]])
            for dict_segment in dict_segments
        ]
        return cls(segments)

    def __str__(self) -> str:
        """Return the full transcription as a single string."""
        return "\n".join(str(segment) for segment in self.segments)
