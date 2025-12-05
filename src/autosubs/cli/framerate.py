import logging
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import load
from autosubs.cli.convert import _get_default_styler_engine
from autosubs.core.generator import to_ass, to_json, to_mpl2, to_srt, to_vtt
from autosubs.models.formats import SubtitleFormat

logger = logging.getLogger(__name__)


def _determine_output_format(
    output_format_option: SubtitleFormat | None,
    output_path_option: Path | None,
    input_path: Path,
) -> SubtitleFormat:
    if output_format_option:
        return output_format_option
    if output_path_option:
        suffix = output_path_option.suffix.lstrip(".").lower()
        try:
            return SubtitleFormat(suffix)
        except ValueError as e:
            raise typer.BadParameter(
                f"Cannot determine subtitle format from output path extension: {output_path_option.suffix}"
            ) from e

    suffix = input_path.suffix.lstrip(".").lower()
    try:
        return SubtitleFormat(suffix)
    except ValueError as e:
        raise typer.BadParameter(
            f"Cannot determine subtitle format from input path extension: {input_path.suffix}. Please specify --format."
        ) from e


def _validate_fps(fps_from: float, fps_to: float) -> None:
    if fps_from <= 0 or fps_to <= 0:
        raise typer.BadParameter("Framerate values must be positive.")
    if fps_from == fps_to:
        raise typer.BadParameter("Source and target framerates cannot be the same.")


def framerate(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the subtitle file to convert.",
        ),
    ],
    fps_from: Annotated[
        float,
        typer.Option(
            "--fps-from",
            help="The source framerate of the subtitle file.",
            rich_help_panel="Framerate Conversion",
        ),
    ],
    fps_to: Annotated[
        float,
        typer.Option(
            "--fps-to",
            help="The target framerate to convert the subtitle file to.",
            rich_help_panel="Framerate Conversion",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to the output file. If not specified, defaults to the input path with a '_newfps' suffix.",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
    output_format: Annotated[
        SubtitleFormat | None,
        typer.Option("--format", "-f", help="Format of the output subtitle file.", case_sensitive=False),
    ] = None,
    encoding: Annotated[
        str | None,
        typer.Option("--encoding", "-e", help="Encoding of the input and output files."),
    ] = None,
) -> None:
    """Converts a subtitle file from a source to a target framerate."""
    _validate_fps(fps_from, fps_to)

    final_output_format = _determine_output_format(output_format, output_path, input_path)

    final_output_path = output_path
    if not final_output_path:
        final_output_path = input_path.with_stem(f"{input_path.stem}_newfps").with_suffix(
            f".{final_output_format.value}"
        )

    generators = {
        SubtitleFormat.SRT: to_srt,
        SubtitleFormat.VTT: to_vtt,
        SubtitleFormat.ASS: lambda subs: to_ass(subs, _get_default_styler_engine()),
        SubtitleFormat.MPL2: to_mpl2,
        SubtitleFormat.JSON: to_json,
    }

    generator_func = generators.get(final_output_format)
    if not generator_func:
        raise typer.BadParameter(f"Unsupported output format: {final_output_format}")

    try:
        typer.echo(f"Loading subtitle file: {input_path}")
        subtitles = load(input_path, encoding=encoding)

        typer.echo(f"Converting framerate from {fps_from} to {fps_to}")
        subtitles.transform_framerate(source_fps=fps_from, target_fps=fps_to)

        content = generator_func(subtitles)

        final_output_path.write_text(content, encoding=encoding or "utf-8")
        typer.secho(f"Successfully converted subtitles to {final_output_path}", fg=typer.colors.GREEN)

    except Exception as e:
        logger.error(f"An error occurred during framerate conversion: {e}", exc_info=True)
        raise typer.Abort() from e
