from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from autosubs.models import AssSubtitleSegment, AssSubtitleWord, WordStyleRange

if TYPE_CHECKING:
    from autosubs.models.styles.domain import StyleEngineConfig, StyleOverride, StyleRule
    from autosubs.models.subtitles import SubtitleSegment


class StylerEngine:
    """Applies advanced, rule-based styling to subtitle segments."""

    def __init__(self, config: StyleEngineConfig):
        """Initializes the engine with a validated style configuration."""
        self.config = config
        self.line_rules: list[dict[str, Any]] = []
        self.word_rules: list[dict[str, Any]] = []

        for rule in sorted(config.rules, key=lambda r: r.priority, reverse=True):
            compiled_rule = {
                "rule": rule,
                "pattern": re.compile(rule.pattern) if rule.pattern else None,
            }
            if rule.apply_to == "line":
                self.line_rules.append(compiled_rule)
            else:
                self.word_rules.append(compiled_rule)

    def _convert_override_to_tags(self, override: StyleOverride) -> tuple[list[str], list[str]]:
        start_tags: list[str] = []
        end_tags: list[str] = []

        if override.primary_color:
            start_tags.append(f"\\c{override.primary_color}")
            end_tags.append("\\c")
        if override.font_name:
            start_tags.append(f"\\fn{override.font_name}")
        if override.font_size:
            start_tags.append(f"\\fs{override.font_size}")
        if override.bold is not None:
            start_tags.append(f"\\b{'1' if override.bold else '0'}")
            end_tags.append(f"\\b{'0' if override.bold else '1'}")

        return [f"{{{tag}}}" for tag in start_tags if tag], [f"{{{tag}}}" for tag in reversed(end_tags) if tag]

    def _rule_matches(self, rule_def: StyleRule, text: str, start_time: float) -> bool:
        if rule_def.time_from and start_time < rule_def.time_from:
            return False
        if rule_def.time_to and start_time >= rule_def.time_to:
            return False
        return not (rule_def.pattern and not re.search(rule_def.pattern, text))

    def _apply_word_rules_to_word(self, word: AssSubtitleWord) -> None:
        for compiled_rule in self.word_rules:
            rule_def: StyleRule = compiled_rule["rule"]
            if self._rule_matches(rule_def, word.text, word.start):
                if rule_def.effect_name and self.config.effects:
                    effect_tag = self.config.effects.get(rule_def.effect_name)
                    if effect_tag:
                        word.styles.append(WordStyleRange(0, len(word.text), effect_tag))

                if rule_def.style_override:
                    start_tags, end_tags = self._convert_override_to_tags(rule_def.style_override)
                    for tag in start_tags:
                        word.styles.append(WordStyleRange(0, 0, tag))
                    for tag in end_tags:
                        word.styles.append(WordStyleRange(len(word.text), len(word.text), tag))

    def _apply_karaoke_to_words(self, words: list[AssSubtitleWord]) -> None:
        for word in words:
            duration_cs = int(round((word.end - word.start) * 100))
            existing_tags = "".join(style.ass_tag for style in word.styles)
            word.styles = [WordStyleRange(0, len(word.text), f"{{\\k{duration_cs}}}{existing_tags}")]

    def process_segment(self, segment: SubtitleSegment, default_style_name: str) -> AssSubtitleSegment:
        """Processes a segment, applying all configured rules and modes."""
        styled_segment = AssSubtitleSegment.from_generic(segment)
        styled_segment.style_name = default_style_name

        for compiled_rule in self.line_rules:
            rule_def: StyleRule = compiled_rule["rule"]
            if self._rule_matches(rule_def, styled_segment.text, styled_segment.start):
                if rule_def.style_name:
                    styled_segment.style_name = rule_def.style_name
                break

        for word in styled_segment.words:
            self._apply_word_rules_to_word(word)

        if self.config.karaoke:
            if self.config.karaoke.style_name:
                styled_segment.style_name = self.config.karaoke.style_name
            self._apply_karaoke_to_words(styled_segment.words)

        return styled_segment
