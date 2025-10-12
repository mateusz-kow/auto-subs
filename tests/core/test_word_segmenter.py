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
    segments = segment_words(sample_words, max_chars=35)
    assert len(segments) == 4
    assert str(segments[0]) == "This is a test transcription for"
    assert str(segments[1]) == "the auto-subs library."
    assert str(segments[2]) == "It includes punctuation!"
    assert str(segments[3]) == "And a final line."


def test_segment_words_short_lines(sample_words: list[SubtitleWord]) -> None:
    """Test segmentation with a very short character limit."""
    segments = segment_words(sample_words, max_chars=16)
    assert len(segments) == 9
    assert str(segments[0]) == "This is a test"
    assert str(segments[1]) == "transcription"
    assert str(segments[2]) == "for the"
    assert str(segments[8]) == "line."


def test_segment_words_break_chars(sample_words: list[SubtitleWord]) -> None:
    """Test that break characters force a new line regardless of length."""
    segments = segment_words(sample_words, max_chars=100)
    assert len(segments) == 3
    assert str(segments[0]) == "This is a test transcription for the auto-subs library."
    assert str(segments[1]) == "It includes punctuation!"
    assert str(segments[2]) == "And a final line."


def test_segment_words_with_long_word() -> None:
    """Test segmentation handles a single word longer than max_chars."""
    long_word = SubtitleWord(text="Supercalifragilisticexpialidocious", start=0.0, end=1.0)
    words = [long_word, SubtitleWord(text="is", start=1.1, end=1.2), SubtitleWord(text="a", start=1.3, end=1.4)]
    segments = segment_words(words, max_chars=20)
    # The long word should be on its own line
    assert len(segments) == 2
    assert str(segments[0]) == long_word.text
    # The next line should start with the next word
    assert str(segments[1]) == "is a"


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
    assert str(segments[0]) == "Hello world"
