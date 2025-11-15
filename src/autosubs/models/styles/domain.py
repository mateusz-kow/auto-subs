"""Internal domain models for the style engine.

These models represent the validated, in-memory configuration used by the
StylerEngine to process and apply styles to subtitles. They are typically
created from the corresponding Pydantic schemas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from autosubs.models.styles.schemas import ExpressionOrNumber


@dataclass(frozen=True)
class Transform:
    """Domain model for a single animation or transformation effect."""

    start: float | None = None
    end: float | None = None
    accel: float | None = None
    ease: Literal["linear", "ease_in", "ease_out", "ease_in_out"] | None = None
    font_size: ExpressionOrNumber | None = None
    scale_x: ExpressionOrNumber | None = None
    scale_y: ExpressionOrNumber | None = None
    rotation_x: ExpressionOrNumber | None = None
    rotation_y: ExpressionOrNumber | None = None
    rotation_z: ExpressionOrNumber | None = None
    alpha: ExpressionOrNumber | None = None
    position_x: ExpressionOrNumber | None = None
    position_y: ExpressionOrNumber | None = None
    blur: ExpressionOrNumber | None = None
    border: ExpressionOrNumber | None = None
    shadow: ExpressionOrNumber | None = None
    move_x1: ExpressionOrNumber | None = None
    move_y1: ExpressionOrNumber | None = None
    move_x2: ExpressionOrNumber | None = None
    move_y2: ExpressionOrNumber | None = None
    move_t1: ExpressionOrNumber | None = None
    move_t2: ExpressionOrNumber | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    outline_color: str | None = None
    shadow_color: str | None = None


@dataclass(frozen=True)
class Clip:
    """Domain model for a vector clipping effect."""

    vector: str | None = None
    rect: (
        tuple[
            ExpressionOrNumber,
            ExpressionOrNumber,
            ExpressionOrNumber,
            ExpressionOrNumber,
        ]
        | None
    ) = None
    inverse: bool = False


@dataclass(frozen=True)
class StyleOverride:
    """Domain model for a set of style properties that can override a base style."""

    font_name: str | None = None
    font_size: ExpressionOrNumber | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikeout: bool | None = None
    spacing: ExpressionOrNumber | None = None
    angle: ExpressionOrNumber | None = None
    scale_x: ExpressionOrNumber | None = None
    scale_y: ExpressionOrNumber | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    outline_color: str | None = None
    shadow_color: str | None = None
    alpha: str | ExpressionOrNumber | None = None
    border: ExpressionOrNumber | None = None
    shadow: ExpressionOrNumber | None = None
    blur: ExpressionOrNumber | None = None
    position_x: ExpressionOrNumber | None = None
    position_y: ExpressionOrNumber | None = None
    move_x1: ExpressionOrNumber | None = None
    move_y1: ExpressionOrNumber | None = None
    move_x2: ExpressionOrNumber | None = None
    move_y2: ExpressionOrNumber | None = None
    move_t1: ExpressionOrNumber | None = None
    move_t2: ExpressionOrNumber | None = None
    rotation_x: ExpressionOrNumber | None = None
    rotation_y: ExpressionOrNumber | None = None
    rotation_z: ExpressionOrNumber | None = None
    origin_x: ExpressionOrNumber | None = None
    origin_y: ExpressionOrNumber | None = None
    karaoke: bool | None = None
    clip: Clip | None = None
    transforms: list[Transform] | None = None
    layer: int | None = None
    alignment: int | None = None
    tags: dict[str, Any] | None = None


@dataclass(frozen=True)
class Effect:
    """Domain model for a named, reusable effect."""

    name: str
    params: dict[str, Any] | None = None
    transforms: list[Transform] | None = None
    description: str | None = None


@dataclass(frozen=True)
class RuleOperator:
    """Domain model for a condition within a style rule."""

    target: Literal["char", "word", "syllable", "line"] = "char"
    index: int | None = None
    index_from: int | None = None
    index_to: int | None = None
    index_modulo: int | None = None
    is_first: bool | None = None
    is_last: bool | None = None
    chars: list[str] | None = None
    exclude_chars: list[str] | None = None
    regex: re.Pattern[str] | None = None
    exclude_regex: re.Pattern[str] | None = None
    time_from: float | None = None
    time_to: float | None = None
    negate: bool = False
    rules: list[StyleRule | RuleOperator] | None = None
    description: str | None = None


@dataclass(frozen=True)
class StyleRule:
    """Domain model for a rule that applies styles or effects based on conditions."""

    name: str | None = None
    priority: int = 0
    pattern: re.Pattern[str] | None = None
    apply_to: Literal["line", "word", "char", "syllable"] = "char"
    time_from: float | None = None
    time_to: float | None = None
    speaker: str | None = None
    layer: int | None = None
    style_name: str | None = None
    style_override: StyleOverride | None = None
    effect: str | None = None
    effect_params: dict[str, Any] | None = None
    transforms: list[Transform] | None = None
    regex: re.Pattern[str] | None = None
    exclude_regex: re.Pattern[str] | None = None
    operators: list[RuleOperator] | None = None


@dataclass(frozen=True)
class KaraokeSettings:
    """Domain model for karaoke-specific styling settings."""

    type: Literal["word-by-word", "syllable", "mora"] = "word-by-word"
    style_name: str | None = None
    highlight_style: StyleOverride | None = None
    transition: Transform | None = None


@dataclass(frozen=True)
class StylePreset:
    """Domain model for a named, reusable set of style overrides."""

    name: str
    override: StyleOverride


@dataclass(frozen=True)
class ScriptInfo:
    """Domain model for the [Script Info] section of an ASS file."""

    Title: str | None
    ScriptType: str | None
    WrapStyle: int | None
    ScaledBorderAndShadow: Literal["yes", "no"] | None
    Collisions: Literal["Normal", "Reverse", "Smart", "Force"] | None
    PlayResX: int | None
    PlayResY: int | None
    other: dict[str, Any] | None


@dataclass(frozen=True)
class StyleEngineConfig:
    """Domain model for the complete style engine configuration."""

    script_info: dict[str, Any] = field(default_factory=dict)
    styles: list[dict[str, Any]] = field(default_factory=list)
    presets: list[StylePreset] = field(default_factory=list)
    rules: list[StyleRule | RuleOperator] = field(default_factory=list)
    effects: dict[str, Effect] = field(default_factory=dict)
    karaoke: KaraokeSettings | None = None
    defaults: StyleOverride | None = None
    metadata: dict[str, Any] | None = None
