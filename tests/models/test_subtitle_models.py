import logging

import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core.builder import create_dict_from_subtitles
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


def test_subtitle_word_validation() -> None:
    """Test SubtitleWord timestamp validation."""
    word = SubtitleWord(text="test", start=1.0, end=2.0)
    assert word.text == "test"
    with pytest.raises(ValueError, match="has invalid timestamp"):
        SubtitleWord(text="invalid", start=2.0, end=1.0)


def test_subtitle_segment_properties_and_validation() -> None:
    """Test SubtitleSegment properties and validations."""
    word1 = SubtitleWord(text="Hello", start=0.5, end=1.0)
    word2 = SubtitleWord(text="world.", start=1.1, end=1.5)

    segment = SubtitleSegment(words=[word1, word2])
    assert segment.start == pytest.approx(0.5)
    assert segment.end == pytest.approx(1.5)
    assert segment.text == "Hello world."

    empty_segment = SubtitleSegment(words=[])
    assert empty_segment.start == pytest.approx(0.0)
    assert empty_segment.end == pytest.approx(0.0)

    with pytest.raises(ValueError, match="has invalid timestamp"):
        word3 = SubtitleWord(text="invalid", start=2.0, end=1.9)
        SubtitleSegment(words=[word3])


def test_subtitles_sorting_and_overlap_warning(caplog: LogCaptureFixture) -> None:
    """Test that Subtitles automatically sorts segments and warns on overlap."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="B", start=2.0, end=3.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="A", start=0.0, end=1.0)])
    seg3 = SubtitleSegment(words=[SubtitleWord(text="Overlap", start=2.5, end=3.5)])

    with caplog.at_level(logging.WARNING):
        subtitles = Subtitles(segments=[seg1, seg2, seg3])

    assert subtitles.segments[0] is seg2
    assert subtitles.segments[1] is seg1
    assert subtitles.segments[2] is seg3

    assert len(caplog.records) == 1
    assert "Overlap detected" in caplog.text
    assert "ending at 3.000s overlaps with segment starting at 2.500s" in caplog.text


def test_subtitles_to_transcription_dict() -> None:
    """Test conversion of a Subtitles object back to a transcription dictionary."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="First.", start=0.0, end=1.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Second.", start=2.0, end=3.0)])
    subtitles = Subtitles(segments=[seg1, seg2])

    result = create_dict_from_subtitles(subtitles)

    assert result["language"] == "unknown"
    assert result["text"] == "First.\nSecond."
    assert len(result["segments"]) == 2
    assert result["segments"][0]["id"] == 1
    assert result["segments"][0]["text"] == "First."
    assert result["segments"][0]["words"][0]["word"] == "First."


def test_subtitles_string_representation() -> None:
    """Test the __str__ method of the Subtitles object."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="First line.", start=0.0, end=1.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Second line.", start=2.0, end=3.0)])
    subtitles = Subtitles(segments=[seg1, seg2])
    assert str(subtitles.text) == "First line.\nSecond line."


def test_subtitle_segment_apply_balanced_wrapping() -> None:
    """Test balanced line wrapping on SubtitleSegment."""
    # Test with the exact example from the issue
    words = [
        SubtitleWord(text="The", start=0.0, end=0.2),
        SubtitleWord(text="quick", start=0.2, end=0.4),
        SubtitleWord(text="brown", start=0.4, end=0.6),
        SubtitleWord(text="fox", start=0.6, end=0.8),
        SubtitleWord(text="jumps", start=0.8, end=1.0),
        SubtitleWord(text="over", start=1.0, end=1.2),
        SubtitleWord(text="the", start=1.2, end=1.4),
        SubtitleWord(text="lazy", start=1.4, end=1.6),
        SubtitleWord(text="dog.", start=1.6, end=1.8),
    ]
    segment = SubtitleSegment(words=words)

    # Apply balanced wrapping
    result = segment.apply_balanced_wrapping(max_width_chars=42)

    # Should return the segment itself for chaining
    assert result is segment

    # The text should now contain a line break
    assert "\\N" in segment.text

    # Verify the result is balanced
    lines = segment.text.split("\\N")
    assert len(lines) == 2
    # The algorithm produces a well-balanced result
    difference = abs(len(lines[0]) - len(lines[1]))
    assert difference <= 10  # Well-balanced result


def test_subtitle_segment_balanced_wrapping_short_text() -> None:
    """Test that short text is not broken when applying balanced wrapping."""
    words = [
        SubtitleWord(text="Hello", start=0.0, end=0.5),
        SubtitleWord(text="world!", start=0.5, end=1.0),
    ]
    segment = SubtitleSegment(words=words)

    segment.apply_balanced_wrapping(max_width_chars=42)

    # Short text should not be broken
    assert "\\N" not in segment.text
    assert segment.text == "Hello world!"


def test_subtitle_segment_balanced_wrapping_chaining() -> None:
    """Test that apply_balanced_wrapping supports method chaining."""
    words = [
        SubtitleWord(text="First", start=0.0, end=0.5),
        SubtitleWord(text="segment", start=0.5, end=1.0),
        SubtitleWord(text="with", start=1.0, end=1.5),
        SubtitleWord(text="multiple", start=1.5, end=2.0),
        SubtitleWord(text="words", start=2.0, end=2.5),
    ]
    segment = SubtitleSegment(words=words)

    # Test method chaining with shift_by
    result = segment.apply_balanced_wrapping(max_width_chars=20).shift_by(1.0)

    assert result is segment
    assert segment.start == pytest.approx(1.0)

