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
    assert segment.start == 0.5
    assert segment.end == 1.5
    assert segment.text == "Hello world."

    with pytest.raises(ValueError, match="must contain at least one word"):
        SubtitleSegment(words=[])

    with pytest.raises(ValueError, match="has invalid timestamp"):
        word3 = SubtitleWord(text="invalid", start=2.0, end=1.9)
        SubtitleSegment(words=[word3])


def test_subtitles_sorting_and_overlap_warning(caplog: LogCaptureFixture) -> None:
    """Test that Subtitles automatically sorts segments and warns on overlap."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="B", start=2.0, end=3.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="A", start=0.0, end=1.0)])
    seg3 = SubtitleSegment(words=[SubtitleWord(text="Overlap", start=2.5, end=3.5)])

    # Segments are out of order and one overlaps
    with caplog.at_level(logging.WARNING):
        subtitles = Subtitles(segments=[seg1, seg2, seg3])

    # Check sorting
    assert subtitles.segments[0] is seg2
    assert subtitles.segments[1] is seg1
    assert subtitles.segments[2] is seg3

    # Check for warning log
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
