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
    move_x1: int | float | None = None
    move_y1: int | float | None = None
    move_x2: int | float | None = None
    move_y2: int | float | None = None
    move_t1: int | None = None
    move_t2: int | None = None
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

        # Handle \move tag with optional time parameters
        if (
            self.move_x1 is not None
            and self.move_y1 is not None
            and self.move_x2 is not None
            and self.move_y2 is not None
        ):
            move_parts = [
                _format_ass_tag_number(self.move_x1),
                _format_ass_tag_number(self.move_y1),
                _format_ass_tag_number(self.move_x2),
                _format_ass_tag_number(self.move_y2),
            ]
            if self.move_t1 is not None and self.move_t2 is not None:
                move_parts.extend([str(self.move_t1), str(self.move_t2)])
            tags.append(f"\\move({','.join(move_parts)})")

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

    def scale(self, scale_x: float, scale_y: float) -> AssTagBlock:
        """Returns a new AssTagBlock with scaled coordinate and size values."""
        return AssTagBlock(
            # Boolean styles - unchanged
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            strikeout=self.strikeout,
            # Layout and Alignment - scale coordinates
            alignment=self.alignment,
            position_x=self.position_x * scale_x if self.position_x is not None else None,
            position_y=self.position_y * scale_y if self.position_y is not None else None,
            origin_x=self.origin_x * scale_x if self.origin_x is not None else None,
            origin_y=self.origin_y * scale_y if self.origin_y is not None else None,
            move_x1=self.move_x1 * scale_x if self.move_x1 is not None else None,
            move_y1=self.move_y1 * scale_y if self.move_y1 is not None else None,
            move_x2=self.move_x2 * scale_x if self.move_x2 is not None else None,
            move_y2=self.move_y2 * scale_y if self.move_y2 is not None else None,
            move_t1=self.move_t1,
            move_t2=self.move_t2,
            # Font Properties - scale font size
            font_name=self.font_name,
            font_size=self.font_size * scale_y if self.font_size is not None else None,
            # Colors and Alpha - unchanged
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            outline_color=self.outline_color,
            shadow_color=self.shadow_color,
            alpha=self.alpha,
            # Spacing and Scaling - unchanged (these are percentages, not absolute)
            spacing=self.spacing,
            scale_x=self.scale_x,
            scale_y=self.scale_y,
            # Rotation - unchanged
            rotation_x=self.rotation_x,
            rotation_y=self.rotation_y,
            rotation_z=self.rotation_z,
            # Border, Shadow, and Blur - scale by Y factor
            border=self.border * scale_y if self.border is not None else None,
            shadow=self.shadow * scale_y if self.shadow is not None else None,
            blur=self.blur * scale_y if self.blur is not None else None,
            fade=self.fade,
            # Complex transforms - unchanged (would need complex parsing)
            transforms=self.transforms,
            unknown_tags=self.unknown_tags,
        )


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

    def resample_resolution(self, target_x: int, target_y: int) -> None:
        """Resample subtitle coordinates and sizes to match a new resolution.

        Args:
            target_x: Target horizontal resolution (PlayResX).
            target_y: Target vertical resolution (PlayResY).

        Raises:
            ValueError: If PlayResX or PlayResY are not set in script_info.
        """
        # Get current resolution from script_info
        current_x_str = self.script_info.get("PlayResX")
        current_y_str = self.script_info.get("PlayResY")

        if not current_x_str or not current_y_str:
            raise ValueError("PlayResX and PlayResY must be set in script_info to resample resolution")

        try:
            current_x = int(current_x_str)
            current_y = int(current_y_str)
        except ValueError as e:
            raise ValueError(f"Invalid PlayResX or PlayResY value: {e}") from e

        # Calculate scale factors
        scale_x = target_x / current_x
        scale_y = target_y / current_y

        # Update script_info
        self.script_info["PlayResX"] = str(target_x)
        self.script_info["PlayResY"] = str(target_y)

        # Scale all segments
        for segment in self.segments:
            # Scale margins
            segment.margin_l = int(segment.margin_l * scale_x)
            segment.margin_r = int(segment.margin_r * scale_x)
            segment.margin_v = int(segment.margin_v * scale_y)

            # Scale all word styles
            for word in segment.words:
                for i, style_range in enumerate(word.styles):
                    scaled_tag_block = style_range.tag_block.scale(scale_x, scale_y)
                    word.styles[i] = WordStyleRange(
                        start_char_index=style_range.start_char_index,
                        end_char_index=style_range.end_char_index,
                        tag_block=scaled_tag_block,
                    )

