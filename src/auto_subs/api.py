"""Public API for the auto-subs library."""

from typing import Any

from auto_subs.core import generator
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
