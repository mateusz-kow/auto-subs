"""Core module for handling audio/video transcription."""

from pathlib import Path
from typing import Any


def run_transcription(media_path: Path, model_name: str) -> dict[str, Any]:
    """Transcribes a media file using Whisper.

    Args:
        media_path: The path to the media file.
        model_name: The name of the Whisper model to use.

    Returns:
        The transcription result as a dictionary.

    Raises:
        ImportError: If the 'whisper' package is not installed.
    """
    try:
        import whisper  # type: ignore
    except ImportError as e:
        raise ImportError(
            "Whisper is not installed. Please install it with: pip install 'auto-subs[transcribe]'"
        ) from e

    model = whisper.load_model(model_name)
    result = model.transcribe(str(media_path), word_timestamps=True)
    return result  # type: ignore[no-any-return]
