import pytest

from autosubs.models.enums import TimingDistribution
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_segment() -> SubtitleSegment:
    """Provides a sample SubtitleSegment for testing."""
    words = [
        SubtitleWord(text="Hello", start=10.0, end=10.5),
        SubtitleWord(text="world", start=10.6, end=11.0),
        SubtitleWord(text="test", start=11.5, end=12.5),
    ]
    return SubtitleSegment(words=words)


@pytest.fixture
def empty_segment() -> SubtitleSegment:
    """Provides an empty SubtitleSegment for testing."""
    return SubtitleSegment(words=[])


def test_segment_boundary_calculation(sample_segment: SubtitleSegment) -> None:
    """Test that start is the first start and end is the last end."""
    assert sample_segment.start == pytest.approx(10.0)
    assert sample_segment.end == pytest.approx(12.5)


def test_add_word_to_empty_segment(empty_segment: SubtitleSegment) -> None:
    """Test adding a word to an empty segment correctly sets boundaries."""
    word = SubtitleWord("First", 9.0, 9.5)
    empty_segment.add_word(word)
    assert empty_segment.start == pytest.approx(9.0)
    assert empty_segment.end == pytest.approx(9.5)
    assert empty_segment.words == [word]


def test_add_word_maintains_order_and_updates_boundaries(
    sample_segment: SubtitleSegment,
) -> None:
    """Test adding a word preserves sorting and correctly updates boundaries."""
    # Word that should be inserted in the middle
    middle_word = SubtitleWord("middle", 11.1, 11.4)
    sample_segment.add_word(middle_word)
    assert [w.start for w in sample_segment.words] == pytest.approx([10.0, 10.6, 11.1, 11.5])
    assert sample_segment.start == pytest.approx(10.0)  # Should not change
    assert sample_segment.end == pytest.approx(12.5)  # Should not change

    # Word that should become the new start
    first_word = SubtitleWord("first", 9.0, 9.5)
    sample_segment.add_word(first_word)
    assert [w.start for w in sample_segment.words] == pytest.approx([9.0, 10.0, 10.6, 11.1, 11.5])
    assert sample_segment.start == pytest.approx(9.0)  # Should update

    # Word that should become the new end
    last_word = SubtitleWord("last", 13.0, 13.5)
    sample_segment.add_word(last_word)
    assert sample_segment.end == pytest.approx(13.5)  # Should update


def test_remove_last_word_from_segment() -> None:
    """Test that removing the last word resets the segment's state."""
    word = SubtitleWord("Only", 1.0, 2.0)
    segment = SubtitleSegment(words=[word])
    segment.remove_word(word)
    assert not segment.words
    assert segment.start == pytest.approx(0.0)
    assert segment.end == pytest.approx(0.0)


def test_remove_boundary_word_recalculates_segment_boundaries() -> None:
    """Test removing a boundary word forces recalculation of start/end times."""
    word1 = SubtitleWord("A", 1.0, 2.0)
    word2 = SubtitleWord("B", 2.5, 3.0)
    word3 = SubtitleWord("C", 3.5, 4.5)
    segment = SubtitleSegment(words=[word1, word2, word3])

    assert segment.start == pytest.approx(1.0)
    assert segment.end == pytest.approx(4.5)

    # Remove the first word, forcing a start time recalculation

    segment.remove_word(word1)
    assert segment.start == pytest.approx(2.5)
    assert segment.end == pytest.approx(4.5)

    # Remove the (new) last word, forcing an end time recalculation
    segment.remove_word(word3)
    assert segment.start == pytest.approx(2.5)
    assert segment.end == pytest.approx(3.0)


def test_remove_non_existent_word(sample_segment: SubtitleSegment) -> None:
    """Test that attempting to remove a word not in the list fails silently."""
    non_existent_word = SubtitleWord("NotInList", 0.0, 1.0)
    original_words = sample_segment.words[:]
    sample_segment.remove_word(non_existent_word)
    assert sample_segment.words == original_words


def test_shift_by(sample_segment: SubtitleSegment) -> None:
    """Test shifting a segment updates its and all its words' timestamps."""
    original_starts = [w.start for w in sample_segment.words]
    original_ends = [w.end for w in sample_segment.words]
    offset = 5.5

    sample_segment.shift_by(offset)

    assert sample_segment.start == pytest.approx(10.0 + offset)
    assert sample_segment.end == pytest.approx(12.5 + offset)
    for i, word in enumerate(sample_segment.words):
        assert word.start == pytest.approx(original_starts[i] + offset)
        assert word.end == pytest.approx(original_ends[i] + offset)


def test_shift_by_on_empty_segment(empty_segment: SubtitleSegment) -> None:
    """Test that shifting an empty segment is a no-op."""
    empty_segment.shift_by(10.0)
    assert empty_segment.start == pytest.approx(0.0)
    assert empty_segment.end == pytest.approx(0.0)
    assert not empty_segment.words


def test_word_linear_sync() -> None:
    """Test linear_sync on a single SubtitleWord."""
    word = SubtitleWord("test", start=50.0, end=51.0)
    # Scenario: A 100s clip is stretched to 200s and shifted forward by 10s.
    # old: 0-100, new: 10-210. Scale = 2, Offset = 10.
    # new_start = 50 * 2 + 10 = 110
    # new_end = 51 * 2 + 10 = 112
    word.linear_sync(old_start=0.0, old_end=100.0, new_start=10.0, new_end=210.0)
    assert word.start == pytest.approx(110.0)
    assert word.end == pytest.approx(112.0)


def test_word_linear_sync_zero_division() -> None:
    """Test that linear_sync raises ValueError if old points are identical."""
    word = SubtitleWord("test", 1.0, 2.0)
    with pytest.raises(ValueError, match="Original start and end times cannot be the same"):
        word.linear_sync(10.0, 10.0, 20.0, 30.0)


def test_segment_linear_sync(sample_segment: SubtitleSegment) -> None:
    """Test that linear_sync on a segment cascades to its words."""
    # old: 10-12.5, new: 20-25. Scale = 2, Offset = 20 - (10*2) = 0.
    sample_segment.linear_sync(old_start=10.0, old_end=12.5, new_start=20.0, new_end=25.0)
    assert sample_segment.start == pytest.approx(20.0)
    assert sample_segment.end == pytest.approx(25.0)
    assert sample_segment.words[0].start == pytest.approx(20.0)
    assert sample_segment.words[0].end == pytest.approx(21.0)
    assert sample_segment.words[1].start == pytest.approx(21.2)
    assert sample_segment.words[1].end == pytest.approx(22.0)
    assert sample_segment.words[2].start == pytest.approx(23.0)
    assert sample_segment.words[2].end == pytest.approx(25.0)


def test_subtitles_linear_sync_drift_correction() -> None:
    """Test linear_sync on a full Subtitles object to correct a 1-second drift over an hour."""
    segments = [
        SubtitleSegment(words=[SubtitleWord("start", 0.0, 1.0)]),
        SubtitleSegment(words=[SubtitleWord("middle", 1799.5, 1800.5)]),
        SubtitleSegment(words=[SubtitleWord("end", 3599.0, 3600.0)]),
    ]
    subs = Subtitles(segments=segments)

    # A 1-hour video (3600s) has a 1s drift. The end is at 3601s instead.
    subs.linear_sync(old_start=0.0, old_end=3600.0, new_start=0.0, new_end=3601.0)

    # Scale factor is 3601/3600 with zero offset
    assert subs.segments[0].start == pytest.approx(0.0)
    assert subs.segments[0].end == pytest.approx(1.0 * 3601.0 / 3600.0)

    # Middle point should be shifted by ~0.5s (1799.5 * 3601/3600 ≈ 1800.0)
    assert subs.segments[1].start == pytest.approx(1799.5 * 3601.0 / 3600.0)

    assert subs.segments[1].end == pytest.approx(1800.5 * 3601.0 / 3600.0)

    assert subs.segments[2].start == pytest.approx(3599.0 * 3601.0 / 3600.0)
    assert subs.segments[2].end == pytest.approx(3601.0)


def test_segment_linear_sync_on_empty_segment(empty_segment: SubtitleSegment) -> None:
    """Test that sync on an empty segment is a no-op."""
    empty_segment.linear_sync(0.0, 1.0, 0.0, 2.0)
    assert empty_segment.start == pytest.approx(0.0)
    assert empty_segment.end == pytest.approx(0.0)
    assert not empty_segment.words


def test_resize_proportional(sample_segment: SubtitleSegment) -> None:
    """Test that resize correctly scales all internal words."""
    sample_segment.resize(new_start=20.0, new_end=25.0)
    assert sample_segment.start == pytest.approx(20.0)
    assert sample_segment.end == pytest.approx(25.0)
    assert sample_segment.words[0].start == pytest.approx(20.0)
    assert sample_segment.words[-1].start == pytest.approx(23.0)


def test_resize_empty_segment(empty_segment: SubtitleSegment) -> None:
    """Test that resizing an empty segment sets its boundaries."""
    empty_segment.resize(10.0, 20.0)
    assert empty_segment.start == pytest.approx(10.0)
    assert empty_segment.end == pytest.approx(20.0)
    assert not empty_segment.words


def test_resize_with_invalid_timestamps(sample_segment: SubtitleSegment) -> None:
    """Test that resizing with start > end raises a ValueError."""
    with pytest.raises(ValueError, match="Start time cannot be after end time"):
        sample_segment.resize(10.0, 5.0)


def test_set_duration(sample_segment: SubtitleSegment) -> None:
    """Test the set_duration helper method with valid anchors."""
    sample_segment.set_duration(5.0, anchor="start")
    assert sample_segment.start == pytest.approx(10.0)
    assert sample_segment.end == pytest.approx(15.0)

    sample_segment.set_duration(1.0, anchor="end")
    assert sample_segment.start == pytest.approx(14.0)
    assert sample_segment.end == pytest.approx(15.0)


def test_set_duration_negative(sample_segment: SubtitleSegment) -> None:
    """Test that setting a negative duration raises a ValueError."""
    with pytest.raises(ValueError, match="Duration cannot be negative"):
        sample_segment.set_duration(-1.0)


def test_set_duration_invalid_anchor(sample_segment: SubtitleSegment) -> None:
    """Test that setting duration with an invalid anchor raises a ValueError."""
    with pytest.raises(ValueError, match="Anchor must be 'start' or 'end'"):
        sample_segment.set_duration(1.0, anchor="middle")


def test_merge_segments() -> None:
    """Test merging two non-empty segments."""
    seg1 = SubtitleSegment(words=[SubtitleWord("A", 1.0, 2.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord("B", 3.0, 4.0)])
    subs = Subtitles(segments=[seg1, seg2])
    subs.merge_segments(0, 1)
    assert len(subs.segments) == 1
    merged = subs.segments[0]
    assert merged.start == pytest.approx(1.0)
    assert merged.end == pytest.approx(4.0)
    assert len(merged.words) == 2


def test_merge_into_empty_segment() -> None:
    """Test merging a non-empty segment into an empty one."""
    seg1 = SubtitleSegment(words=[])
    seg2 = SubtitleSegment(words=[SubtitleWord("B", 3.0, 4.0)])
    subs = Subtitles(segments=[seg1, seg2])
    subs.merge_segments(0, 1)
    assert len(subs.segments) == 1
    merged = subs.segments[0]
    assert merged.start == pytest.approx(3.0)
    assert merged.end == pytest.approx(4.0)
    assert len(merged.words) == 1


def test_merge_with_empty_segment() -> None:
    """Test that merging an empty segment into a non-empty one is a no-op."""
    seg1 = SubtitleSegment(words=[SubtitleWord("A", 1.0, 2.0)])
    seg2 = SubtitleSegment(words=[])
    subs = Subtitles(segments=[seg1, seg2])
    original_words = seg1.words[:]
    subs.merge_segments(0, 1)
    assert len(subs.segments) == 1
    assert subs.segments[0].words == original_words


def test_split_segment() -> None:
    """Test splitting a segment at a valid word index."""
    seg = SubtitleSegment(
        words=[
            SubtitleWord("A", 1, 2),
            SubtitleWord("B", 3, 4),
            SubtitleWord("C", 5, 6),
        ]
    )
    subs = Subtitles(segments=[seg])
    subs.split_segment_at_word(0, 1)
    assert len(subs.segments) == 2
    assert subs.segments[0].text == "A"
    assert subs.segments[1].text == "B C"
    assert subs.segments[1].start == pytest.approx(3.0)


@pytest.mark.parametrize("invalid_index", [0, 3])
def test_split_segment_at_word_invalid_index(invalid_index: int) -> None:
    """Test splitting a segment at an out-of-bounds index raises IndexError."""
    seg = SubtitleSegment(
        words=[
            SubtitleWord("A", 1, 2),
            SubtitleWord("B", 3, 4),
            SubtitleWord("C", 5, 6),
        ]
    )
    subs = Subtitles(segments=[seg])
    with pytest.raises(IndexError, match="Split index must be within the bounds"):
        subs.split_segment_at_word(0, invalid_index)


def test_generate_word_timings_no_op(sample_segment: SubtitleSegment) -> None:
    """Test that generation is a no-op on already detailed segments."""
    original_words = sample_segment.words[:]
    sample_segment.generate_word_timings()
    assert sample_segment.words == original_words


def test_generate_word_timings_with_zero_chars() -> None:
    """Test word timing generation on a synthetic word with no characters."""
    segment = SubtitleSegment(words=[SubtitleWord(" ", 1.0, 4.0)])
    segment.generate_word_timings(strategy=TimingDistribution.BY_CHAR_COUNT)
    assert not segment.words


def test_generate_word_timings_with_empty_text_avoids_division_by_zero() -> None:
    """Test word timing generation on a synthetic word with empty text.

    This covers the `if total_chars == 0` check by first hitting the `if not words_in_text`
    check, which is the only way to produce a zero-character count from a split string.
    """
    segment = SubtitleSegment(words=[SubtitleWord("", 1.0, 4.0)])
    # The `strip()` on "" results in "", and `"".split()` results in `[]`.
    # This is caught by `if not words_in_text`, preventing division by zero.
    segment.generate_word_timings(strategy=TimingDistribution.BY_CHAR_COUNT)
    assert not segment.words


@pytest.mark.parametrize(
    "strategy, expected_durations",
    [
        (TimingDistribution.BY_WORD_COUNT, [1.0, 1.0, 1.0]),
        (TimingDistribution.BY_CHAR_COUNT, [0.5, 1.0, 1.5]),
    ],
)
def test_generate_word_timings_strategies(strategy: TimingDistribution, expected_durations: list[float]) -> None:
    """Test both word timing generation strategies."""
    seg = SubtitleSegment(words=[SubtitleWord("A BB CCC", 1.0, 4.0)])
    seg.generate_word_timings(strategy=strategy)
    assert len(seg.words) == 3
    assert seg.words[0].text == "A"
    current_time = 1.0
    for i, word in enumerate(seg.words):
        assert word.start == pytest.approx(current_time)
        duration = word.end - word.start
        assert duration == pytest.approx(expected_durations[i])
        current_time += duration


def test_complex_editing_sequence_maintains_integrity() -> None:
    """
    Performs a chain of editing operations and validates the final state.
    Any method that modifies segments or words should appear here to ensure the overall integrity

    This test ensures that after multiple manipulations (merge, split, add, shift),
    the core invariants of the Subtitles and SubtitleSegment models hold true:
    1. The main segments list is sorted by start time.
    2. Each segment's word list is sorted by start time.
    3. Each segment's start/end time correctly reflects its words' boundaries.
    4. All words have valid start <= end timestamps.
    """
    seg_a = SubtitleSegment(words=[SubtitleWord("A", 1.0, 2.0)])
    seg_b = SubtitleSegment(
        words=[
            SubtitleWord("B1", 10.0, 10.5),
            SubtitleWord("B2", 10.6, 11.0),
        ]
    )
    seg_c = SubtitleSegment(
        words=[
            SubtitleWord("C1", 20.0, 20.2),
            SubtitleWord("C2", 20.3, 20.5),
            SubtitleWord("C3", 20.6, 21.0),
        ]
    )
    subs = Subtitles(segments=[seg_a, seg_b, seg_c])

    subs.merge_segments(0, 1)
    subs.split_segment_at_word(segment_index=1, word_index=1)

    word_to_add = SubtitleWord("New", 0.5, 0.9)
    subs.segments[0].add_word(word_to_add)
    subs.segments[2].shift_by(5.0)

    subs = Subtitles(segments=subs.segments)

    segment_starts = [s.start for s in subs.segments]
    assert segment_starts == sorted(segment_starts), "Segments are not sorted by start time."

    for segment in subs.segments:
        assert segment.words, "A segment should not be empty after these operations."
        assert segment.start == segment.words[0].start, "Segment start time does not match its first word."
        assert segment.end == segment.words[-1].end, "Segment end time does not match its last word."

        word_starts = [w.start for w in segment.words]
        assert word_starts == sorted(word_starts), "Words within a segment are not sorted."

        # Store state, call recalculation, and assert that nothing changed.
        original_start = segment.start
        original_end = segment.end
        original_words = segment.words[:]
        segment._recalculate_boundaries_full()
        assert segment.start == original_start, "Recalculation changed the start time unexpectedly."
        assert segment.end == original_end, "Recalculation changed the end time unexpectedly."
        assert segment.words == original_words, "Recalculation changed the words list unexpectedly."

        for word in segment.words:
            assert word.start <= word.end, f"Word '{word.text}' has an invalid timestamp."

    assert len(subs.segments) == 3
    assert subs.segments[0].text == "New A B1 B2"
    assert subs.segments[1].text == "C1"
    assert subs.segments[2].text == "C2 C3"
    assert subs.segments[2].start == pytest.approx(25.3)


def test_generate_word_timings_handles_whitespace_only_word() -> None:
    """Test that a word with only whitespace is correctly handled, resulting in an empty segment."""
    segment = SubtitleSegment(words=[SubtitleWord(" \t ", 5.0, 10.0)])
    segment.generate_word_timings()
    assert not segment.words
    assert segment.start == pytest.approx(0.0)
    assert segment.end == pytest.approx(0.0)


def test_transform_framerate() -> None:
    """Test framerate conversion on a Subtitles object."""
    segments = [
        SubtitleSegment(words=[SubtitleWord("A", 12.0, 13.0)]),
        SubtitleSegment(words=[SubtitleWord("B", 24.0, 25.0)]),
    ]
    subs = Subtitles(segments=segments)

    # 24fps -> 25fps: speed-up, timestamps should decrease.
    # Scale factor = 24 / 25 = 0.96
    subs.transform_framerate(source_fps=24.0, target_fps=25.0)

    assert subs.segments[0].start == pytest.approx(12.0 * 0.96)
    assert subs.segments[0].end == pytest.approx(13.0 * 0.96)
    assert subs.segments[1].start == pytest.approx(24.0 * 0.96)
    assert subs.segments[1].end == pytest.approx(25.0 * 0.96)


def test_transform_framerate_common_conversions() -> None:
    """Test common framerate conversions (e.g., 23.976 -> 25)."""
    segments = [SubtitleSegment(words=[SubtitleWord("test", 100.0, 101.0)])]
    subs = Subtitles(segments=segments)

    # 23.976 -> 25.0 (PAL speed-up)
    scale_factor = 23.976 / 25.0
    subs.transform_framerate(source_fps=23.976, target_fps=25.0)
    assert subs.segments[0].start == pytest.approx(100.0 * scale_factor)
    assert subs.segments[0].end == pytest.approx(101.0 * scale_factor)

    # Reset
    subs = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("test", 100.0, 101.0)])])

    # 29.97 -> 30.0
    scale_factor = 29.97 / 30.0
    subs.transform_framerate(source_fps=29.97, target_fps=30.0)
    assert subs.segments[0].start == pytest.approx(100.0 * scale_factor)
    assert subs.segments[0].end == pytest.approx(101.0 * scale_factor)


def test_transform_framerate_validation() -> None:
    """Test that transform_framerate validates its inputs."""
    subs = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("A", 1.0, 2.0)])])
    with pytest.raises(ValueError, match="Source and target framerates must be positive"):
        subs.transform_framerate(-24.0, 25.0)
    with pytest.raises(ValueError, match="Source and target framerates must be positive"):
        subs.transform_framerate(24.0, 0.0)
    with pytest.raises(ValueError, match="Source and target framerates cannot be the same"):
        subs.transform_framerate(25.0, 25.0)


def test_transform_framerate_empty_subtitles() -> None:
    """Test that framerate conversion on empty subtitles is a no-op."""
    subs = Subtitles(segments=[])
    # Should not raise any error
    result = subs.transform_framerate(24.0, 25.0)
    assert not result.segments
    assert result is subs
