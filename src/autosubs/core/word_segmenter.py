"""Module responsible for segmenting a word stream into discrete subtitle units."""

from logging import getLogger

from autosubs.core.text_utils import partition_words_optimal
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def _partition_to_segments(words: list[SubtitleWord], max_chars: int) -> list[SubtitleSegment]:
    """Applies optimal partitioning to words and returns SubtitleSegment objects."""
    if not words:
        return []

    partitions = partition_words_optimal(words, max_chars=max_chars)
    segments = []

    for group in partitions:
        segments.append(SubtitleSegment(words=group))

    return segments


def _combine_segments(segments: list[SubtitleSegment], max_lines: int, max_chars: int) -> list[SubtitleSegment]:
    """Groups potential word chunks and applies deterministic partitioning.

    Instead of using newlines, this refactor splits multi-line candidates
    into individual, perfectly timed segments.
    """
    if not segments:
        return []

    final_segments: list[SubtitleSegment] = []
    i = 0
    while i < len(segments):
        # Gather a group of candidate lines based on the requested max_lines limit
        group = segments[i : i + max_lines]
        all_words = [word for seg in group for word in seg.words]

        # Use the DP Partitioner to break the chunk into 1...N deterministic segments
        partitioned = _partition_to_segments(all_words, max_chars)
        final_segments.extend(partitioned)

        i += len(group)

    logger.info(f"Transformed {len(segments)} candidate blocks into {len(final_segments)} deterministic segments.")
    return final_segments


def segment_words(
    words: list[SubtitleWord],
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 2,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[SubtitleSegment]:
    """Segments word-level transcription data into subtitle segments.

    Args:
        words: The list of words to include.
        max_chars: Max character limit for any resulting segment.
        min_words: Min words per line before allowing a punctuation break.
        max_lines: How many 'lines' of spoken text to consider per group.
        break_chars: Punctuation forcing a candidate break.

    Returns:
        A list of SubtitleSegment objects.
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

        # Basic length heuristic for candidate creation
        current_text_len = sum(len(w.text) + 1 for w in current_chunk)

        if current_chunk and current_text_len + len(word_text) > max_chars:
            candidates.append(SubtitleSegment(words=current_chunk.copy()))
            current_chunk = []

        current_chunk.append(SubtitleWord(text=word_text, start=word_model.start, end=word_model.end))

        # Punctuation break check
        if word_text.endswith(break_chars) and len(current_chunk) >= min_words:
            candidates.append(SubtitleSegment(words=current_chunk.copy()))
            current_chunk = []

    if current_chunk:
        candidates.append(SubtitleSegment(words=current_chunk.copy()))

    # Apply the DP optimization pass
    return _combine_segments(candidates, max_lines, max_chars)
