from collections.abc import Generator
from logging import getLogger
from typing import Any

from auto_subs.typing.transcription import Transcription, WordDict

logger = getLogger(__name__)


def _extract_words(transcription: Transcription) -> Generator[WordDict, None, None]:
    """A generator that flattens and yields valid word dictionaries from a transcription.

    Args:
        transcription: The raw transcription dictionary.

    Yields:
        Individual word dictionaries.

    Raises:
        ValueError: If the transcription data has an invalid structure.
    """
    try:
        for segment in transcription["segments"]:
            for word in segment["words"]:
                if "word" in word and "start" in word and "end" in word:
                    yield word
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid transcription format: {e}")
        raise ValueError("Transcription data is missing 'segments' or has invalid structure.") from e


def segment_words(
    transcription: Transcription,
    max_chars: int = 35,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[dict[str, Any]]:
    """Segments word-level transcription data into subtitle lines.

    Args:
        transcription: The transcription data. Must contain a "segments" key,
                       which holds a list of segments, each with a "words" key.
        max_chars: The maximum number of characters desired per subtitle line.
        break_chars: Punctuation that should force a line break.

    Returns:
        A list of dictionaries, each representing a subtitle line.
    """
    all_words = list(_extract_words(transcription))
    if not all_words:
        return []

    lines: list[dict[str, Any]] = []
    current_line_words: list[WordDict] = []

    for word_data in all_words:
        word_text = word_data.get("word", "").strip()
        if not word_text:
            continue

        current_line_words.append(word_data)
        current_text = " ".join(w["word"].strip() for w in current_line_words)

        is_too_long = len(current_text) >= max_chars
        ends_with_break_char = word_text.endswith(break_chars)

        if is_too_long or ends_with_break_char:
            lines.append(
                {
                    "start": current_line_words[0]["start"],
                    "end": current_line_words[-1]["end"],
                    "text": current_text,
                    "words": current_line_words.copy(),
                }
            )
            current_line_words = []

    if current_line_words:
        lines.append(
            {
                "start": current_line_words[0]["start"],
                "end": current_line_words[-1]["end"],
                "text": " ".join(w["word"].strip() for w in current_line_words),
                "words": current_line_words.copy(),
            }
        )

    logger.info(f"Segmentation complete: {len(lines)} subtitle lines created.")
    return lines
