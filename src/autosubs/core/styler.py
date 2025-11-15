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

        # Sort rules once by priority for efficient processing later.
        sorted_rules = sorted(config.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            compiled_rule = {
                "rule": rule,
                "pattern": (re.compile(rule.pattern) if hasattr(rule, "pattern") and rule.pattern else None),
            }
            if rule.apply_to == "line":
                self.line_rules.append(compiled_rule)
            else:
                self.word_rules.append(compiled_rule)

    def _rule_matches(self, rule_def: StyleRule, text: str, start_time: float) -> bool:
        """Checks if a rule's conditions match the given context.

        Note: This is a simplified implementation for backward compatibility.
        A full implementation would evaluate the `operators` field.
        """
        # Time-based matching
        if rule_def.time_from is not None and start_time < rule_def.time_from:
            return False
        if rule_def.time_to is not None and start_time >= rule_def.time_to:
            return False

        # Pattern-based matching (legacy)
        if rule_def.pattern and not re.search(rule_def.pattern, text):
            return False

        # Regex-based matching (new)
        return not (hasattr(rule_def, "regex") and rule_def.regex and not re.search(rule_def.regex, text))

    def process_segment(self, segment: SubtitleSegment, default_style_name: str) -> tuple[str, str]:
        """Processes a segment and returns a tuple of (style_name, dialogue_text)."""
        style_name = default_style_name
        for compiled_rule in self.line_rules:
            rule_def: StyleRule = compiled_rule["rule"]
            if self._rule_matches(rule_def, segment.text, segment.start):
                if rule_def.style_name:
                    style_name = rule_def.style_name
                # Note: Overrides/effects on 'line' rules are not yet applied in this version.
                break

        dialogue_parts = []
        for word in segment.words:
            effect_tag = ""
            # Find the highest priority rule that matches this word
            for compiled_rule in self.word_rules:
                rule_def: StyleRule = compiled_rule["rule"]
                if self._rule_matches(rule_def, word.text, word.start):
                    effect_name = rule_def.effect
                    if effect_name and effect_name in self.config.effects:
                        # This is a placeholder for a much more complex effect-building system.
                        # For now, we assume effects are simple templates, which is incorrect
                        # based on the new domain models but maintains prior behavior.
                        # A full implementation would build tags from the Effect and Transform models.
                        effect_tag = f"\\{effect_name}"  # Simplified representation
                    break  # Apply only the first (highest priority) matching rule

            dialogue_parts.append(f"{effect_tag}{word.text}")

        dialogue_text = " ".join(dialogue_parts)
        return style_name, dialogue_text
