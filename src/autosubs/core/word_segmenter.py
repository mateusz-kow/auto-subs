from logging import getLogger

from autosubs.core.text_utils import balance_lines_with_timing
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def _balance_segment_lines(words: list[SubtitleWord], max_chars: int) -> str | None:
    r"""Balance lines within a segment using temporal cost function.

    Args:
        words: The words in the segment.
        max_chars: The maximum number of characters per line.

    Returns:
        The balanced text with \N line breaks, or None if no balancing needed.
    """
    if not words:
        return None

    # Use the temporal balancing algorithm
    balanced_lines = balance_lines_with_timing(words, max_width_chars=max_chars)

    # If only one line, no balancing needed
    if len(balanced_lines) == 1:
        return None

    # Convert word lists to text with \\N line breaks
    text_lines = [" ".join(word.text for word in line) for line in balanced_lines]
    return "\\N".join(text_lines)


def _combine_segments(segments: list[SubtitleSegment], max_lines: int, max_chars: int) -> list[SubtitleSegment]:
    """Combines single-line segments into multi-line segments with balanced line breaks.

    Args:
        segments: The list of segments to combine.
        max_lines: The maximum number of lines to combine into a single segment.
        max_chars: The maximum number of characters per line.

    Returns:
        The combined segments with balanced line breaks applied.
    """
    if not segments or max_lines <= 1:
        return segments

    combined: list[SubtitleSegment] = []
    i = 0
    while i < len(segments):
        group = segments[i : i + max_lines]
        all_words = [word for seg in group for word in seg.words]

        new_segment = SubtitleSegment(words=all_words)

        # Apply temporal balancing to the combined segment
        balanced_text = _balance_segment_lines(all_words, max_chars)
        if balanced_text:
            new_segment.text_override = balanced_text
        else:
            # Fallback to simple newline joining if no balancing
            new_segment.text_override = "\n".join(seg.text for seg in group)

        combined.append(new_segment)
        i += len(group)

    logger.info(f"Combined {len(segments)} lines into {len(combined)} multi-line segments with balanced breaks.")
    return combined


def segment_words(
    words: list[SubtitleWord],
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 2,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[SubtitleSegment]:
    """Segments word-level transcription data into subtitle lines.

    Args:
        words: The list of words to include in the subtitles.
        max_chars: The maximum number of characters desired per subtitle line.
        min_words: The minimum number of words for a line to be broken by punctuation.
        max_lines: The maximum number of lines to combine into a single segment.
        break_chars: Punctuation that should force a line break.

    Returns:
        A list of SubtitleSegment objects.
    """
    logger.info("Starting word segmentation...")

    if not words:
        return []

    lines: list[SubtitleSegment] = []
    current_line_words: list[SubtitleWord] = []

    for word_model in words:
        word_text = word_model.text.strip()
        if not word_text:
            continue

        current_text = " ".join(w.text for w in current_line_words)

        if current_line_words and len(current_text) + 1 + len(word_text) > max_chars:
            lines.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []  # Reset for a new line

        current_line_words.append(SubtitleWord(text=word_text, start=word_model.start, end=word_model.end))

        # If the newly added word ends with a break character, this line might be done.
        if word_text.endswith(break_chars) and len(current_line_words) >= min_words:
            lines.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []

    if current_line_words:
        lines.append(SubtitleSegment(words=current_line_words.copy()))

    logger.info(f"Segmentation created {len(lines)} raw subtitle lines.")

    final_segments = _combine_segments(lines, max_lines, max_chars)
    logger.info(f"Segmentation complete: {len(final_segments)} final subtitle segments created.")
    return final_segments
