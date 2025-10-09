import json
from pathlib import Path

import pytest

from auto_subs.core.word_segmenter import segment_words
from auto_subs.typing.transcription import Transcription


@pytest.fixture
def sample_transcription() -> Transcription:
    """Load sample transcription data from a fixture file."""
    path = Path(__file__).parent.parent / "fixtures" / "sample_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_segment_words_default(sample_transcription: Transcription) -> None:
    """Test segmentation with default character limit."""
    segments = segment_words(sample_transcription, max_chars=35)
    assert len(segments) == 4
    # The line should break *before* exceeding max_chars.
    assert segments[0]["text"] == "This is a test transcription for"
    assert segments[1]["text"] == "the auto-subs library."
    assert segments[2]["text"] == "It includes punctuation!"
    assert segments[3]["text"] == "And a final line."


def test_segment_words_short_lines(sample_transcription: Transcription) -> None:
    """Test segmentation with a very short character limit."""
    segments = segment_words(sample_transcription, max_chars=16)
    assert len(segments) == 9
    assert segments[0]["text"] == "This is a test"
    assert segments[1]["text"] == "transcription"
    assert segments[2]["text"] == "for the"
    assert segments[8]["text"] == "line."


def test_segment_words_break_chars(sample_transcription: Transcription) -> None:
    """Test that break characters force a new line regardless of length."""
    segments = segment_words(sample_transcription, max_chars=100)
    assert len(segments) == 3
    assert segments[0]["text"] == "This is a test transcription for the auto-subs library."
    assert segments[1]["text"] == "It includes punctuation!"
    assert segments[2]["text"] == "And a final line."


def test_empty_transcription() -> None:
    """Test segmentation with empty or invalid transcription data."""
    assert segment_words({"segments": []}) == []  # type: ignore[reportArgumentType]
    assert segment_words({"segments": [{"words": []}]}) == []  # type: ignore[reportArgumentType]


def test_invalid_transcription_format() -> None:
    """Test that invalid transcription formats raise a ValueError."""
    with pytest.raises(ValueError):
        segment_words({"no_segments_key": []})  # type: ignore[reportArgumentType]
    with pytest.raises(ValueError):
        segment_words({"segments": [{"no_words_key": []}]})  # type: ignore[reportArgumentType]
