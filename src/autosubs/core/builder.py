"""Module responsible for constructing domain models from raw data.

This acts as a factory/builder layer to orchestrate validation and transformation,
separating the core logic from the data models themselves.
"""

from typing import Any

from autosubs.core.word_segmenter import segment_words
from autosubs.models import TRANSCRIPTION_ADAPTER
from autosubs.models.subtitles import Subtitles, SubtitleWord


def create_subtitles_from_transcription(
    transcription_dict: dict[str, Any], max_chars: int, min_words: int, max_lines: int
) -> "Subtitles":
    """Validates a raw transcription dictionary and builds a Subtitles object.

    This is the canonical factory function for creating Subtitles from a
    Whisper-like transcription source.

    Args:
        transcription_dict: The raw transcription dictionary.
        max_chars: The maximum number of characters per subtitle line.
        min_words: The minimum number of words per subtitle line (punctuation breaks).
        max_lines: The maximum number of lines per subtitle segment.

    Returns:
        A fully constructed and validated Subtitles object.
    """
    validated_model = TRANSCRIPTION_ADAPTER.validate_python(transcription_dict)

    words = [
        SubtitleWord(text=word.word, start=word.start, end=word.end)
        for segment in validated_model.segments
        for word in segment.words
    ]
    segments = segment_words(words, max_chars=max_chars, min_words=min_words, max_lines=max_lines)

    return Subtitles(segments=segments)


def create_dict_from_subtitles(subtitles: "Subtitles") -> dict[str, Any]:
    """Converts a Subtitles object back into a Whisper-compatible dictionary.

    Args:
        subtitles: The Subtitles object to convert.

    Returns:
        A dictionary compatible with the original transcription format.
    """
    return {
        "segments": [
            {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": [
                    {
                        "word": word.text,
                        "start": word.start,
                        "end": word.end,
                    }
                    for word in segment.words
                ],
            }
            for i, segment in enumerate(subtitles.segments, 1)
        ],
        "language": "unknown",
        "text": subtitles.text,
    }
