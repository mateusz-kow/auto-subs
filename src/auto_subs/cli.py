import json
import logging
from pathlib import Path
from typing import Annotated

import typer

import auto_subs
from auto_subs import __version__
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A powerful, local-first CLI for video transcription and subtitle generation.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Prints the version of the application and exits."""
    if value:
        typer.echo(f"auto-subs version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show the application's version and exit.",
        ),
    ] = False,
) -> None:
    """Manage the CLI application."""
    pass


@app.command()
def generate(
    input_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the Whisper-compatible transcription JSON file.",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the subtitle file. Defaults to the input filename with a new extension.",
        ),
    ] = None,
    output_format: Annotated[
        SubtitleFormat,
        typer.Option("--format", "-f", case_sensitive=False, help="Format for the output subtitles."),
    ] = SubtitleFormat.SRT,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
) -> None:
    """Generate a subtitle file from a transcription JSON."""
    typer.echo(f"Loading transcription from: {input_file}")

    try:
        with input_file.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        content = auto_subs.generate(
            raw_data,
            output_format=output_format.value,
            max_chars=max_chars,
            ass_settings=AssSettings(),
        )

    except (OSError, json.JSONDecodeError) as e:
        typer.secho(f"Error reading or parsing input file: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        typer.secho(f"Input file validation error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

    if output_path is None:
        output_path = input_file.with_suffix(f".{output_format.value}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Generating subtitles in {output_format.value.upper()} format...")

    try:
        output_path.write_text(content, encoding="utf-8")
        typer.secho(f"Successfully saved subtitles to: {output_path}", fg=typer.colors.GREEN)
    except OSError as e:
        typer.secho(f"Error writing to file {output_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
