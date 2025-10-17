"""Models for representing the structure of an Advanced SubStation Alpha file."""

from __future__ import annotations

from dataclasses import dataclass, field

from autosubs.models.styles.ass import AssStyle, WordStyleRange
from autosubs.models.subtitles.base import Subtitles, SubtitleSegment, SubtitleWord


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

    @property
    def text(self) -> str:
        """Returns the segment's plain text content, stripping all style tags.

        If `text_override` is set, it returns that value. Otherwise, it
        concatenates the text of its constituent words.
        """
        if self.text_override is not None:
            return self.text_override
        # In an ASS context, parsed words already contain necessary whitespace.
        return "".join(word.text for word in self.words)


@dataclass(eq=True)
class AssSubtitles(Subtitles):
    """Represents a complete ASS file, including headers, styles, and events."""

    script_info: dict[str, str] = field(default_factory=dict)
    styles: list[AssStyle] = field(default_factory=list)
    segments: list[AssSubtitleSegment] = field(default_factory=list)  # type: ignore[assignment]
    style_format_keys: list[str] = field(default_factory=list)
    events_format_keys: list[str] = field(default_factory=list)
