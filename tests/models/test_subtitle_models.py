from typing import Any
from unittest.mock import patch

import pytest

from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


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


def test_subtitles_from_dict_creates_segments() -> None:
    """Test that Subtitles.from_dict builds subtitle segments correctly."""
    mock_dict = {
        "text": "Hello world",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "text": "Hello world",
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0},
                ],
            }
        ],
        "language": "en",
    }

    # Mock segment_words to isolate testing to the Subtitles class logic
    mock_segments_from_word_segmenter = [
        {
            "text": "Hello world",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.5, "end": 1.0},
            ],
        }
    ]

    with patch(
        "auto_subs.models.subtitles.segment_words",
        return_value=mock_segments_from_word_segmenter,
    ) as mock_sw:
        subtitles = Subtitles.from_dict(mock_dict)
        mock_sw.assert_called_once()

    assert isinstance(subtitles, Subtitles)
    assert len(subtitles.segments) == 1

    segment = subtitles.segments[0]
    assert isinstance(segment, SubtitleSegment)
    assert len(segment.words) == 2
    assert str(segment) == "Hello world"
    assert subtitles.segments[0].start == 0.0
    assert subtitles.segments[0].end == 1.0


def test_subtitles_from_dict_raises_value_error_on_invalid_data() -> None:
    """Test that Subtitles.from_dict raises ValueError for invalid data."""
    invalid_dict: dict[str, Any] = {"text": "missing segments", "language": "en"}
    with pytest.raises(ValueError, match="Transcription data failed validation."):
        Subtitles.from_dict(invalid_dict)
