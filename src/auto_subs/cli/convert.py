from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from auto_subs.api import load
from auto_subs.cli.utils import PathProcessor, SupportedExtension
from auto_subs.core import generator
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings
from auto_subs.models.subtitles import Subtitles

# Factory mapping formats to their generator functions
_format_map: dict[SubtitleFormat, Callable[..., str]] = {
    SubtitleFormat.SRT: generator.to_srt,
    SubtitleFormat.VTT: generator.to_vtt,
    SubtitleFormat.ASS: lambda subs: generator.to_ass(subs, AssSettings()),
}


def convert(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="Path to a subtitle file (.srt, .vtt, .ass) or a directory of such files.",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the converted subtitle file or directory. "
            "Defaults to the input path with a new extension.",
        ),
    ] = None,
    output_format: Annotated[
        SubtitleFormat,
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Format for the output subtitles.",
        ),
    ] = SubtitleFormat.SRT,
) -> None:
    """Convert an existing subtitle file to a different format."""
    typer.echo(f"Converting subtitles to {output_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.SUBTITLE)
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Processing: {in_file.name}")
        out_file = out_file_base.with_suffix(f".{output_format.value}")

        try:
            subtitles: Subtitles = load(in_file)
            writer_func = _format_map[output_format]
            content = writer_func(subtitles)

            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
            typer.secho(
                f"Successfully saved converted subtitles to: {out_file}",
                fg=typer.colors.GREEN,
            )
        except (OSError, ValueError) as e:
            typer.secho(f"Error processing file {in_file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

    if has_errors:
        raise typer.Exit(code=1)
