"""Module responsible for segmenting a word stream into discrete subtitle units."""

from logging import getLogger

from autosubs.core.text_utils import partition_words_optimal
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def _create_optimal_segments(words: list[SubtitleWord], max_chars: int) -> list[SubtitleSegment]:
    """Applies optimal partitioning to words and returns SubtitleSegment objects."""
    if not words:
        return []

    partitions = partition_words_optimal(words, max_chars=max_chars)
    return [SubtitleSegment(words=group) for group in partitions]


def _refine_segment_boundaries(
    segments: list[SubtitleSegment], max_lines: int, max_chars: int
) -> list[SubtitleSegment]:
    """Optimizes segmentation by re-partitioning grouped word chunks.

    Instead of using internal newlines, this process identifies optimal split
    points to produce discrete, perfectly timed segments.
    """
    if not segments:
        return []

    final_segments: list[SubtitleSegment] = []
    i = 0
    while i < len(segments):
        group = segments[i : i + max_lines]
        all_words = [word for seg in group for word in seg.words]

        # Partition the word chunk into deterministic timed segments.
        partitioned = _create_optimal_segments(all_words, max_chars)
        final_segments.extend(partitioned)

        i += len(group)

    logger.info(f"Optimized {len(segments)} blocks into {len(final_segments)} deterministic timed segments.")
    return final_segments


def segment_words(
    words: list[SubtitleWord],
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 2,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[SubtitleSegment]:
    """Segments word-level transcription data into discrete subtitle segments.

    Args:
        words: The list of words to include.
        max_chars: Max character limit for any resulting segment.
        min_words: Min words per block before allowing a punctuation break.
        max_lines: How many 'logical lines' to group for optimization.
        break_chars: Punctuation forcing a candidate break.

    Returns:
        A list of optimally segmented SubtitleSegment objects.
    """
    logger.info("Starting deterministic word segmentation...")

    if not words:
        return []

    candidates: list[SubtitleSegment] = []
    current_chunk: list[SubtitleWord] = []

    for word_model in words:
        word_text = word_model.text.strip()
        if not word_text:
            continue

        # Simple length check for preliminary candidate grouping.
        current_text_len = sum(len(w.text) + 1 for w in current_chunk)

        if current_chunk and current_text_len + len(word_text) > max_chars:
            candidates.append(SubtitleSegment(words=current_chunk.copy()))
            current_chunk = []

        current_chunk.append(SubtitleWord(text=word_text, start=word_model.start, end=word_model.end))

        # Check for natural punctuation breaks.
        if word_text.endswith(break_chars) and len(current_chunk) >= min_words:
            candidates.append(SubtitleSegment(words=current_chunk.copy()))
            current_chunk = []

    if current_chunk:
        candidates.append(SubtitleSegment(words=current_chunk.copy()))

    # Optimize and refine candidates into final timed segments.
    return _refine_segment_boundaries(candidates, max_lines, max_chars)
