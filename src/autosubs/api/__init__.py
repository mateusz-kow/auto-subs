"""Public API for the auto-subs library."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from autosubs.core import generator, parser
from autosubs.core.builder import create_subtitles_from_transcription
from autosubs.core.encoding import read_with_encoding_detection
from autosubs.core.styler import AssStyler
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
    SubtitleFormat.MICRODVD: generator.to_microdvd,
    SubtitleFormat.MPL2: generator.to_mpl2,
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
    char_limit: int = 80,
    target_cps: float = 15.0,
    style_config_path: str | Path | None = None,
    encoding: str | None = None,
    fps: float | None = None,
    **kwargs: Any,
) -> str:
    """Generate subtitle content from a transcription source."""
    if isinstance(transcription_source, (str, Path)):
        path = Path(transcription_source)
        if not path.is_file():
            raise FileNotFoundError(f"Transcription file not found at: {path}")
        content = read_with_encoding_detection(path, encoding)
        try:
            transcription_dict = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from: {path}") from e
    else:
        transcription_dict = transcription_source

    try:
        format_enum = SubtitleFormat(output_format.lower())
        writer_func = _format_map[format_enum]
    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Invalid output format: {output_format}. Must be one of: {', '.join(f.value for f in _format_map)}."
        ) from e

    subtitles = create_subtitles_from_transcription(
        transcription_dict,
        char_limit=char_limit,
        target_cps=target_cps,
    )

    if format_enum == SubtitleFormat.ASS:
        schema = _DEFAULT_STYLE_CONFIG
        if style_config_path:
            config_path = Path(style_config_path)
            config_content = read_with_encoding_detection(config_path, encoding)
            try:
                schema = StyleEngineConfigSchema.model_validate_json(config_content)
            except ValueError as e:
                raise ValueError(f"Failed to parse style config from: {config_path}") from e
        domain_config = schema.to_domain()
        styler_engine = AssStyler(domain_config)
        return writer_func(subtitles, styler_engine=styler_engine)
    if format_enum == SubtitleFormat.MICRODVD:
        if fps is None:
            raise ValueError("FPS is required for MicroDVD format.")
        return writer_func(subtitles, fps=fps)
    return writer_func(subtitles)


def transcribe(
    media_file: str | Path,
    output_format: str,
    model_name: str = "base",
    char_limit: int = 80,
    target_cps: float = 15.0,
    style_config_path: str | Path | None = None,
    verbose: bool | None = None,
    encoding: str | None = None,
    fps: float | None = None,
    **kwargs: Any,
) -> str:
    """Transcribe a media file and generate subtitle content."""
    media_path = Path(media_file)
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found at: {media_path}")
    transcription_dict = run_transcription(media_path, model_name, verbose=verbose)
    return generate(
        transcription_dict,
        output_format,
        char_limit=char_limit,
        target_cps=target_cps,
        style_config_path=style_config_path,
        encoding=encoding,
        fps=fps,
        **kwargs,
    )


def load(
    file_path: str | Path,
    generate_word_timings: bool = False,
    timing_strategy: TimingDistribution = TimingDistribution.BY_CHAR_COUNT,
    encoding: str | None = None,
    fps: float | None = None,
) -> Subtitles:
    """Load and parse a subtitle file into a Subtitles object."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Subtitle file not found at: {path}")

    suffix = path.suffix.lower()
    content = read_with_encoding_detection(path, encoding)
    subtitles: Subtitles

    if suffix == ".srt":
        subtitles = Subtitles(segments=parser.parse_srt(content))
    elif suffix == ".vtt":
        subtitles = Subtitles(segments=parser.parse_vtt(content))
    elif suffix == ".ass":
        subtitles = parser.parse_ass(content)
    elif suffix == ".sub":
        subtitles = Subtitles(segments=parser.parse_microdvd(content, fps=fps))
    elif suffix == ".txt":
        first_line = content.split("\n", 1)[0].strip()
        if parser.MPL2_TIMESTAMP_REGEX.match(first_line):
            subtitles = Subtitles(segments=parser.parse_mpl2(content))
        else:
            raise ValueError(f"File {suffix} does not appear to be in MPL2 format.")
    else:
        raise ValueError(f"Unsupported format: {suffix}.")

    if generate_word_timings and not isinstance(subtitles, AssSubtitles):
        for segment in subtitles.segments:
            segment.generate_word_timings(strategy=timing_strategy)

    return subtitles
