from logging import getLogger

from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def segment_words(
    words: list[SubtitleWord],
    max_chars: int = 35,
    min_words: int = 1,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[SubtitleSegment]:
    """Segments word-level transcription data into subtitle lines.

    Args:
        words: The list of words to include in the subtitles.
        max_chars: The maximum number of characters desired per subtitle line.
        min_words: The minimum number of words for a line to be broken by punctuation.
        break_chars: Punctuation that should force a line break.

    Returns:
        A list of SubtitleSegment objects.
    """
    logger.info("Starting word segmentation...")

    if not words:
        return []

    segments: list[SubtitleSegment] = []
    current_line_words: list[SubtitleWord] = []

    for word_model in words:
        word_text = word_model.text.strip()
        if not word_text:
            continue

        current_text = " ".join(w.text for w in current_line_words)
        # The +1 is for the space character.
        if current_line_words and len(current_text) + 1 + len(word_text) > max_chars:
            segments.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []  # Reset for a new line

        # Add the word to the (potentially new) line.
        current_line_words.append(SubtitleWord(text=word_text, start=word_model.start, end=word_model.end))

        # If the newly added word ends with a break character, this line might be done.
        if word_text.endswith(break_chars) and len(current_line_words) >= min_words:
            segments.append(SubtitleSegment(words=current_line_words.copy()))
            current_line_words = []

    if current_line_words:
        segments.append(SubtitleSegment(words=current_line_words.copy()))

    logger.info(f"Segmentation complete: {len(segments)} subtitle lines created.")
    return segments
