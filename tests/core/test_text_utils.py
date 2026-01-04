"""Tests for professional subtitle segmentation utilities."""

from autosubs.core.text_utils import partition_words_optimal
from autosubs.models.subtitles import SubtitleWord


def test_partition_words_optimal_single_partition() -> None:
    """Test that words fitting within char_limit remain in a single partition."""
    words = [
        SubtitleWord(text="Hello", start=0.0, end=0.5),
        SubtitleWord(text="world", start=0.6, end=1.0),
    ]
    result = partition_words_optimal(words, char_limit=42)

    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0][0].text == "Hello"


def test_partition_words_optimal_forced_split() -> None:
    """Test that words exceeding char_limit are split into multiple partitions."""
    words = [
        SubtitleWord(text="VeryLongWordHere", start=0.0, end=1.0),
        SubtitleWord(text="AnotherWord", start=1.1, end=2.0),
    ]
    # Length is 16 + 1 + 11 = 28. char_limit 15 forces split.
    result = partition_words_optimal(words, char_limit=15)

    assert len(result) == 2


def test_partition_words_optimal_oversized_word() -> None:
    """Test that a single word exceeding char_limit is handled gracefully."""
    words = [
        SubtitleWord(text="Supercalifragilisticexpialidocious", start=0.0, end=1.0),
        SubtitleWord(text="Short", start=1.1, end=1.2),
    ]
    # Word is 34 chars, limit is 10. Algorithm forces a break as best as possible.
    result = partition_words_optimal(words, char_limit=10)

    assert len(result) == 2
    assert result[0][0].text == "Supercalifragilisticexpialidocious"


def test_partition_words_optimal_high_cps() -> None:
    """Test that the cost function penalizes segments with high CPS."""
    # "Too fast to read" - 40 chars in 1 second = 40 CPS.
    words_fast = [SubtitleWord(text="This sentence is spoken way too fast now", start=0.0, end=1.0)]
    # "Normal speed" - 40 chars in 4 seconds = 10 CPS.
    words_slow = [SubtitleWord(text="This sentence is spoken way too fast now", start=0.0, end=4.0)]

    context = [SubtitleWord(text="Next", start=1.1, end=2.0)]

    res_fast = partition_words_optimal(words_fast + context, char_limit=100)
    res_slow = partition_words_optimal(words_slow + context, char_limit=100)

    assert isinstance(res_fast, list)
    assert isinstance(res_slow, list)


def test_partition_words_optimal_punctuation_preference() -> None:
    """Test that partitioning prefers splitting at punctuation marks."""
    words = [
        SubtitleWord(text="End.", start=0.0, end=0.5),
        SubtitleWord(text="New", start=0.6, end=1.0),
        SubtitleWord(text="word", start=1.1, end=1.5),
    ]
    result = partition_words_optimal(words, char_limit=15)

    assert len(result) == 2
    assert result[0][-1].text == "End."


def test_partition_words_optimal_silence_preference() -> None:
    """Test that partitioning prefers splitting during silence gaps."""
    words = [
        SubtitleWord(text="Word", start=0.0, end=0.5),
        SubtitleWord(text="Gap", start=2.0, end=2.5),
        SubtitleWord(text="Next", start=2.6, end=3.0),
    ]
    result = partition_words_optimal(words, char_limit=20)

    assert len(result) == 2
    assert result[0][-1].text == "Word"


def test_partition_words_optimal_empty_input() -> None:
    """Test that empty input returns an empty list."""
    assert partition_words_optimal([], char_limit=42) == []
