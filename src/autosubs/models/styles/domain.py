from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, eq=True)
class WordStyleRange:
    """Represents a style tag applied to a range of characters within a word."""

    start_char_index: int
    end_char_index: int
    ass_tag: str


@dataclass(frozen=True)
class StyleOverride:
    """Represents a set of overrides for a base style."""

    font_name: str | None = None
    font_size: int | None = None
    primary_color: str | None = None
    bold: bool | None = None


@dataclass(frozen=True)
class StyleRule:
    """Defines a rule for applying styles or effects."""

    name: str
    priority: int = 0

    pattern: str | None = None
    apply_to: Literal["word", "line"] = "word"
    time_from: float | None = None
    time_to: float | None = None

    style_name: str | None = None
    style_override: StyleOverride | None = None
    effect_name: str | None = None


@dataclass(frozen=True)
class KaraokeSettings:
    """Defines how karaoke timing tags should be applied."""

    type: Literal["word-by-word"] = "word-by-word"
    style_name: str | None = None


@dataclass(frozen=True)
class StyleEngineConfig:
    """Domain model for the complete style engine configuration."""

    script_info: dict[str, Any]
    styles: list[dict[str, Any]]
    rules: list[StyleRule]
    effects: dict[str, str]
    karaoke: KaraokeSettings | None = None
