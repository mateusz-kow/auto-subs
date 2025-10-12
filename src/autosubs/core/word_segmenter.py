from logging import getLogger

from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def _combine_segments(segments: list[SubtitleSegment], max_lines: int) -> list[SubtitleSegment]:
    """Combines single-line segments into multi-line segments up to a limit."""
    if not segments or max_lines <= 1:
        return segments

    combined: list[SubtitleSegment] = []
    i = 0
    while i < len(segments):
        group = segments[i : i + max_lines]
        all_words = [word for seg in group for word in seg.words]

        new_segment = SubtitleSegment(words=all_words)
        new_segment.text_override = "\n".join(seg.text for seg in group)

        combined.append(new_segment)
        i += len(group)

    logger.info(f"Combined {len(segments)} lines into {len(combined)} multi-line segments.")
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
        # The +1 is for the space character.
        if current_line_words and len(current_text) + 1 + len(word_text) > max_chars:
            lines.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []  # Reset for a new line

        # Add the word to the (potentially new) line.
        current_line_words.append(SubtitleWord(text=word_text, start=word_model.start, end=word_model.end))

        # If the newly added word ends with a break character, this line might be done.
        if word_text.endswith(break_chars) and len(current_line_words) >= min_words:
            lines.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []

    if current_line_words:
        lines.append(SubtitleSegment(words=current_line_words.copy()))

    logger.info(f"Segmentation created {len(lines)} raw subtitle lines.")

    final_segments = _combine_segments(lines, max_lines)
    logger.info(f"Segmentation complete: {len(final_segments)} final subtitle segments created.")
    return final_segments
