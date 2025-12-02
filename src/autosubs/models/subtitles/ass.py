"""Models for representing the structure of an Advanced SubStation Alpha file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from autosubs.models.subtitles.base import Subtitles, SubtitleSegment, SubtitleWord


def _format_ass_tag_number(value: int | float) -> str:
    """Formats a number for an ASS tag, dropping .0 for whole numbers."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


@dataclass(frozen=True, eq=True)
class AssTagBlock:
    """Represents a block of ASS style override tags."""

    # Boolean styles
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikeout: bool | None = None
    # Layout and Alignment
    alignment: int | None = None
    position_x: int | float | None = None
    position_y: int | float | None = None
    origin_x: int | float | None = None
    origin_y: int | float | None = None
    # Font Properties
    font_name: str | None = None
    font_size: int | float | None = None
    # Colors and Alpha
    primary_color: str | None = None
    secondary_color: str | None = None
    outline_color: str | None = None
    shadow_color: str | None = None
    alpha: str | None = None
    # Spacing and Scaling
    spacing: int | float | None = None
    scale_x: int | float | None = None
    scale_y: int | float | None = None
    # Rotation
    rotation_x: int | float | None = None
    rotation_y: int | float | None = None
    rotation_z: int | float | None = None
    # Border, Shadow, and Blur
    border: int | float | None = None
    shadow: int | float | None = None
    blur: int | float | None = None
    # Complex transforms
    transforms: list[str] = field(default_factory=list)
    unknown_tags: list[str] = field(default_factory=list)

    def to_ass_string(self) -> str:
        """Serializes the tag block into a string for an ASS file."""
        tags = []
        # Layout and Alignment
        if self.alignment is not None:
            tags.append(f"\\an{self.alignment}")
        if self.position_x is not None and self.position_y is not None:
            tags.append(f"\\pos({_format_ass_tag_number(self.position_x)},{_format_ass_tag_number(self.position_y)})")
        if self.origin_x is not None and self.origin_y is not None:
            tags.append(f"\\org({_format_ass_tag_number(self.origin_x)},{_format_ass_tag_number(self.origin_y)})")

        # Font Properties
        if self.font_name:
            tags.append(f"\\fn{self.font_name}")
        if self.font_size is not None:
            tags.append(f"\\fs{_format_ass_tag_number(self.font_size)}")

        # Boolean Styles
        if self.bold is not None:
            tags.append(f"\\b{'1' if self.bold else '0'}")
        if self.italic is not None:
            tags.append(f"\\i{'1' if self.italic else '0'}")
        if self.underline is not None:
            tags.append(f"\\u{'1' if self.underline else '0'}")
        if self.strikeout is not None:
            tags.append(f"\\s{'1' if self.strikeout else '0'}")

        # Colors and Alpha
        if self.primary_color:
            tags.append(f"\\c{self.primary_color}")
        if self.secondary_color:
            tags.append(f"\\2c{self.secondary_color}")
        if self.outline_color:
            tags.append(f"\\3c{self.outline_color}")
        if self.shadow_color:
            tags.append(f"\\4c{self.shadow_color}")
        if self.alpha:
            tags.append(f"\\alpha{self.alpha}")

        # Spacing and Scaling
        if self.spacing is not None:
            tags.append(f"\\fsp{_format_ass_tag_number(self.spacing)}")
        if self.scale_x is not None:
            tags.append(f"\\fscx{_format_ass_tag_number(self.scale_x)}")
        if self.scale_y is not None:
            tags.append(f"\\fscy{_format_ass_tag_number(self.scale_y)}")

        # Rotation
        if self.rotation_z is not None:
            tags.append(f"\\frz{_format_ass_tag_number(self.rotation_z)}")
        if self.rotation_x is not None:
            tags.append(f"\\frx{_format_ass_tag_number(self.rotation_x)}")
        if self.rotation_y is not None:
            tags.append(f"\\fry{_format_ass_tag_number(self.rotation_y)}")

        # Border, Shadow, and Blur Effects
        if self.border is not None:
            tags.append(f"\\bord{_format_ass_tag_number(self.border)}")
        if self.shadow is not None:
            tags.append(f"\\shad{_format_ass_tag_number(self.shadow)}")
        if self.blur is not None:
            tags.append(f"\\blur{_format_ass_tag_number(self.blur)}")

        for transform in self.transforms:
            tags.append(f"\\t({transform})")

        for unknown in self.unknown_tags:
            tags.append(f"\\{unknown}")

        tag_str = "".join(tags)
        if not tag_str:
            return ""
        return f"{{{tag_str}}}"


@dataclass(frozen=True, eq=True)
class WordStyleRange:
    """Represents a style tag applied to a range of characters within a word."""

    start_char_index: int
    end_char_index: int
    tag_block: AssTagBlock

    @property
    def ass_tag(self) -> str:
        """Returns the ASS tag string representation of the tag block."""
        return self.tag_block.to_ass_string()


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
        return " ".join(word.text for word in self.words)


@dataclass(eq=True)
class AssSubtitles(Subtitles):
    """Represents a complete ASS file, including headers, styles, and events."""

    script_info: dict[str, str] = field(default_factory=dict)
    segments: list[AssSubtitleSegment] = field(default_factory=list)  # type: ignore[assignment]
    style_format_keys: list[str] = field(default_factory=list)
    events_format_keys: list[str] = field(default_factory=list)
