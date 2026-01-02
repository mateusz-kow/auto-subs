"""Tests for the word segmentation engine."""

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


def test_segment_words_deterministic_output(sample_words: list[SubtitleWord]) -> None:
    """Test that segmentation creates separate SubtitleSegment objects."""
    segments = segment_words(sample_words, max_chars=35, max_lines=1)

    assert len(segments) > 0
    for segment in segments:
        assert "\\N" not in segment.text
        assert "\n" not in segment.text


def test_segment_words_max_lines_creates_more_segments(sample_words: list[SubtitleWord]) -> None:
    """Test that max_lines > 1 results in multiple discrete segments, not newlines."""
    # When max_lines is 2, it groups lines but then the DP passes and splits them
    # back into optimal timed segments.
    segments = segment_words(sample_words, max_chars=35, max_lines=2)

    assert len(segments) >= 2
    # Verify absolute absence of newline control characters in the core output
    for seg in segments:
        assert "\\N" not in seg.text
        assert "\n" not in seg.text


def test_segment_words_punctuation_breaks(sample_words: list[SubtitleWord]) -> None:
    """Test that segments are correctly created at punctuation boundaries."""
    segments = segment_words(sample_words, max_chars=100, max_lines=1)

    # First sentence: "This is a test transcription for the auto-subs library."
    assert segments[0].text.endswith(".")
    assert "punctuation!" in segments[1].text


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
    segments = segment_words(words, max_chars=42)

    assert len(segments) == 1
    assert segments[0].text == "Valid Word"
