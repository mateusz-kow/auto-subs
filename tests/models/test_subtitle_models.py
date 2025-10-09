from unittest.mock import patch

import pytest

from auto_subs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord
from auto_subs.models.transcription import TranscriptionModel


def test_subtitle_word_from_dict() -> None:
    """Test that SubtitleWord.from_dict correctly creates an instance."""
    data = {"word": " Hello ", "start": 1.0, "end": 2.0}
    word = SubtitleWord.from_dict(data)

    assert isinstance(word, SubtitleWord)
    assert word.text == "Hello"  # Leading/trailing spaces are stripped
    assert word.start == 1.0
    assert word.end == 2.0


def test_subtitle_segment_raises_for_empty_words() -> None:
    """Test that SubtitleSegment raises ValueError when initialized with no words."""
    with pytest.raises(ValueError, match="SubtitleSegment must contain at least one word."):
        SubtitleSegment(words=[])


def test_subtitles_from_transcription_creates_segments() -> None:
    """Test that Subtitles.from_transcription builds subtitle segments correctly."""
    mock_transcription = TranscriptionModel(
        text="Hello world",
        segments=[],
        language="en",
    )

    # Mock segment_words to return a structured response similar to the actual output
    mock_segments = [
        {
            "text": "Hello world",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.5, "end": 1.0},
            ],
        }
    ]

    with patch("auto_subs.models.subtitles.segment_words", return_value=mock_segments):
        subtitles = Subtitles.from_transcription(mock_transcription)

    assert isinstance(subtitles, Subtitles)
    assert len(subtitles.segments) == 1

    segment = subtitles.segments[0]
    assert isinstance(segment, SubtitleSegment)
    assert len(segment.words) == 2
    assert str(segment) == "Hello world"
    assert subtitles.segments[0].start == 0.0
    assert subtitles.segments[0].end == 1.0
