import json
from pathlib import Path

import pytest

from auto_subs.core.word_segmenter import segment_words
from auto_subs.typing.transcription import SegmentDict, Transcription


@pytest.fixture
def sample_transcription() -> Transcription:
    """Load a sample transcription from a fixture file."""
    path = Path(__file__).parent.parent / "fixtures" / "sample_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def empty_transcription() -> Transcription:
    """Load an empty transcription from a fixture file."""
    path = Path(__file__).parent.parent / "fixtures" / "empty_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_segment_words_default(sample_transcription: Transcription, empty_transcription: Transcription) -> None:
    """Test segmentation with the default character limit."""
    segments = segment_words(sample_transcription, max_chars=35)
    assert len(segments) == 4
    assert segments[0]["text"] == "This is a test transcription for"
    assert segments[1]["text"] == "the auto-subs library."
    assert segments[2]["text"] == "It includes punctuation!"
    assert segments[3]["text"] == "And a final line."

    empty_segments = segment_words(empty_transcription, max_chars=35)
    assert empty_segments == []


def test_segment_words_short_lines(sample_transcription: Transcription, empty_transcription: Transcription) -> None:
    """Test segmentation with a very short character limit."""
    segments = segment_words(sample_transcription, max_chars=16)
    assert len(segments) == 9
    assert segments[0]["text"] == "This is a test"
    assert segments[1]["text"] == "transcription"
    assert segments[2]["text"] == "for the"
    assert segments[8]["text"] == "line."

    empty_segments = segment_words(empty_transcription, max_chars=16)
    assert empty_segments == []


def test_segment_words_break_chars(sample_transcription: Transcription, empty_transcription: Transcription) -> None:
    """Test that break characters force a new line regardless of length."""
    segments = segment_words(sample_transcription, max_chars=100)
    assert len(segments) == 3
    assert segments[0]["text"] == "This is a test transcription for the auto-subs library."
    assert segments[1]["text"] == "It includes punctuation!"
    assert segments[2]["text"] == "And a final line."

    empty_segments = segment_words(empty_transcription, max_chars=100)
    assert empty_segments == []


def test_empty_transcription(empty_transcription: Transcription) -> None:
    """Test segmentation with empty transcription data."""
    segments = segment_words(empty_transcription)
    assert segments == []


def test_invalid_transcription_format() -> None:
    """Test that invalid transcription formats raise a ValueError."""
    with pytest.raises(ValueError):
        segment_words({"no_segments_key": []})  # type: ignore[reportArgumentType]

    with pytest.raises(ValueError):
        segment_words({"segments": [{"no_words_key": []}]})  # type: ignore[reportArgumentType]


def test_segment_words_returns_empty_for_no_words() -> None:
    """Test that segment_words returns an empty list when transcription has no words."""
    segment: SegmentDict = {
        "id": 0,
        "start": 0.0,
        "end": 0.0,
        "text": "",
        "words": [],
    }
    empty_transcription: Transcription = {"segments": [segment], "text": "", "language": "en"}
    segments = segment_words(empty_transcription)
    assert segments == []


def test_segment_words_creates_line_from_current_line_words() -> None:
    """Test that a segment is correctly created when current_line_words is not empty."""
    segment: SegmentDict = {
        "id": 0,
        "start": 0.0,
        "end": 1.0,
        "text": "Hello world",
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
        ],
    }
    transcription: Transcription = {
        "text": "Hello world",
        "segments": [segment],
        "language": "en",
    }

    segments = segment_words(transcription, max_chars=100)

    # One segment should be created
    assert len(segments) == 1

    segment = segments[0]
    assert segment["start"] == 0.0
    assert segment["end"] == 1.0
    assert segment["text"] == "Hello world"
    assert len(segment["words"]) == 2
    assert segment["words"][0]["word"] == "Hello"
    assert segment["words"][1]["word"] == "world"
