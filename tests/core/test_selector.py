"""Tests for line selection functionality."""

import re

import pytest

from autosubs.core.selector import LineSelector
from autosubs.models.subtitles.ass import AssSubtitleSegment, AssSubtitleWord


def create_segment(
    text: str,
    start: float,
    end: float,
    actor: str = "",
    style: str = "Default",
    layer: int = 0,
    effect: str = "",
) -> AssSubtitleSegment:
    """Helper to create a test segment."""
    word = AssSubtitleWord(text=text, start=start, end=end)
    segment = AssSubtitleSegment(words=[word])
    segment.actor_name = actor
    segment.style_name = style
    segment.layer = layer
    segment.effect = effect
    return segment


def test_by_actor_case_insensitive() -> None:
    """Test filtering by actor name (case insensitive)."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, actor="Singer"),
        create_segment("Line 2", 1.0, 2.0, actor="Narrator"),
        create_segment("Line 3", 2.0, 3.0, actor="singer"),
    ]
    
    result = LineSelector.by_actor(segments, "Singer")
    assert len(result) == 2
    assert result[0].text == "Line 1"
    assert result[1].text == "Line 3"


def test_by_actor_case_sensitive() -> None:
    """Test filtering by actor name (case sensitive)."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, actor="Singer"),
        create_segment("Line 2", 1.0, 2.0, actor="singer"),
    ]
    
    result = LineSelector.by_actor(segments, "Singer", case_sensitive=True)
    assert len(result) == 1
    assert result[0].text == "Line 1"


def test_by_style_case_insensitive() -> None:
    """Test filtering by style name (case insensitive)."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, style="Karaoke"),
        create_segment("Line 2", 1.0, 2.0, style="Default"),
        create_segment("Line 3", 2.0, 3.0, style="karaoke"),
    ]
    
    result = LineSelector.by_style(segments, "Karaoke")
    assert len(result) == 2
    assert result[0].text == "Line 1"
    assert result[1].text == "Line 3"


def test_by_style_case_sensitive() -> None:
    """Test filtering by style name (case sensitive)."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, style="Karaoke"),
        create_segment("Line 2", 1.0, 2.0, style="karaoke"),
    ]
    
    result = LineSelector.by_style(segments, "Karaoke", case_sensitive=True)
    assert len(result) == 1
    assert result[0].text == "Line 1"


def test_by_text_regex_string_pattern() -> None:
    """Test filtering by regex pattern (string)."""
    segments = [
        create_segment("Hello world", 0.0, 1.0),
        create_segment("Goodbye world", 1.0, 2.0),
        create_segment("Hello there", 2.0, 3.0),
    ]
    
    result = LineSelector.by_text_regex(segments, r"^Hello")
    assert len(result) == 2
    assert result[0].text == "Hello world"
    assert result[1].text == "Hello there"


def test_by_text_regex_compiled_pattern() -> None:
    """Test filtering by regex pattern (compiled)."""
    segments = [
        create_segment("Test 123", 0.0, 1.0),
        create_segment("No numbers", 1.0, 2.0),
        create_segment("Test 456", 2.0, 3.0),
    ]
    
    pattern = re.compile(r"\d+")
    result = LineSelector.by_text_regex(segments, pattern)
    assert len(result) == 2
    assert result[0].text == "Test 123"
    assert result[1].text == "Test 456"


def test_by_layer() -> None:
    """Test filtering by layer number."""
    segments = [
        create_segment("Layer 0", 0.0, 1.0, layer=0),
        create_segment("Layer 1", 1.0, 2.0, layer=1),
        create_segment("Layer 0 again", 2.0, 3.0, layer=0),
    ]
    
    result = LineSelector.by_layer(segments, 0)
    assert len(result) == 2
    assert result[0].text == "Layer 0"
    assert result[1].text == "Layer 0 again"


def test_by_effect() -> None:
    """Test filtering by effect field."""
    segments = [
        create_segment("Effect 1", 0.0, 1.0, effect="fade"),
        create_segment("Effect 2", 1.0, 2.0, effect="scroll"),
        create_segment("Effect 3", 2.0, 3.0, effect="Fade"),
    ]
    
    result = LineSelector.by_effect(segments, "fade")
    assert len(result) == 2
    assert result[0].text == "Effect 1"
    assert result[1].text == "Effect 3"


def test_by_time_range_both_bounds() -> None:
    """Test filtering by time range with both start and end."""
    segments = [
        create_segment("Before", 0.0, 1.0),
        create_segment("Inside 1", 2.0, 3.0),
        create_segment("Inside 2", 3.0, 4.0),
        create_segment("After", 5.0, 6.0),
    ]
    
    result = LineSelector.by_time_range(segments, start=2.0, end=4.0)
    assert len(result) == 2
    assert result[0].text == "Inside 1"
    assert result[1].text == "Inside 2"


def test_by_time_range_start_only() -> None:
    """Test filtering by time range with start only."""
    segments = [
        create_segment("Early", 0.0, 1.0),
        create_segment("Later 1", 2.0, 3.0),
        create_segment("Later 2", 3.0, 4.0),
    ]
    
    result = LineSelector.by_time_range(segments, start=2.0)
    assert len(result) == 2
    assert result[0].text == "Later 1"
    assert result[1].text == "Later 2"


def test_by_time_range_end_only() -> None:
    """Test filtering by time range with end only."""
    segments = [
        create_segment("Early 1", 0.0, 1.0),
        create_segment("Early 2", 1.0, 2.0),
        create_segment("Late", 5.0, 6.0),
    ]
    
    result = LineSelector.by_time_range(segments, end=2.0)
    assert len(result) == 2
    assert result[0].text == "Early 1"
    assert result[1].text == "Early 2"


def test_by_custom_predicate() -> None:
    """Test filtering with custom predicate."""
    segments = [
        create_segment("Short", 0.0, 1.0),
        create_segment("Very long text here", 1.0, 2.0),
        create_segment("Hi", 2.0, 3.0),
    ]
    
    # Filter segments with text length > 5
    result = LineSelector.by_custom(segments, lambda seg: len(seg.text) > 5)
    assert len(result) == 1
    assert result[0].text == "Very long text here"


def test_combine_and() -> None:
    """Test combining filters with AND logic."""
    segments = [
        create_segment("Hello Singer", 0.0, 1.0, actor="Singer", style="Karaoke"),
        create_segment("Hello Robot", 1.0, 2.0, actor="Robot", style="Default"),
        create_segment("Goodbye Singer", 2.0, 3.0, actor="Singer", style="Default"),
    ]
    
    by_actor_result = LineSelector.by_actor(segments, "Singer")
    by_style_result = LineSelector.by_style(segments, "Karaoke")
    
    result = LineSelector.combine_and(by_actor_result, by_style_result)
    assert len(result) == 1
    assert result[0].text == "Hello Singer"


def test_combine_or() -> None:
    """Test combining filters with OR logic."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, actor="Singer"),
        create_segment("Line 2", 1.0, 2.0, style="Karaoke"),
        create_segment("Line 3", 2.0, 3.0, actor="Robot"),
    ]
    
    by_actor_result = LineSelector.by_actor(segments, "Singer")
    by_style_result = LineSelector.by_style(segments, "Karaoke")
    
    result = LineSelector.combine_or(by_actor_result, by_style_result)
    assert len(result) == 2
    assert result[0].text == "Line 1"
    assert result[1].text == "Line 2"


def test_empty_results() -> None:
    """Test that filters return empty lists when no matches."""
    segments = [
        create_segment("Line 1", 0.0, 1.0, actor="Singer"),
    ]
    
    result = LineSelector.by_actor(segments, "NonExistent")
    assert len(result) == 0


def test_chaining_filters() -> None:
    """Test chaining multiple filters together."""
    segments = [
        create_segment("Hello world", 0.0, 1.0, actor="Singer", style="Karaoke"),
        create_segment("Hello there", 1.0, 2.0, actor="Singer", style="Default"),
        create_segment("Goodbye world", 2.0, 3.0, actor="Robot", style="Karaoke"),
    ]
    
    # Filter by actor, then by style, then by regex
    result = LineSelector.by_actor(segments, "Singer")
    result = LineSelector.by_style(result, "Karaoke")
    result = LineSelector.by_text_regex(result, "Hello")
    
    assert len(result) == 1
    assert result[0].text == "Hello world"
