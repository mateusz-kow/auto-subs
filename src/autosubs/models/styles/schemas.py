from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from autosubs.models.styles import domain


class StyleOverrideSchema(BaseModel):
    """Validation schema for style overrides."""

    font_name: str | None = None
    font_size: int | None = None
    primary_color: str | None = None
    bold: bool | None = None

    def to_domain(self) -> domain.StyleOverride:
        """Converts the schema to its domain model equivalent."""
        return domain.StyleOverride(**self.model_dump(exclude_none=True))


class StyleRuleSchema(BaseModel):
    """Validation schema for a single style rule."""

    name: str
    priority: int = 0
    pattern: str | None = None
    apply_to: Literal["word", "line"] = "word"
    time_from: float | None = None
    time_to: float | None = None
    style_name: str | None = None
    style_override: StyleOverrideSchema | None = None
    effect_name: str | None = Field(None, alias="effect")

    def to_domain(self) -> domain.StyleRule:
        """Converts the schema to its domain model equivalent."""
        return domain.StyleRule(
            name=self.name,
            priority=self.priority,
            pattern=self.pattern,
            apply_to=self.apply_to,
            time_from=self.time_from,
            time_to=self.time_to,
            style_name=self.style_name,
            style_override=(self.style_override.to_domain() if self.style_override else None),
            effect_name=self.effect_name,
        )


class KaraokeSettingsSchema(BaseModel):
    """Validation schema for karaoke settings."""

    type: Literal["word-by-word"] = "word-by-word"
    style_name: str | None = None

    def to_domain(self) -> domain.KaraokeSettings:
        """Converts the schema to its domain model equivalent."""
        return domain.KaraokeSettings(**self.model_dump(exclude_none=True))


class StyleEngineConfigSchema(BaseModel):
    """Validation schema for the complete style engine configuration."""

    script_info: dict[str, Any] = {
        "Title": "auto-subs generated subtitles",
        "ScriptType": "v4.00+",
        "WrapStyle": 0,
        "ScaledBorderAndShadow": "yes",
        "Collisions": "Normal",
        "PlayResX": 1920,
        "PlayResY": 1080,
    }
    styles: list[dict[str, Any]]
    rules: list[StyleRuleSchema]
    effects: dict[str, str] | None = {}
    karaoke: KaraokeSettingsSchema | None = None

    def to_domain(self) -> domain.StyleEngineConfig:
        """Converts the schema to its domain model equivalent."""
        return domain.StyleEngineConfig(
            script_info=self.script_info,
            styles=self.styles,
            rules=[rule.to_domain() for rule in self.rules],
            effects=self.effects or {},
            karaoke=self.karaoke.to_domain() if self.karaoke else None,
        )
