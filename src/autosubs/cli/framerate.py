import logging
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import load
from autosubs.cli.utils import (
    determine_output_format,
    get_generator_func,
    write_content_to_file,
)
from autosubs.models.formats import SubtitleFormat

logger = logging.getLogger(__name__)


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

    final_output_format = determine_output_format(output_format, output_path, input_path)
    final_output_path: Path = output_path or input_path.with_stem(f"{input_path.stem}_newfps").with_suffix(
        f".{final_output_format.value}"
    )

    try:
        typer.echo(f"Loading: {input_path}")
        subtitles = load(input_path, encoding=encoding)

        typer.echo(f"Converting framerate from {fps_from} to {fps_to}")
        subtitles.transform_framerate(source_fps=fps_from, target_fps=fps_to)

        generator_func = get_generator_func(final_output_format)
        content = generator_func(subtitles)

        write_content_to_file(final_output_path, content, encoding=encoding or "utf-8")
        typer.secho(f"Successfully converted subtitles to {final_output_path}", fg=typer.colors.GREEN)

    except Exception as e:
        logger.error(f"Framerate conversion error: {e}", exc_info=True)
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Abort() from e
