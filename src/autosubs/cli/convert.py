from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import load
from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
)
from autosubs.core import generator
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings
from autosubs.models.subtitles import Subtitles

# Factory mapping formats to their generator functions
_format_map: dict[SubtitleFormat, Callable[..., str]] = {
    SubtitleFormat.SRT: generator.to_srt,
    SubtitleFormat.VTT: generator.to_vtt,
    SubtitleFormat.ASS: lambda subs: generator.to_ass(subs, AssSettings()),
    SubtitleFormat.JSON: generator.to_json,
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
        SubtitleFormat | None,
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Format for the output subtitles. Inferred from --output if not specified.",
        ),
    ] = None,
) -> None:
    """Convert an existing subtitle file to a different format."""
    final_output_format = determine_output_format(output_format, output_path)

    typer.echo(f"Converting subtitles to {final_output_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.SUBTITLE)
    is_batch = input_path.is_dir()
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Processing: {in_file.name}")

        if is_batch:
            # Batch mode: append extension to avoid collisions
            out_file = out_file_base.with_name(f"{in_file.name}.{final_output_format.value}")
        else:
            # Single file mode: just replace the extension
            out_file = out_file_base.with_suffix(f".{final_output_format.value}")

        try:
            subtitles: Subtitles = load(in_file)
            writer_func = _format_map[final_output_format]
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
