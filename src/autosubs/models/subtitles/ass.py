"""Models for representing the structure of an Advanced SubStation Alpha file."""

from __future__ import annotations

from dataclasses import dataclass, field

from autosubs.models.subtitles.base import Subtitles, SubtitleSegment, SubtitleWord


@dataclass(frozen=True, eq=True)
class WordStyleRange:
    """Represents a style tag applied to a range of characters within a word."""

    start_char_index: int
    end_char_index: int
    ass_tag: str


@dataclass(eq=True)
class AssSubtitleWord(SubtitleWord):
    """Represents a single word in an ASS file, including rich styling."""

    styles: list[WordStyleRange] = field(default_factory=list, hash=False, repr=False)


@dataclass(eq=True)
class AssSubtitleSegment(SubtitleSegment):
    """Represents a Dialogue line in an ASS file, including all metadata."""

    words: list[AssSubtitleWord] = field(default_factory=list)  # type: ignore[assignment]
    layer: int = 0
    style_name: str = "Default"
    actor_name: str = ""
    margin_l: int = 0
    margin_r: int = 0
    margin_v: int = 0
    effect: str = ""

    @classmethod
    def from_generic(cls, segment: SubtitleSegment) -> AssSubtitleSegment:
        """Creates an AssSubtitleSegment from a generic SubtitleSegment."""
        ass_words = [AssSubtitleWord(text=w.text, start=w.start, end=w.end) for w in segment.words]
        return cls(words=ass_words)

    @property
    def text(self) -> str:
        """Returns the segment's plain text content, stripping all style tags."""
        if self.text_override is not None:
            return self.text_override
        return "".join(word.text for word in self.words)


@dataclass(eq=True)
class AssSubtitles(Subtitles):
    """Represents a complete ASS file, including headers, styles, and events."""

    script_info: dict[str, str] = field(default_factory=dict)
    segments: list[AssSubtitleSegment] = field(default_factory=list)  # type: ignore[assignment]
    style_format_keys: list[str] = field(default_factory=list)
    events_format_keys: list[str] = field(default_factory=list)
