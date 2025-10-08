import json
import logging
from enum import StrEnum, auto
from pathlib import Path

import typer

from . import __version__
from .core.generator import SubtitleGenerator
from .models.settings import AssSettings
from .models.subtitles import Subtitles

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = typer.Typer(help="A powerful CLI for video transcription and subtitle generation.")


class SubtitleFormat(StrEnum):
    ASS = auto()
    SRT = auto()
    TXT = auto()


def version_callback(value: bool) -> None:
    """Prints the version of the application and exits."""
    if value:
        typer.echo(f"auto-subs version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show the version and exit."
    ),
) -> None:
    """Main callback for the CLI application."""
    pass


@app.command()
def generate(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the input transcription JSON file.",
    ),
    output_path: Path | None = typer.Option(
        None, "--output", "-o", help="Path to save the subtitle file. Defaults to the same name as the input."
    ),
    output_format: SubtitleFormat = typer.Option(
        SubtitleFormat.SRT, "--format", "-f", case_sensitive=False, help="Format for the output subtitles."
    ),
    max_chars: int = typer.Option(35, help="Maximum characters per subtitle line for segmentation."),
) -> None:
    """Generates a subtitle file from a transcription JSON file."""
    typer.echo(f"Loading transcription from: {input_file}")

    try:
        with input_file.open("r", encoding="utf-8") as f:
            transcription_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        typer.secho(f"Error reading or parsing input file: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Convert the raw transcription data into our internal Subtitles format
    subtitles = Subtitles.from_transcription(transcription_data, max_chars=max_chars)

    # Determine the output path if not provided
    if output_path is None:
        output_path = input_file.with_suffix(f".{output_format.value}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Generating subtitles in {output_format.value.upper()} format...")

    # Generate the content based on the chosen format
    content = ""
    if output_format == SubtitleFormat.ASS:
        content = SubtitleGenerator.to_ass(subtitles, AssSettings())
    elif output_format == SubtitleFormat.SRT:
        content = SubtitleGenerator.to_srt(subtitles)
    elif output_format == SubtitleFormat.TXT:
        content = SubtitleGenerator.to_txt(subtitles)

    # Write the content to the output file
    try:
        output_path.write_text(content, encoding="utf-8")
        typer.secho(f"Successfully saved subtitles to: {output_path}", fg=typer.colors.GREEN)
    except OSError as e:
        typer.secho(f"Error writing to file {output_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
