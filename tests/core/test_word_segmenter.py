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


def test_segment_words_default(sample_words: list[SubtitleWord]) -> None:
    """Test segmentation with the default character limit."""
    segments = segment_words(sample_words, max_chars=35, max_lines=1)  # Test uncombined
    assert len(segments) == 4
    assert str(segments[0].text) == "This is a test transcription for"
    assert str(segments[1].text) == "the auto-subs library."
    assert str(segments[2].text) == "It includes punctuation!"
    assert str(segments[3].text) == "And a final line."


def test_segment_words_short_lines(sample_words: list[SubtitleWord]) -> None:
    """Test segmentation with a very short character limit."""
    segments = segment_words(sample_words, max_chars=16, max_lines=1)  # Test uncombined
    assert len(segments) == 9
    assert str(segments[0].text) == "This is a test"
    assert str(segments[1].text) == "transcription"
    assert str(segments[2].text) == "for the"
    assert str(segments[8].text) == "line."


def test_segment_words_break_chars(sample_words: list[SubtitleWord]) -> None:
    """Test that break characters force a new line regardless of length."""
    segments = segment_words(sample_words, max_chars=100, max_lines=1)  # Test uncombined
    assert len(segments) == 3
    assert str(segments[0].text) == "This is a test transcription for the auto-subs library."
    assert str(segments[1].text) == "It includes punctuation!"
    assert str(segments[2].text) == "And a final line."


def test_segment_words_with_long_word() -> None:
    """Test segmentation handles a single word longer than max_chars."""
    long_word = SubtitleWord(text="Supercalifragilisticexpialidocious", start=0.0, end=1.0)
    words = [
        long_word,
        SubtitleWord(text="is", start=1.1, end=1.2),
        SubtitleWord(text="a", start=1.3, end=1.4),
    ]
    segments = segment_words(words, max_chars=20)
    # The long word should be on its own line, combined with the next line.
    assert len(segments) == 1
    assert str(segments[0].text) == "Supercalifragilisticexpialidocious\nis a"


def test_segment_words_empty_input() -> None:
    """Test segmentation with an empty list of words."""
    assert segment_words([]) == []


def test_segment_words_handles_empty_word_text() -> None:
    """Test that words with empty or whitespace-only text are skipped."""
    words = [
        SubtitleWord(text="Hello", start=0.0, end=0.5),
        SubtitleWord(text=" ", start=0.5, end=0.6),
        SubtitleWord(text="world", start=0.6, end=1.0),
    ]
    segments = segment_words(words)
    assert len(segments) == 1
    assert str(segments[0].text) == "Hello world"


def test_segment_words_max_lines_combines_short_lines(
    sample_words: list[SubtitleWord],
) -> None:
    """Test that max_lines combines short lines into multi-line segments."""
    segments = segment_words(sample_words, max_chars=35, max_lines=2)
    assert len(segments) == 2
    assert segments[0].text == "This is a test transcription for\nthe auto-subs library."
    assert segments[1].text == "It includes punctuation!\nAnd a final line."
    assert segments[0].start == pytest.approx(0.1)
    assert segments[0].end == pytest.approx(4.2)
    assert segments[1].start == pytest.approx(5.1)
    assert segments[1].end == pytest.approx(9.0)


def test_segment_words_max_lines_with_odd_number_of_lines(
    sample_words: list[SubtitleWord],
) -> None:
    """Test that max_lines handles leftover single lines correctly."""
    # This will generate 3 lines based on punctuation breaks. With max_lines=2,
    # it should be one 2-line segment and one 1-line segment.
    segments = segment_words(sample_words, max_chars=100, max_lines=2)
    assert len(segments) == 2
    assert segments[0].text == "This is a test transcription for the auto-subs library.\nIt includes punctuation!"
    assert segments[1].text == "And a final line."


def test_segment_words_max_lines_one_does_nothing(
    sample_words: list[SubtitleWord],
) -> None:
    """Test that max_lines=1 does not combine any lines."""
    segments_default = segment_words(sample_words, max_chars=35, max_lines=1)
    assert len(segments_default) == 4  # Same as default behavior without combining
    assert "\n" not in segments_default[0].text
