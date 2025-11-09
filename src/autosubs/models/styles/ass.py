"""Models for representing ASS-specific styling information."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, eq=True)
class WordStyleRange:
    """Represents a style tag applied to a range of characters within a word."""

    start_char_index: int
    end_char_index: int
    ass_tag: str


class AssStyle(BaseModel):
    """Represents a single 'Style:' line in the [V4+ Styles] section."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="Name")
    font_name: str = Field("Arial", alias="Fontname")
    font_size: float = Field(48.0, alias="Fontsize")
    primary_color: str = Field("&H00FFFFFF", alias="PrimaryColour")
    secondary_color: str = Field("&H000000FF", alias="SecondaryColour")
    outline_color: str = Field("&H00000000", alias="OutlineColour")
    back_color: str = Field("&H00000000", alias="BackColour")
    bold: bool = Field(False, alias="Bold")
    italic: bool = Field(False, alias="Italic")
    underline: bool = Field(False, alias="Underline")
    strikeout: bool = Field(False, alias="StrikeOut")
    scale_x: float = Field(100.0, alias="ScaleX")
    scale_y: float = Field(100.0, alias="ScaleY")
    spacing: float = Field(0.0, alias="Spacing")
    angle: float = Field(0.0, alias="Angle")
    border_style: int = Field(1, alias="BorderStyle")
    outline: float = Field(2.0, alias="Outline")
    shadow: float = Field(1.0, alias="Shadow")
    alignment: int = Field(2, alias="Alignment")
    margin_l: int = Field(10, alias="MarginL")
    margin_r: int = Field(10, alias="MarginR")
    margin_v: int = Field(20, alias="MarginV")
    encoding: int = Field(1, alias="Encoding")
