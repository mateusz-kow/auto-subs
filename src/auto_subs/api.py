"""Public API for the auto-subs library."""

from pathlib import Path
from typing import Any

from auto_subs.core import generator
from auto_subs.core.transcriber import run_transcription
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings
from auto_subs.models.subtitles import Subtitles


def generate(
    transcription_dict: dict[str, Any],
    output_format: str,
    max_chars: int = 35,
    ass_settings: AssSettings | None = None,
) -> str:
    """Generate subtitle content from a transcription dictionary.

    This is the main entry point for using auto-subs as a library.

    Args:
        transcription_dict: A dictionary containing transcription data, compatible
                            with Whisper's word-level output.
        output_format: The desired output format ("srt", "vtt", "ass", or "txt").
        max_chars: The maximum number of characters per subtitle line.
        ass_settings: Optional settings for ASS format generation. If None,
                      default settings will be used.

    Returns:
        A string containing the generated subtitle content.

    Raises:
        ValueError: If the transcription data fails validation or the output
                    format is not supported.
    """
    subtitles = Subtitles.from_dict(transcription_dict, max_chars=max_chars)
    normalized_format = output_format.lower()

    if normalized_format == SubtitleFormat.SRT:
        return generator.to_srt(subtitles)
    if normalized_format == SubtitleFormat.ASS:
        settings = ass_settings or AssSettings()
        return generator.to_ass(subtitles, settings)
    if normalized_format == SubtitleFormat.TXT:
        return generator.to_txt(subtitles)
    if normalized_format == SubtitleFormat.VTT:
        return generator.to_vtt(subtitles)

    raise ValueError(f"Invalid output format specified: {output_format}. Must be 'srt', 'vtt', 'ass', or 'txt'.")


def transcribe(
    media_file: str | Path,
    output_format: str,
    model_name: str = "base",
    max_chars: int = 35,
    ass_settings: AssSettings | None = None,
) -> str:
    """Transcribe a media file and generate subtitle content.

    This function provides an end-to-end solution from a media file to a
    subtitle string. It requires the `transcribe` extra to be installed.

    Args:
        media_file: Path to the audio or video file.
        output_format: The desired output format ("srt", "vtt", "ass", or "txt").
        model_name: The name of the Whisper model to use (e.g., "tiny", "base", "small").
        max_chars: The maximum number of characters per subtitle line.
        ass_settings: Optional settings for ASS format generation.

    Returns:
        A string containing the generated subtitle content.

    Raises:
        ImportError: If the required 'whisper' package is not installed.
        FileNotFoundError: If the specified media file does not exist.
        ValueError: If transcription or generation fails.
    """
    media_path = Path(media_file)
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found at: {media_path}")

    transcription_dict = run_transcription(media_path, model_name)
    return generate(transcription_dict, output_format, max_chars=max_chars, ass_settings=ass_settings)
