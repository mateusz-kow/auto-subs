"""Public API for the auto-subs library."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from autosubs.core import generator, parser
from autosubs.core.builder import create_subtitles_from_transcription
from autosubs.core.styler import StylerEngine
from autosubs.core.transcriber import run_transcription
from autosubs.models.enums import TimingDistribution
from autosubs.models.formats import SubtitleFormat
from autosubs.models.styles.schemas import StyleEngineConfigSchema
from autosubs.models.subtitles import AssSubtitles, Subtitles

_format_map: dict[SubtitleFormat, Callable[..., str]] = {
    SubtitleFormat.SRT: generator.to_srt,
    SubtitleFormat.VTT: generator.to_vtt,
    SubtitleFormat.ASS: generator.to_ass,
    SubtitleFormat.JSON: generator.to_json,
}

_DEFAULT_STYLE_CONFIG = StyleEngineConfigSchema(
    styles=[
        {
            "Name": "Default",
            "Fontname": "Arial",
            "Fontsize": 48,
            "PrimaryColour": "&H00FFFFFF",
            "SecondaryColour": "&H000000FF",
            "OutlineColour": "&H00000000",
            "BackColour": "&H00000000",
            "Bold": 0,
            "Italic": 0,
            "Underline": 0,
            "StrikeOut": 0,
            "ScaleX": 100,
            "ScaleY": 100,
            "Spacing": 0,
            "Angle": 0,
            "BorderStyle": 1,
            "Outline": 2,
            "Shadow": 1,
            "Alignment": 2,
            "MarginL": 10,
            "MarginR": 10,
            "MarginV": 20,
            "Encoding": 1,
        }
    ],
    rules=[],
)


def generate(
    transcription_source: dict[str, Any] | str | Path,
    output_format: str,
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 1,
    style_config_path: str | Path | None = None,
) -> str:
    """Generate subtitle content from a transcription dictionary.

    Args:
        transcription_source: A dictionary compatible with Whisper's output.
        output_format: The desired output format ("srt", "vtt", "ass", or "json").
        max_chars: The maximum number of characters per subtitle line.
        min_words: The minimum number of words per line before a punctuation break.
        max_lines: The maximum number of lines per subtitle segment.
        style_config_path: Optional path to a JSON file for the dynamic style engine.
                           Required for ASS output.

    Returns:
        A string containing the generated subtitle content.
    """
    if isinstance(transcription_source, (str, Path)):
        path = Path(transcription_source)
        if not path.is_file():
            raise FileNotFoundError(f"Transcription file not found at: {path}")
        with path.open("r", encoding="utf-8") as f:
            transcription_dict = json.load(f)
    else:
        transcription_dict = transcription_source

    try:
        format_enum = SubtitleFormat(output_format.lower())
        writer_func = _format_map[format_enum]
    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Invalid output format: {output_format}. Must be one of: {', '.join(_format_map.keys())}."
        ) from e

    subtitles = create_subtitles_from_transcription(
        transcription_dict,
        max_chars=max_chars,
        min_words=min_words,
        max_lines=max_lines,
    )

    if format_enum == SubtitleFormat.ASS:
        schema = _DEFAULT_STYLE_CONFIG
        if style_config_path:
            config_path = Path(style_config_path)
            schema = StyleEngineConfigSchema.model_validate_json(config_path.read_text(encoding="utf-8"))
        domain_config = schema.to_domain()
        styler_engine = StylerEngine(domain_config)
        return writer_func(subtitles, styler_engine=styler_engine)
    return writer_func(subtitles)


def transcribe(
    media_file: str | Path,
    output_format: str,
    model_name: str = "base",
    max_chars: int = 35,
    min_words: int = 1,
    max_lines: int = 2,
    style_config_path: str | Path | None = None,
    verbose: bool | None = None,
) -> str:
    """Transcribe a media file and generate subtitle content."""
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
        style_config_path=style_config_path,
    )


def load(
    file_path: str | Path,
    generate_word_timings: bool = False,
    timing_strategy: TimingDistribution = TimingDistribution.BY_CHAR_COUNT,
) -> Subtitles:
    """Load and parse a subtitle file into a Subtitles object."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Subtitle file not found at: {path}")

    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")
    subtitles: Subtitles

    if suffix == ".srt":
        subtitles = Subtitles(segments=parser.parse_srt(content))
    elif suffix == ".vtt":
        subtitles = Subtitles(segments=parser.parse_vtt(content))
    elif suffix == ".ass":
        subtitles = parser.parse_ass(content)
    else:
        supported = ", ".join(f".{fmt}" for fmt in SubtitleFormat if fmt != "json")
        raise ValueError(f"Unsupported format: {suffix}. Supported: {supported}.")

    if generate_word_timings and not isinstance(subtitles, AssSubtitles):
        for segment in subtitles.segments:
            segment.generate_word_timings(strategy=timing_strategy)

    return subtitles
