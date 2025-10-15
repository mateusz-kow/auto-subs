from __future__ import annotations

import bisect
import logging
from dataclasses import dataclass, field

from autosubs.models.enums import TimingDistribution

logger = logging.getLogger(__name__)


@dataclass(eq=True)
class SubtitleWord:
    """Represents a single word with its text and timing."""

    text: str
    start: float
    end: float

    def __post_init__(self) -> None:
        """Validates the word's timestamps after initialization."""
        if self.start > self.end:
            raise ValueError(f"SubtitleWord has invalid timestamp: start ({self.start}) > end ({self.end})")

    def shift_by(self, offset: float) -> SubtitleWord:
        """Shifts the entire segment and all its words by a time offset.

        Returns:
            The segment itself, for method chaining.
        """
        self.start += offset
        self.end += offset

        return self


@dataclass(eq=True)
class SubtitleSegment:
    """Represents a segment of subtitles containing one or more words."""

    words: list[SubtitleWord]
    start: float = field(init=False)
    end: float = field(init=False)
    text_override: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Calculates start and end times after initialization."""
        self._recalculate_boundaries_full()

    def _recalculate_boundaries_full(self) -> None:
        """Performs a full recalculation of segment start and end times."""
        if not self.words:
            self.start = self.end = 0.0
            return

        self.words.sort(key=lambda w: w.start)
        self.start = self.words[0].start
        self.end = max(word.end for word in self.words)

    def add_word(self, word: SubtitleWord) -> SubtitleSegment:
        """Adds a word, keeping the list sorted and efficiently updating boundaries.

        Returns:
            The segment itself, for method chaining.
        """
        if not self.words:
            self.start, self.end = word.start, word.end
            self.words.append(word)
        else:
            self.start = min(self.start, word.start)
            self.end = max(self.end, word.end)
            bisect.insort_left(self.words, word, key=lambda w: w.start)
        return self

    def remove_word(self, word: SubtitleWord) -> None:
        """Removes a word, only recalculating boundaries if necessary."""
        try:
            is_boundary_word = (word.start == self.start) or (word.end == self.end)
            self.words.remove(word)
            if not self.words:
                self.start = self.end = 0.0
            elif is_boundary_word:
                self._recalculate_boundaries_full()
        except ValueError:
            return  # Word not in list; fail silently.

    def shift_by(self, offset: float) -> SubtitleSegment:
        """Shifts the entire segment and all its words by a time offset.

        Returns:
            The segment itself, for method chaining.
        """
        if not self.words:
            return self
        self.start += offset
        self.end += offset
        for word in self.words:
            word.shift_by(offset)

        return self

    def resize(self, new_start: float, new_end: float) -> SubtitleSegment:
        """Resizes the segment, proportionally scaling all word timestamps.

        Returns:
            The segment itself, for method chaining.
        """
        if new_start > new_end:
            raise ValueError("Start time cannot be after end time.")
        if not self.words:
            self.start, self.end = new_start, new_end
            return self

        old_duration = self.end - self.start
        new_duration = new_end - new_start
        scale = new_duration / old_duration if old_duration > 0 else 0.0

        for w in self.words:
            w.start = new_start + (w.start - self.start) * scale
            w.end = new_start + (w.end - self.start) * scale

        self.start, self.end = new_start, new_end
        return self

    def set_duration(self, new_duration: float, anchor: str = "start") -> SubtitleSegment:
        """Adjusts the segment's duration, keeping one end anchored.

        Args:
            new_duration: The target duration in seconds. Must be non-negative.
            anchor: The point to keep fixed ("start" or "end").

        Returns:
            The segment itself, for method chaining.
        """
        if new_duration < 0:
            raise ValueError("Duration cannot be negative.")
        if anchor == "start":
            self.resize(self.start, self.start + new_duration)
        elif anchor == "end":
            self.resize(self.end - new_duration, self.end)
        else:
            raise ValueError("Anchor must be 'start' or 'end'.")
        return self

    def generate_word_timings(self, strategy: TimingDistribution = TimingDistribution.BY_CHAR_COUNT) -> SubtitleSegment:
        """For a segment with a single synthetic word, splits it into multiple words
        and heuristically generates word-level timestamps.

        This is a no-op if the segment already has more than one word.

        Args:
            strategy: The method for distributing the segment's total duration.

        Returns:
            The segment itself, for method chaining.
        """
        if len(self.words) != 1:
            return self  # Already has word timings or is empty

        synthetic_word = self.words[0]
        words_in_text = synthetic_word.text.strip().split()
        if not words_in_text:
            self.words = []
            self.start = self.end = 0.0
            return self

        total_duration = self.end - self.start
        new_words: list[SubtitleWord] = []
        current_time = self.start

        if strategy == TimingDistribution.BY_WORD_COUNT:
            duration_per_word = total_duration / len(words_in_text)
            for word_text in words_in_text:
                new_words.append(
                    SubtitleWord(
                        text=word_text,
                        start=current_time,
                        end=current_time + duration_per_word,
                    )
                )
                current_time += duration_per_word
        elif strategy == TimingDistribution.BY_CHAR_COUNT:
            total_chars = sum(len(w) for w in words_in_text)
            if total_chars == 0:
                return self  # Avoid division by zero
            for word_text in words_in_text:
                char_proportion = len(word_text) / total_chars
                word_duration = total_duration * char_proportion
                new_words.append(
                    SubtitleWord(
                        text=word_text,
                        start=current_time,
                        end=current_time + word_duration,
                    )
                )
                current_time += word_duration

        self.words = new_words
        return self

    def _split_at_word_index(self, index: int) -> tuple[SubtitleSegment, SubtitleSegment]:
        """Splits the segment into two at a given word index."""
        if not 0 < index < len(self.words):
            raise IndexError("Split index must be within the bounds of the word list.")
        part1 = SubtitleSegment(words=self.words[:index])
        part2 = SubtitleSegment(words=self.words[index:])
        return part1, part2

    def _merge_with(self, other: SubtitleSegment) -> None:
        """Merges another segment's words into this one."""
        if not other.words:
            return
        if not self.words:
            self.words = other.words
            self._recalculate_boundaries_full()
            return

        self.words.extend(other.words)
        self.start = min(self.start, other.start)
        self.end = max(self.end, other.end)
        self.words.sort(key=lambda w: w.start)

    @property
    def text(self) -> str:
        """Returns the segment text.

        If `text_override` is set, it returns that value. Otherwise, it
        concatenates the words with spaces.
        """
        if self.text_override is not None:
            return self.text_override
        return " ".join(word.text for word in self.words)


@dataclass(eq=True)
class Subtitles:
    """Represents a collection of subtitle segments for a piece of media."""

    segments: list[SubtitleSegment]

    def __post_init__(self) -> None:
        """Sorts segments and checks for overlaps after initialization."""
        self.segments.sort(key=lambda s: s.start)
        self._validate_overlaps()

    def _validate_overlaps(self) -> None:
        """Checks for any overlapping segments and logs a warning."""
        for i in range(len(self.segments) - 1):
            current_seg = self.segments[i]
            next_seg = self.segments[i + 1]
            if current_seg.end > next_seg.start:
                logger.warning(
                    f"Overlap detected: Segment ending at {current_seg.end:.3f}s overlaps with "
                    f"segment starting at {next_seg.start:.3f}s."
                )

    def remove_segment(self, index: int) -> SubtitleSegment:
        """Removes and returns a segment at a given index."""
        return self.segments.pop(index)

    def merge_segments(self, index1: int, index2: int) -> SubtitleSegment:
        """Merges two segments into one, returning the merged segment."""
        first_index = min(index1, index2)
        second_index = max(index1, index2)

        segment1 = self.segments[first_index]
        segment2 = self.segments[second_index]

        segment1._merge_with(segment2)
        self.remove_segment(second_index)
        return segment1

    def split_segment_at_word(self, segment_index: int, word_index: int) -> tuple[SubtitleSegment, SubtitleSegment]:
        """Splits a single segment into two at a specific word.

        Returns:
            A tuple containing the two new segments.
        """
        segment_to_split = self.segments[segment_index]
        new_seg1, new_seg2 = segment_to_split._split_at_word_index(word_index)
        self.segments[segment_index : segment_index + 1] = [new_seg1, new_seg2]
        return new_seg1, new_seg2

    @property
    def text(self) -> str:
        """Returns the segment text by concatenating the words."""
        return "\n".join(segment.text for segment in self.segments)
