import pytest

from autosubs.models.enums import TimingDistribution
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_segment() -> SubtitleSegment:
    """Provides a sample SubtitleSegment for testing."""
    words = [
        SubtitleWord(text="Hello", start=10.0, end=10.5),
        SubtitleWord(text="world", start=10.6, end=11.0),
        SubtitleWord(text="test", start=11.5, end=12.5),  # Note the end time
    ]
    return SubtitleSegment(words=words)


def test_segment_allows_empty_init() -> None:
    """Test that SubtitleSegment can be initialized with no words."""
    segment = SubtitleSegment(words=[])
    assert segment.start == 0.0
    assert segment.end == 0.0
    assert not segment.words


def test_segment_boundary_calculation(sample_segment: SubtitleSegment) -> None:
    """Test that start is the first start and end is the last end."""
    assert sample_segment.start == 10.0
    assert sample_segment.end == 12.5  # Max of all word ends


def test_add_word_optimized(sample_segment: SubtitleSegment) -> None:
    """Test that add_word correctly inserts and updates boundaries."""
    # Add to beginning
    sample_segment.add_word(SubtitleWord("First", 9.0, 9.5))
    assert sample_segment.start == 9.0
    assert sample_segment.words[0].text == "First"

    # Add to end
    sample_segment.add_word(SubtitleWord("Last", 13.0, 13.5))
    assert sample_segment.end == 13.5
    assert sample_segment.words[-1].text == "Last"


def test_remove_word_optimized(sample_segment: SubtitleSegment) -> None:
    """Test that remove_word only recalculates boundaries when necessary."""
    # Remove a middle word (no full recalc needed)
    middle_word = sample_segment.words[1]
    sample_segment.remove_word(middle_word)
    assert len(sample_segment.words) == 2
    assert sample_segment.start == 10.0
    assert sample_segment.end == 12.5

    # Remove the last boundary word (triggers full recalc)
    last_word = sample_segment.words[-1]
    sample_segment.remove_word(last_word)
    assert len(sample_segment.words) == 1
    assert sample_segment.end == 10.5  # Recalculated


def test_shift_by_optimized(sample_segment: SubtitleSegment) -> None:
    """Test that shift_by directly adds offsets."""
    sample_segment.shift_by(5.0)
    assert sample_segment.start == 15.0
    assert sample_segment.end == 17.5
    assert sample_segment.words[0].start == 15.0
    assert sample_segment.words[-1].end == 17.5


def test_resize_proportional(sample_segment: SubtitleSegment) -> None:
    """Test that resize correctly scales all internal words."""
    # Original duration = 2.5s. New duration = 5.0s (2x scale)
    sample_segment.resize(new_start=20.0, new_end=25.0)
    assert sample_segment.start == 20.0
    assert sample_segment.end == 25.0
    # First word was at start (10.0), now should be at new start (20.0)
    assert pytest.approx(sample_segment.words[0].start) == 20.0
    # Last word was at 11.5, which is (11.5-10.0)=1.5s into the segment.
    # New position should be 20.0 + 1.5*2 = 23.0
    assert pytest.approx(sample_segment.words[-1].start) == 23.0


def test_set_duration(sample_segment: SubtitleSegment) -> None:
    """Test the set_duration helper method."""
    # Anchor start
    sample_segment.set_duration(5.0, anchor="start")
    assert sample_segment.start == 10.0
    assert pytest.approx(sample_segment.end) == 15.0

    # Anchor end
    sample_segment.set_duration(1.0, anchor="end")
    assert pytest.approx(sample_segment.start) == 14.0
    assert sample_segment.end == 15.0


def test_merge_segments() -> None:
    """Test merging two segments."""
    seg1 = SubtitleSegment(words=[SubtitleWord("A", 1.0, 2.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord("B", 3.0, 4.0)])
    subs = Subtitles(segments=[seg1, seg2])
    subs.merge_segments(0, 1)
    assert len(subs.segments) == 1
    merged = subs.segments[0]
    assert merged.start == 1.0
    assert merged.end == 4.0
    assert len(merged.words) == 2


def test_split_segment() -> None:
    """Test splitting a segment."""
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
    assert len(subs.segments[0].words) == 1
    assert subs.segments[0].text == "A"
    assert len(subs.segments[1].words) == 2
    assert subs.segments[1].text == "B C"
    assert subs.segments[1].start == 3.0


def test_generate_word_timings_no_op() -> None:
    """Test that generation is a no-op on already detailed segments."""
    seg = SubtitleSegment(words=[SubtitleWord("A", 1, 2), SubtitleWord("B", 3, 4)])
    original_words = seg.words
    seg.generate_word_timings()
    assert seg.words == original_words


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
    assert seg.words[1].text == "BB"
    assert seg.words[2].text == "CCC"
    current_time = 1.0
    for i, word in enumerate(seg.words):
        assert pytest.approx(word.start) == current_time
        duration = word.end - word.start
        assert pytest.approx(duration) == expected_durations[i]
        current_time += duration
