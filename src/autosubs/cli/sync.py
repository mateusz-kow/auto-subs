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


def _parse_time(time_str: str) -> float:
    """Parses a time string into seconds."""
    try:
        return float(time_str.strip())
    except ValueError as e:
        raise typer.BadParameter(f"Invalid time: '{time_str}'. Use seconds (e.g. '123.45').") from e


def sync(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the subtitle file to synchronize.",
        ),
    ],
    points: Annotated[
        list[str],
        typer.Option(
            "--point",
            "-p",
            help='A synchronization point in "old_time,new_time" format. Two points are required.',
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to the output file. If not specified, defaults to the input path with a '_synced' suffix.",
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
    """Linearly synchronizes subtitles based on two reference points."""
    if len(points) != 2:
        raise typer.BadParameter("Exactly two synchronization points required.")

    try:
        old_start, new_start = map(_parse_time, points[0].split(","))
        old_end, new_end = map(_parse_time, points[1].split(","))
    except ValueError:
        raise typer.BadParameter('Each point must be in "old_time,new_time" format.') from None

    if old_start == old_end:
        raise typer.BadParameter("The two 'old_time' values cannot be the same.")

    target_format = determine_output_format(output_format, output_path, input_path=input_path)

    if not output_path:
        output_path = input_path.with_stem(f"{input_path.stem}_synced").with_suffix(f".{target_format.value}")

    try:
        typer.echo(f"Loading subtitle file: {input_path}")
        subtitles = load(input_path, encoding=encoding)

        typer.echo(f"Syncing: ({old_start} -> {new_start}) to ({old_end} -> {new_end})")
        subtitles.linear_sync(old_start, old_end, new_start, new_end)

        generator_func = get_generator_func(target_format)
        content = generator_func(subtitles)

        write_content_to_file(output_path, content, encoding=encoding or "utf-8")

    except Exception as e:
        logger.error(f"An error occurred during synchronization: {e}", exc_info=True)
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Abort() from e
