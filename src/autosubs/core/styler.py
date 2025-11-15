from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autosubs.models.styles.domain import RuleOperator, StyleOverride, Transform

if TYPE_CHECKING:
    from autosubs.models.styles.domain import StyleEngineConfig, StyleRule
    from autosubs.models.subtitles import SubtitleSegment


@dataclass
class CharContext:
    """Holds the contextual information for a single character in a segment."""

    char: str
    char_index_line: int
    char_index_word: int
    word_index_line: int
    word_text: str
    word_start: float
    word_end: float
    line_start: float
    line_end: float
    is_first_word: bool
    is_last_word: bool
    is_first_char: bool
    is_last_char: bool


@dataclass
class AppliedStyles:
    """Represents the final, combined style properties for a character."""

    style_override: StyleOverride | None = None
    transforms: list[Transform] = field(default_factory=list)
    raw_prefix: str = ""
    raw_suffix: str = ""

    def to_ass_tags(self, context: CharContext) -> str:
        """Converts the applied styles into an ASS tag block."""
        tags = []
        if self.style_override:
            # Layout and Alignment
            if self.style_override.alignment is not None:
                tags.append(f"\\an{self.style_override.alignment}")
            if self.style_override.position_x is not None and self.style_override.position_y is not None:
                tags.append(f"\\pos({self.style_override.position_x},{self.style_override.position_y})")
            if self.style_override.origin_x is not None and self.style_override.origin_y is not None:
                tags.append(f"\\org({self.style_override.origin_x},{self.style_override.origin_y})")

            # Font Properties
            if self.style_override.font_name:
                tags.append(f"\\fn{self.style_override.font_name}")
            if self.style_override.font_size is not None:
                tags.append(f"\\fs{int(self.style_override.font_size)}")

            # Boolean Styles
            if self.style_override.bold is not None:
                tags.append(f"\\b{'1' if self.style_override.bold else '0'}")
            if self.style_override.italic is not None:
                tags.append(f"\\i{'1' if self.style_override.italic else '0'}")
            if self.style_override.underline is not None:
                tags.append(f"\\u{'1' if self.style_override.underline else '0'}")
            if self.style_override.strikeout is not None:
                tags.append(f"\\s{'1' if self.style_override.strikeout else '0'}")

            # Colors and Alpha
            if self.style_override.primary_color:
                tags.append(f"\\c{self.style_override.primary_color}")
            if self.style_override.secondary_color:
                tags.append(f"\\2c{self.style_override.secondary_color}")
            if self.style_override.outline_color:
                tags.append(f"\\3c{self.style_override.outline_color}")
            if self.style_override.shadow_color:
                tags.append(f"\\4c{self.style_override.shadow_color}")
            if self.style_override.alpha:
                tags.append(f"\\alpha{self.style_override.alpha}")

            # Spacing and Scaling
            if self.style_override.spacing is not None:
                tags.append(f"\\fsp{self.style_override.spacing}")
            if self.style_override.scale_x is not None:
                tags.append(f"\\fscx{self.style_override.scale_x}")
            if self.style_override.scale_y is not None:
                tags.append(f"\\fscy{self.style_override.scale_y}")

            # Rotation (prioritizing 'angle' for z-axis)
            angle = (
                self.style_override.angle if self.style_override.angle is not None else self.style_override.rotation_z
            )
            if angle is not None:
                tags.append(f"\\frz{angle}")
            if self.style_override.rotation_x is not None:
                tags.append(f"\\frx{self.style_override.rotation_x}")
            if self.style_override.rotation_y is not None:
                tags.append(f"\\fry{self.style_override.rotation_y}")

            # Border, Shadow, and Blur Effects
            if self.style_override.border is not None:
                tags.append(f"\\bord{self.style_override.border}")
            if self.style_override.shadow is not None:
                tags.append(f"\\shad{self.style_override.shadow}")
            if self.style_override.blur is not None:
                tags.append(f"\\blur{self.style_override.blur}")

        for transform in self.transforms:
            parts = []
            if transform.start is not None and transform.end is not None:
                parts.append(str(int(transform.start)))
                parts.append(str(int(transform.end)))
            elif transform.end is not None:
                parts.append(f"0,{int(transform.end)}")

            if transform.accel is not None:
                parts.append(str(transform.accel))

            transform_tags = []
            if transform.scale_x is not None or transform.scale_y is not None:
                sx = transform.scale_x or 100
                sy = transform.scale_y or 100
                transform_tags.append(f"\\fscx{sx}\\fscy{sy}")
            if transform.primary_color:
                transform_tags.append(f"\\1c{transform.primary_color}")
            if transform.secondary_color:
                transform_tags.append(f"\\2c{transform.secondary_color}")
            if transform.outline_color:
                transform_tags.append(f"\\3c{transform.outline_color}")
            if transform.shadow_color:
                transform_tags.append(f"\\4c{transform.shadow_color}")

            if transform_tags:
                parts.append("".join(transform_tags))
                tags.append(f"\\t({','.join(parts)})")

        tag_str = "".join(tags)
        if not tag_str:
            return ""
        return f"{{{self.raw_prefix}{tag_str}{self.raw_suffix}}}"


class StylerEngine:
    """Applies advanced, rule-based styling to subtitle segments."""

    def __init__(self, config: StyleEngineConfig):
        """Initializes the engine with a validated style configuration."""
        self.config = config
        self.sorted_rules = sorted(config.rules, key=lambda r: r.priority, reverse=True)  # type: ignore[union-attr] # TODO: Remove it
        # Initialize state attributes to prevent errors and state leakage.
        self.last_line_check_result: bool = False
        self.last_word_check_result: bool = False

    def _get_char_contexts(self, segment: SubtitleSegment) -> list[CharContext]:
        """Generates a context object for each character in the segment."""
        contexts = []
        char_index_line = 0
        for word_i, word in enumerate(segment.words):
            for char_i, char in enumerate(word.text):
                contexts.append(
                    CharContext(
                        char=char,
                        char_index_line=char_index_line,
                        char_index_word=char_i,
                        word_index_line=word_i,
                        word_text=word.text,
                        word_start=word.start,
                        word_end=word.end,
                        line_start=segment.start,
                        line_end=segment.end,
                        is_first_word=(word_i == 0),
                        is_last_word=(word_i == len(segment.words) - 1),
                        is_first_char=(char_i == 0),
                        is_last_char=(char_i == len(word.text) - 1),
                    )
                )
                char_index_line += 1
        return contexts

    def _check_operator(self, op: RuleOperator, context: CharContext, line_text: str) -> bool:
        """Evaluates a single rule operator against a character's context."""
        match = True
        target_text, target_index, target_is_first, target_is_last = "", 0, False, False

        if op.target == "line":
            target_text, target_index, target_is_first, target_is_last = line_text, 0, True, True
        elif op.target == "word":
            target_text, target_index, target_is_first, target_is_last = (
                context.word_text,
                context.word_index_line,
                context.is_first_word,
                context.is_last_word,
            )
        elif op.target == "char":
            target_text, target_index, target_is_first, target_is_last = (
                context.char,
                context.char_index_word,
                context.is_first_char,
                context.is_last_char,
            )

        if op.index is not None and target_index != op.index:
            match = False
        if op.index_from is not None and target_index < op.index_from:
            match = False
        if op.index_to is not None and target_index > op.index_to:
            match = False
        if op.is_first is not None and target_is_first != op.is_first:
            match = False
        if op.is_last is not None and target_is_last != op.is_last:
            match = False
        if op.regex and not op.regex.search(target_text):
            match = False
        if op.rules:
            match = any(self._rule_matches_char(rule, context, line_text) for rule in op.rules)

        return match if not op.negate else not match

    def _rule_matches_char(self, rule: StyleRule | RuleOperator, context: CharContext, line_text: str) -> bool:
        """Checks if a rule or operator matches a character's context."""
        if isinstance(rule, RuleOperator):
            return self._check_operator(rule, context, line_text)

        has_char_operator = any(op.target == "char" for op in rule.operators or [])

        if rule.apply_to == "line" and context.char_index_line > 0:
            return self.last_line_check_result
        if rule.apply_to == "word" and context.char_index_word > 0 and not has_char_operator:
            return self.last_word_check_result

        check_text = ""
        if rule.apply_to == "line":
            check_text = line_text
        elif rule.apply_to in {"word", "char", "syllable"}:
            check_text = context.word_text

        match = True
        if rule.regex and not rule.regex.search(check_text):
            match = False
        if match and rule.operators:
            match = all(self._check_operator(op, context, line_text) for op in rule.operators)

        if not has_char_operator:
            if rule.apply_to == "line":
                self.last_line_check_result = match
            if rule.apply_to == "word":
                self.last_word_check_result = match
        return match

    def _get_styles_for_char(self, context: CharContext, line_text: str) -> AppliedStyles:
        """Finds the highest-priority matching rule and returns its styles."""
        for rule in self.sorted_rules:
            if self._rule_matches_char(rule, context, line_text):
                style_override = rule.style_override  # type: ignore[union-attr] # TODO: Remove it
                transforms = rule.transforms or []  # type: ignore[union-attr] # TODO: Remove it

                raw_prefix = ""
                if style_override and style_override.tags and "raw_prefix" in style_override.tags:
                    raw_prefix = style_override.tags["raw_prefix"]

                # If operators provided transforms, merge them
                if rule.operators:  # type: ignore[union-attr] # TODO: Remove it
                    for op in rule.operators:  # type: ignore[union-attr] # TODO: Remove it
                        if self._check_operator(op, context, line_text) and hasattr(op, "transforms"):
                            transforms.extend(op.transforms or [])

                return AppliedStyles(style_override, transforms, raw_prefix)
        return AppliedStyles()

    def process_segment(self, segment: SubtitleSegment, default_style_name: str) -> tuple[str, str]:
        """Processes a segment and returns a tuple of (style_name, dialogue_text)."""
        self.last_line_check_result = False
        self.last_word_check_result = False

        if not segment.words:
            return default_style_name, ""

        line_text = " ".join(w.text for w in segment.words)
        char_contexts = self._get_char_contexts(segment)

        style_name = default_style_name
        for rule in self.sorted_rules:
            if rule.apply_to == "line" and self._rule_matches_char(rule, char_contexts[0], line_text):  # type: ignore[union-attr] # TODO: Remove it
                if rule.style_name:  # type: ignore[union-attr] # TODO: Remove it
                    style_name = rule.style_name  # type: ignore[union-attr] # TODO: Remove it
                break

        word_strings = []
        for i in range(len(segment.words)):
            word_contexts = [c for c in char_contexts if c.word_index_line == i]
            if not word_contexts:
                continue

            word_parts = []
            last_tags = ""
            for context in word_contexts:
                styles = self._get_styles_for_char(context, line_text)
                current_tags = styles.to_ass_tags(context)

                if current_tags != last_tags:
                    if last_tags:
                        word_parts.append(r"{\r}")
                    word_parts.append(current_tags)
                    last_tags = current_tags

                word_parts.append(context.char)

            if last_tags:
                word_parts.append(r"{\r}")

            word_strings.append("".join(word_parts))

        return style_name, " ".join(word_strings)
