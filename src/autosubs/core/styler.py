from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from autosubs.models.styles.domain import StyleEngineConfig, StyleRule
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

    def _rule_matches(self, rule_def: StyleRule, text: str, start_time: float) -> bool:
        return not (rule_def.pattern and not re.search(rule_def.pattern, text))

    def process_segment(self, segment: SubtitleSegment, default_style_name: str) -> tuple[str, str]:
        """Processes a segment and returns a tuple of (style_name, dialogue_text)."""
        style_name = default_style_name
        for compiled_rule in self.line_rules:
            rule_def: StyleRule = compiled_rule["rule"]
            if self._rule_matches(rule_def, segment.text, segment.start):
                if rule_def.style_name:
                    style_name = rule_def.style_name
                break

        dialogue_parts = []
        for word in segment.words:
            effect_tag = ""
            # Find the highest priority rule that matches this word
            for compiled_rule in self.word_rules:
                rule_def: StyleRule = compiled_rule["rule"]
                if self._rule_matches(rule_def, word.text, word.start):
                    effect_name = rule_def.effect_name
                    if effect_name and self.config.effects:
                        effect_tag = self.config.effects.get(effect_name, "")
                    break  # Apply only the first (highest priority) matching rule

            # Replace placeholders
            duration_ms = (word.end - word.start) * 1000
            duration_cs = duration_ms / 10
            effect_tag = effect_tag.replace("<duration_ms>", str(int(round(duration_ms))))
            effect_tag = effect_tag.replace("<duration_cs>", str(int(round(duration_cs))))

            dialogue_parts.append(f"{effect_tag}{word.text}")

        dialogue_text = " ".join(dialogue_parts)
        return style_name, dialogue_text
