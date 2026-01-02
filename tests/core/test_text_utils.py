"""Tests for deterministic subtitle segmentation utilities."""

from autosubs.core.text_utils import balance_lines_with_timing, partition_words_optimal
from autosubs.models.subtitles import SubtitleWord


def test_partition_words_optimal_basic_fit() -> None:
    """Test that words fitting within max_chars remain in a single partition."""
    words = [
        SubtitleWord(text="Hello", start=0.0, end=0.5),
        SubtitleWord(text="world", start=0.6, end=1.0),
    ]
    result = partition_words_optimal(words, max_chars=42)

    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0][0].text == "Hello"


def test_partition_words_optimal_forced_split() -> None:
    """Test that words exceeding max_chars are split into multiple partitions."""
    words = [
        SubtitleWord(text="VeryLongWordHere", start=0.0, end=1.0),
        SubtitleWord(text="AnotherWord", start=1.1, end=2.0),
    ]
    # Length is 16 + 1 + 11 = 28. Max 15 forces split.
    result = partition_words_optimal(words, max_chars=15)

    assert len(result) == 2


def test_partition_words_optimal_punctuation_preference() -> None:
    """Test that partitioning prefers splitting at punctuation marks."""
    # Text: "End. New word" (13 chars). Fits in 15 chars.
    # Punctuation bonus should trigger split at "End."
    words = [
        SubtitleWord(text="End.", start=0.0, end=0.5),
        SubtitleWord(text="New", start=0.6, end=1.0),
        SubtitleWord(text="word", start=1.1, end=1.5),
    ]
    result = partition_words_optimal(words, max_chars=15)

    assert len(result) == 2
    assert result[0][-1].text == "End."


def test_partition_words_optimal_silence_preference() -> None:
    """Test that partitioning prefers splitting during silence gaps."""
    # Text: "Word Gap Next" (13 chars). Fits in 20 chars.
    # Large 1.5s gap should trigger split.
    words = [
        SubtitleWord(text="Word", start=0.0, end=0.5),
        SubtitleWord(text="Gap", start=2.0, end=2.5),
        SubtitleWord(text="Next", start=2.6, end=3.0),
    ]
    result = partition_words_optimal(words, max_chars=20)

    assert len(result) == 2
    assert result[0][-1].text == "Word"


def test_balance_lines_with_timing_wraps_partitioner() -> None:
    """Test that balance_lines_with_timing correctly wraps the DP logic."""
    words = [SubtitleWord(text="Test", start=0.0, end=1.0)]
    result = balance_lines_with_timing(words, max_chars=42)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0][0].text == "Test"


def test_partition_words_optimal_empty_input() -> None:
    """Test that empty input returns an empty list."""
    assert partition_words_optimal([], max_chars=42) == []
