"""Models for representing the structure of an Advanced SubStation Alpha file."""

from __future__ import annotations

from collections.abc import Callable
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
    fade: tuple[int, int] | None = None
    # Complex transforms
    transforms: tuple[str, ...] = field(default_factory=tuple)
    unknown_tags: tuple[str, ...] = field(default_factory=tuple)

    def to_ass_string(self) -> str:
        """Serializes the tag block into a string for an ASS file."""
        tags = []

        def _append_paired(tag: str, x_attr: str, y_attr: str) -> None:
            x, y = getattr(self, x_attr, None), getattr(self, y_attr, None)
            if x is not None and y is not None:
                tags.append(f"\\{tag}({_format_ass_tag_number(x)},{_format_ass_tag_number(y)})")

        tag_descriptors: list[tuple[str, str, Callable[[Any], str] | None]] = [
            # (attribute_name, tag_name, formatter)
            ("alignment", "an", None),
            ("font_name", "fn", None),
            ("font_size", "fs", _format_ass_tag_number),
            ("bold", "b", lambda v: "1" if v else "0"),
            ("italic", "i", lambda v: "1" if v else "0"),
            ("underline", "u", lambda v: "1" if v else "0"),
            ("strikeout", "s", lambda v: "1" if v else "0"),
            ("primary_color", "c", None),
            ("secondary_color", "2c", None),
            ("outline_color", "3c", None),
            ("shadow_color", "4c", None),
            ("alpha", "alpha", None),
            ("spacing", "fsp", _format_ass_tag_number),
            ("scale_x", "fscx", _format_ass_tag_number),
            ("scale_y", "fscy", _format_ass_tag_number),
            ("rotation_z", "frz", _format_ass_tag_number),
            ("rotation_x", "frx", _format_ass_tag_number),
            ("rotation_y", "fry", _format_ass_tag_number),
            ("border", "bord", _format_ass_tag_number),
            ("shadow", "shad", _format_ass_tag_number),
            ("blur", "blur", _format_ass_tag_number),
        ]
        string_attrs = {"font_name", "primary_color", "secondary_color", "outline_color", "shadow_color", "alpha"}

        _append_paired("pos", "position_x", "position_y")
        _append_paired("org", "origin_x", "origin_y")

        for attr, tag, formatter in tag_descriptors:
            value = getattr(self, attr)

            # For string attributes, check truthiness; for others, check if not None
            should_include = bool(value) if attr in string_attrs else value is not None
            if should_include:
                formatted = formatter(value) if formatter else value
                tags.append(f"\\{tag}{formatted}")

        if self.fade is not None:
            tags.append(f"\\fad({self.fade[0]},{self.fade[1]})")

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
