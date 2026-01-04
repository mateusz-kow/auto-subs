"""Module responsible for constructing domain models from raw data.

This acts as a factory/builder layer to orchestrate validation and transformation,
separating the core logic from the data models themselves.
"""

from typing import Any

from autosubs.core.word_segmenter import segment_words
from autosubs.models import TRANSCRIPTION_ADAPTER
from autosubs.models.subtitles import Subtitles, SubtitleWord


def create_subtitles_from_transcription(
    transcription_dict: dict[str, Any],
    char_limit: int = 80,
    target_cps: float = 15.0,
) -> Subtitles:
    """Validates a raw transcription dictionary and builds a Subtitles object."""
    validated_model = TRANSCRIPTION_ADAPTER.validate_python(transcription_dict)

    words = [
        SubtitleWord(text=word.word, start=word.start, end=word.end)
        for segment in validated_model.segments
        for word in segment.words
    ]

    segments = segment_words(words, char_limit=char_limit, target_cps=target_cps)

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
