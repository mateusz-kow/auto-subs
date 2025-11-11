"""Public API for the auto-subs library."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from autosubs.core import generator, parser
from autosubs.core.builder import create_subtitles_from_transcription
from autosubs.core.transcriber import run_transcription
from autosubs.models.enums import TimingDistribution
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings
from autosubs.models.subtitles import AssSubtitles, Subtitles

# Factory mapping subtitle formats to their respective generator functions.
_format_map: dict[SubtitleFormat, Callable[..., str]] = {
    SubtitleFormat.SRT: generator.to_srt,
    SubtitleFormat.VTT: generator.to_vtt,
    SubtitleFormat.ASS: generator.to_ass,
    SubtitleFormat.JSON: generator.to_json,
}


def generate(
    transcription_source: dict[str, Any] | str | Path,
    output_format: str,
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 1,
    ass_settings: AssSettings | None = None,
) -> str:
    """Generate subtitle content from a transcription dictionary.

    This is the main entry point for using auto-subs as a library.

    Args:
        transcription_source: A dictionary containing transcription data (compatible
                              with Whisper's word-level output), or a path to a
                              JSON file containing such data.
        output_format: The desired output format ("srt", "vtt", "ass", or "json").
        max_chars: The maximum number of characters per subtitle line.
        min_words: The minimum number of words per subtitle line (punctuation breaks).
        max_lines: The maximum number of lines per subtitle segment.
        ass_settings: Optional settings for ASS format generation. If None,
                      default settings will be used.

    Returns:
        A string containing the generated subtitle content.

    Raises:
        ValueError: If the transcription data fails validation or the output
                    format is not supported.
        FileNotFoundError: If `transcription_source` is a path that does not exist.
    """
    if isinstance(transcription_source, (str, Path)):
        path = Path(transcription_source)
        if not path.is_file():
            raise FileNotFoundError(f"Transcription file not found at: {path}")
        with path.open("r", encoding="utf-8") as f:
            transcription_dict = json.load(f)
    else:
        transcription_dict = transcription_source

    normalized_format = output_format.lower()
    try:
        format_enum = SubtitleFormat(normalized_format)
        writer_func = _format_map[format_enum]
    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Invalid output format specified: {output_format}. Must be one of: {', '.join(_format_map.keys())}."
        ) from e

    subtitles = create_subtitles_from_transcription(
        transcription_dict,
        max_chars=max_chars,
        min_words=min_words,
        max_lines=max_lines,
    )

    if format_enum == SubtitleFormat.ASS:
        settings = ass_settings or AssSettings()
        return writer_func(subtitles, settings)
    return writer_func(subtitles)


def transcribe(
    media_file: str | Path,
    output_format: str,
    model_name: str = "base",
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 2,
    ass_settings: AssSettings | None = None,
    verbose: bool | None = None,
) -> str:
    """Transcribe a media file and generate subtitle content.

    This function provides an end-to-end solution from a media file to a
    subtitle string. It requires the `transcribe` extra to be installed.

    Args:
        media_file: Path to the audio or video file.
        output_format: The desired output format ("srt", "vtt", "ass", "json").
        model_name: The name of the Whisper model to use (e.g., "tiny", "base", "small").
        max_chars: The maximum number of characters per subtitle line.
        min_words: The minimum number of words per subtitle line (punctuation breaks).
        max_lines: The maximum number of lines per subtitle segment.
        ass_settings: Optional settings for ASS format generation.
        verbose: Controls Whisper's output. None for no output, False for a progress
                 bar, True for detailed transcription text.

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

    transcription_dict = run_transcription(media_path, model_name, verbose=verbose)

    return generate(
        transcription_dict,
        output_format,
        max_chars=max_chars,
        min_words=min_words,
        max_lines=max_lines,
        ass_settings=ass_settings,
    )


def load(
    file_path: str | Path,
    generate_word_timings: bool = False,
    timing_strategy: TimingDistribution = TimingDistribution.BY_CHAR_COUNT,
) -> Subtitles:
    """Load and parse a subtitle file into a Subtitles object.

    Args:
        file_path: Path to the subtitle file (.srt, .vtt, .ass).
        generate_word_timings: If True, heuristically generates word-level timestamps
                               for formats that lack them (e.g., SRT, VTT).
        timing_strategy: The strategy to use for generating word timings.

    Returns:
        A Subtitles object (or AssSubtitles for .ass files) representing the parsed file content.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Subtitle file not found at: {path}")

    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    subtitles: Subtitles

    supported_formats = {f".{fmt}" for fmt in SubtitleFormat if fmt != SubtitleFormat.JSON}
    if suffix == ".srt":
        segments = parser.parse_srt(content)
        subtitles = Subtitles(segments=segments)
    elif suffix == ".vtt":
        segments = parser.parse_vtt(content)
        subtitles = Subtitles(segments=segments)
    elif suffix == ".ass":
        subtitles = parser.parse_ass(content)
    else:
        raise ValueError(
            f"Unsupported subtitle format: {suffix}. Must be one of: {', '.join(sorted(supported_formats))}."
        )

    if generate_word_timings and not isinstance(subtitles, AssSubtitles):
        for segment in subtitles.segments:
            segment.generate_word_timings(strategy=timing_strategy)

    return subtitles
