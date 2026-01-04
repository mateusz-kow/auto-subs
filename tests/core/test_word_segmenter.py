"""Tests for the professional word segmentation engine."""

from typing import Any

import pytest

from autosubs.core.word_segmenter import segment_words
from autosubs.models.subtitles import SubtitleWord
from autosubs.models.transcription import TranscriptionModel


@pytest.fixture
def sample_words(sample_transcription: dict[str, Any]) -> list[SubtitleWord]:
    """Provides a list of SubtitleWord objects from the raw transcription fixture."""
    model = TranscriptionModel.model_validate(sample_transcription)
    return [
        SubtitleWord(text=word.word, start=word.start, end=word.end)
        for segment in model.segments
        for word in segment.words
    ]


def test_segment_words_no_internal_newlines(sample_words: list[SubtitleWord]) -> None:
    """Test that segmentation creates separate SubtitleSegment objects without hardcoded newlines."""
    segments = segment_words(sample_words, char_limit=35)

    assert len(segments) > 0
    for segment in segments:
        assert "\\N" not in segment.text
        assert "\n" not in segment.text


def test_segment_words_creates_independent_segments(sample_words: list[SubtitleWord]) -> None:
    """Test that heuristic logic results in independent timed segments."""
    segments = segment_words(sample_words, char_limit=35)

    assert len(segments) >= 2
    for seg in segments:
        assert "\\N" not in seg.text
        assert "\n" not in seg.text


def test_segment_words_punctuation_boundaries() -> None:
    """Test that segments are correctly created at natural linguistic boundaries."""
    words = [
        SubtitleWord(text="First", start=0.0, end=0.5),
        SubtitleWord(text="sentence.", start=0.6, end=1.0),
        SubtitleWord(text="Second", start=2.0, end=2.5),
        SubtitleWord(text="part!", start=2.6, end=3.0),
    ]
    segments = segment_words(words, char_limit=100)

    assert len(segments) == 2
    assert segments[0].text == "First sentence."
    assert segments[1].text == "Second part!"


def test_segment_words_handles_empty_input() -> None:
    """Test that empty word list returns empty segment list."""
    assert segment_words([]) == []


def test_segment_words_handles_whitespace_only_words() -> None:
    """Test that whitespace-only word strings are filtered out."""
    words = [
        SubtitleWord(text="Valid", start=0.0, end=1.0),
        SubtitleWord(text="  ", start=1.0, end=1.1),
        SubtitleWord(text="Word", start=1.1, end=2.0),
    ]
    segments = segment_words(words, char_limit=42)

    assert len(segments) == 1
    assert segments[0].text == "Valid Word"
