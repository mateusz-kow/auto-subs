import re
from unittest.mock import MagicMock

import pytest

from autosubs.core.styler import AppliedStyles, StylerEngine
from autosubs.models.styles.domain import (
    RuleOperator,
    StyleEngineConfig,
    StyleOverride,
    StyleRule,
    Transform,
)
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_segment() -> SubtitleSegment:
    """Provides a sample SubtitleSegment for testing the styler."""
    words = [
        SubtitleWord("Test", 0.0, 0.5),
        SubtitleWord("line", 0.6, 1.0),
        SubtitleWord("now!", 1.1, 1.5),
    ]
    return SubtitleSegment(words=words)


@pytest.fixture
def base_config() -> StyleEngineConfig:
    """Provides a basic, empty StyleEngineConfig."""
    return StyleEngineConfig(
        script_info={},
        styles=[{"Name": "Default"}],
        rules=[],
    )


def test_char_context_generation(sample_segment: SubtitleSegment) -> None:
    """Verify that character contexts are generated with correct indices and flags."""
    engine = StylerEngine(StyleEngineConfig())
    contexts = engine._get_char_contexts(sample_segment)

    assert len(contexts) == 12  # "Test line now!" without spaces

    # Test context for 'T' (first char, first word)
    ctx_t = contexts[0]
    assert ctx_t.char == "T"
    assert ctx_t.char_index_line == 0
    assert ctx_t.char_index_word == 0
    assert ctx_t.word_index_line == 0
    assert ctx_t.is_first_char is True
    assert ctx_t.is_last_char is False
    assert ctx_t.is_first_word is True
    assert ctx_t.is_last_word is False

    # Test context for 't' (last char, first word)
    ctx_last_t = contexts[3]
    assert ctx_last_t.char == "t"
    assert ctx_last_t.char_index_word == 3
    assert ctx_last_t.is_first_char is False
    assert ctx_last_t.is_last_char is True

    # Test context for 'n' (first char, third word)
    ctx_n = contexts[8]
    assert ctx_n.char == "n"
    assert ctx_n.char_index_line == 8
    assert ctx_n.char_index_word == 0
    assert ctx_n.word_index_line == 2
    assert ctx_n.is_first_char is True
    assert ctx_n.is_last_word is True

    # Test context for '!' (last char, last word)
    ctx_excl = contexts[11]
    assert ctx_excl.char == "!"
    assert ctx_excl.char_index_word == 3
    assert ctx_excl.is_last_char is True
    assert ctx_excl.is_last_word is True


def test_applied_styles_to_ass_tags() -> None:
    """Verify that AppliedStyles correctly formats various ASS tags."""
    # Test empty
    assert AppliedStyles().to_ass_tags(MagicMock()) == ""

    # Test blur
    styles = AppliedStyles(style_override=StyleOverride(blur=5))
    assert styles.to_ass_tags(MagicMock()) == r"{\blur5}"

    # Test transforms
    transform = Transform(start=100, end=500, accel=0.5, scale_x=120, primary_color="&HFFFFFF&")
    styles = AppliedStyles(transforms=[transform])
    assert styles.to_ass_tags(MagicMock()) == r"{\t(100,500,0.5,\fscx120\fscy100\1c&HFFFFFF&)}"

    # Test raw prefix
    styles = AppliedStyles(raw_prefix=r"\an5", style_override=StyleOverride(blur=2))
    assert styles.to_ass_tags(MagicMock()) == r"{\an5\blur2}"


def test_process_segment_no_rules(base_config: StyleEngineConfig, sample_segment: SubtitleSegment) -> None:
    """Test that with no rules, the default style and plain text are produced."""
    engine = StylerEngine(base_config)
    style_name, text = engine.process_segment(sample_segment, "Default")
    assert style_name == "Default"
    assert text == "Test line now!"


def test_rule_priority(base_config: StyleEngineConfig, sample_segment: SubtitleSegment) -> None:
    """Test that a higher-priority rule overrides a lower-priority one."""
    low_priority_rule = StyleRule(
        priority=1,
        apply_to="word",
        regex=re.compile("line"),
        style_override=StyleOverride(blur=1),
    )
    high_priority_rule = StyleRule(
        priority=10,
        apply_to="word",
        regex=re.compile("line"),
        style_override=StyleOverride(blur=10),
    )
    config_with_rules = StyleEngineConfig(rules=[low_priority_rule, high_priority_rule])
    engine = StylerEngine(config_with_rules)

    _, text = engine.process_segment(sample_segment, "Default")
    assert text == r"Test {\blur10}line{\r} now!"


def test_rule_targeting_and_conditions(sample_segment: SubtitleSegment) -> None:
    """Test various rule targeting and operator conditions."""
    # Rule for the first character of the word "line"
    rule = StyleRule(
        apply_to="word",
        regex=re.compile("line"),
        operators=[RuleOperator(target="char", is_first=True)],
        style_override=StyleOverride(blur=5),
    )
    config_with_rule = StyleEngineConfig(rules=[rule])
    engine = StylerEngine(config_with_rule)
    _, text = engine.process_segment(sample_segment, "Default")
    assert text == r"Test {\blur5}l{\r}ine now!"


def test_tag_consolidation_and_reset(sample_segment: SubtitleSegment) -> None:
    """Test that tags are consolidated for adjacent characters and reset when style changes."""
    # Rule to style the entire word "line"
    rule = StyleRule(
        apply_to="word",
        regex=re.compile("line"),
        style_override=StyleOverride(blur=3),
    )
    config_with_rule = StyleEngineConfig(rules=[rule])
    engine = StylerEngine(config_with_rule)
    _, text = engine.process_segment(sample_segment, "Default")
    # Tags should be applied once for the whole word, then reset.
    assert text == r"Test {\blur3}line{\r} now!"


def test_style_name_override(sample_segment: SubtitleSegment) -> None:
    """Test that a line-level rule can override the style name for the segment."""
    rule = StyleRule(
        apply_to="line",
        regex=re.compile("Test line"),
        style_name="OverriddenStyle",
    )
    config_with_rule = StyleEngineConfig(rules=[rule])
    engine = StylerEngine(config_with_rule)
    style_name, _ = engine.process_segment(sample_segment, "Default")
    assert style_name == "OverriddenStyle"


def test_negated_operator(sample_segment: SubtitleSegment) -> None:
    """Test a rule with a negated operator."""
    # Style any character in "now!" that is NOT the first character
    rule = StyleRule(
        apply_to="word",
        regex=re.compile("now!"),
        operators=[RuleOperator(target="char", is_first=True, negate=True)],
        style_override=StyleOverride(blur=1),
    )
    config_with_rule = StyleEngineConfig(rules=[rule])
    engine = StylerEngine(config_with_rule)
    _, text = engine.process_segment(sample_segment, "Default")
    assert text == r"Test line n{\blur1}ow!{\r}"


def test_state_is_reset_between_segments() -> None:
    """Verify that rule-matching state is reset for each new segment processed."""
    segment1 = SubtitleSegment(words=[SubtitleWord("MATCH", 0, 1)])
    segment2 = SubtitleSegment(words=[SubtitleWord("no-match", 2, 3)])
    rule = StyleRule(apply_to="line", regex=re.compile("MATCH"), style_override=StyleOverride(blur=1))
    config_with_rule = StyleEngineConfig(rules=[rule])
    engine = StylerEngine(config_with_rule)

    # Process the first segment, which should match and set internal state
    _, text1 = engine.process_segment(segment1, "Default")
    assert r"{\blur1}MATCH{\r}" in text1
    assert engine.last_line_check_result is True

    # Process the second segment, which should NOT match
    _, text2 = engine.process_segment(segment2, "Default")
    assert text2 == "no-match"
    assert engine.last_line_check_result is False
