from collections.abc import Generator
from logging import getLogger
from typing import cast

from autosubs.typing.transcription import SegmentDict, TranscriptionDict, WordDict

logger = getLogger(__name__)


def _extract_words(transcription: TranscriptionDict) -> Generator[WordDict, None, None]:
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
    transcription: TranscriptionDict,
    max_chars: int = 35,
    min_words: int = 1,
    break_chars: tuple[str, ...] = (".", ",", "!", "?"),
) -> list[SegmentDict]:
    """Segments word-level transcription data into subtitle lines.

    Args:
        transcription: The transcription data. Must contain a "segments" key,
                       which holds a list of segments, each with a "words" key.
        max_chars: The maximum number of characters desired per subtitle line.
        min_words: The minimum number of words for a line to be broken by punctuation.
        break_chars: Punctuation that should force a line break.

    Returns:
        A list of dictionaries, each representing a subtitle line.
    """
    all_words = list(_extract_words(transcription))
    if not all_words:
        return []

    lines: list[SegmentDict] = []
    current_line_words: list[WordDict] = []

    for word_data in all_words:
        word_text = word_data.get("word", "").strip()
        if not word_text:
            continue

        current_text = " ".join(w["word"].strip() for w in current_line_words)
        # The +1 is for the space character.
        if current_line_words and len(current_text) + 1 + len(word_text) > max_chars:
            cast(
                SegmentDict,
                lines.append(
                    cast(
                        SegmentDict,
                        {
                            "start": current_line_words[0]["start"],
                            "end": current_line_words[-1]["end"],
                            "text": current_text,
                            "words": current_line_words.copy(),
                        },
                    )
                ),
            )
            current_line_words = []  # Reset for a new line

        # Add the word to the (potentially new) line.
        current_line_words.append(word_data)

        # If the newly added word ends with a break character, this line might be done.
        if word_text.endswith(break_chars) and len(current_line_words) >= min_words:
            lines.append(
                cast(
                    SegmentDict,
                    {
                        "start": current_line_words[0]["start"],
                        "end": current_line_words[-1]["end"],
                        "text": " ".join(w["word"].strip() for w in current_line_words),
                        "words": current_line_words.copy(),
                    },
                )
            )
            current_line_words = []

    if current_line_words:
        lines.append(
            cast(
                SegmentDict,
                {
                    "start": current_line_words[0]["start"],
                    "end": current_line_words[-1]["end"],
                    "text": " ".join(w["word"].strip() for w in current_line_words),
                    "words": current_line_words.copy(),
                },
            )
        )

    logger.info(f"Segmentation complete: {len(lines)} subtitle lines created.")
    return lines
