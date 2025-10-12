import json
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import generate as generate_api
from autosubs.cli.utils import PathProcessor, SupportedExtension
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings, AssStyleSettings


def generate(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="Path to a Whisper-compatible JSON file or a directory of JSON files.",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the subtitle file or directory. Defaults to the input path with a new extension.",
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
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    karaoke: Annotated[
        bool,
        typer.Option(help="Enable karaoke-style word highlighting for ASS format."),
    ] = False,
) -> None:
    """Generate a subtitle file from a transcription JSON."""
    typer.echo(f"Generating subtitles in {output_format.upper()} format...")
    ass_settings = AssSettings()
    if karaoke:
        if output_format != SubtitleFormat.ASS:
            typer.secho(
                "Warning: --karaoke flag is only applicable for ASS format.",
                fg=typer.colors.YELLOW,
            )
        else:
            ass_settings.highlight_style = AssStyleSettings()

    processor = PathProcessor(input_path, output_path, SupportedExtension.JSON)
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Processing: {in_file.name}")
        out_file = out_file_base.with_suffix(f".{output_format.value}")

        try:
            with in_file.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            content = generate_api(
                raw_data,
                output_format=output_format,
                max_chars=max_chars,
                ass_settings=ass_settings,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)

        except (OSError, json.JSONDecodeError) as e:
            typer.secho(
                f"Error reading or parsing input file {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True
        except ValueError as e:
            typer.secho(
                f"Input file validation error for {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True

    if has_errors:
        raise typer.Exit(code=1)
