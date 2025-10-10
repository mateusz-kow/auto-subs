import json
import logging
from pathlib import Path
from typing import Annotated

import typer

import auto_subs
from auto_subs import __version__
from auto_subs.api import transcribe as transcribe_api
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings, AssStyleSettings
from auto_subs.models.whisper import WhisperModel

# The logger is configured in the main() callback based on CLI flags.
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A powerful, local-first CLI for video transcription and subtitle generation.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)

SUPPORTED_MEDIA_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".mkv", ".avi", ".wav", ".flac"}


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
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show the application's version and exit.",
        ),
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Suppress all output except for errors.")] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging. Use -vv for more detail.",
            count=True,
            is_eager=True,  # Process this before other options
        ),
    ] = 0,
) -> None:
    """Configure logging and manage the CLI application."""
    if quiet and verbose > 0:
        raise typer.BadParameter("--quiet and --verbose options cannot be used together.")

    log_level = logging.INFO
    if quiet:
        log_level = logging.WARNING
    elif verbose >= 1:
        log_level = logging.DEBUG

    # Configure the root logger
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.debug(f"Verbose logging enabled. Level set to: {logging.getLevelName(log_level)}")


@app.command()
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
        typer.Option("--format", "-f", case_sensitive=False, help="Format for the output subtitles."),
    ] = SubtitleFormat.SRT,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    karaoke: Annotated[bool, typer.Option(help="Enable karaoke-style word highlighting for ASS format.")] = False,
) -> None:
    """Generate a subtitle file from a transcription JSON."""
    ass_settings = AssSettings()
    if karaoke:
        if output_format != SubtitleFormat.ASS:
            typer.secho("Warning: --karaoke flag is only applicable for ASS format.", fg=typer.colors.YELLOW)
        else:
            ass_settings.highlight_style = AssStyleSettings()

    files_to_process = []
    if input_path.is_dir():
        if output_path and not output_path.is_dir():
            typer.secho("Error: If input is a directory, output must also be a directory.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        files_to_process.extend(sorted(input_path.glob("*.json")))
        if not files_to_process:
            typer.secho(f"No JSON files found in directory: {input_path}", fg=typer.colors.YELLOW)
            raise typer.Exit()
    else:
        files_to_process.append(input_path)

    has_errors = False
    for file in files_to_process:
        typer.echo(f"Processing: {file.name}")
        try:
            with file.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

            content = auto_subs.generate(
                raw_data,
                output_format=output_format,
                max_chars=max_chars,
                ass_settings=ass_settings,
            )

        except (OSError, json.JSONDecodeError) as e:
            typer.secho(f"Error reading or parsing input file {file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue
        except ValueError as e:
            typer.secho(f"Input file validation error for {file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

        if output_path:
            out_file = (
                output_path / file.with_suffix(f".{output_format.value}").name if output_path.is_dir() else output_path
            )
        else:
            out_file = file.with_suffix(f".{output_format.value}")
        out_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            out_file.write_text(content, encoding="utf-8")
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)
        except OSError as e:
            typer.secho(f"Error writing to file {out_file}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

    if has_errors:
        raise typer.Exit(code=1)


@app.command()
def transcribe(
    media_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="Path to an audio/video file or a directory of media files.",
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
        typer.Option("--format", "-f", case_sensitive=False, help="Format for the output subtitles."),
    ] = SubtitleFormat.SRT,
    model: Annotated[
        WhisperModel, typer.Option(case_sensitive=False, help="Whisper model to use.")
    ] = WhisperModel.BASE,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    karaoke: Annotated[bool, typer.Option(help="Enable karaoke-style word highlighting for ASS format.")] = False,
) -> None:
    """Transcribe a media file and generate subtitles."""
    ass_settings = AssSettings()
    if karaoke:
        if output_format != SubtitleFormat.ASS:
            typer.secho("Warning: --karaoke flag is only applicable for ASS format.", fg=typer.colors.YELLOW)
        else:
            ass_settings.highlight_style = AssStyleSettings()

    files_to_process = []
    if media_path.is_dir():
        if output_path and not output_path.is_dir():
            typer.secho("Error: If input is a directory, output must also be a directory.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        for ext in SUPPORTED_MEDIA_EXTENSIONS:
            files_to_process.extend(sorted(media_path.glob(f"*{ext}")))
        if not files_to_process:
            typer.secho(f"No supported media files found in directory: {media_path}", fg=typer.colors.YELLOW)
            raise typer.Exit()
    else:
        files_to_process.append(media_path)

    has_errors = False
    for file in files_to_process:
        typer.echo(f"Transcribing: {file.name} (using '{model}' model)")
        try:
            content = transcribe_api(
                file,
                output_format=output_format,
                model_name=model,
                max_chars=max_chars,
                ass_settings=ass_settings,
            )
        except (ImportError, FileNotFoundError) as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
            typer.secho(
                "Please ensure 'auto-subs[transcribe]' is installed and ffmpeg is in your PATH.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1) from e
        except Exception as e:
            typer.secho(f"An unexpected error occurred while processing {file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

        if output_path:
            out_file = (
                output_path / file.with_suffix(f".{output_format.value}").name if output_path.is_dir() else output_path
            )
        else:
            out_file = file.with_suffix(f".{output_format.value}")
        out_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            out_file.write_text(content, encoding="utf-8")
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)
        except OSError as e:
            typer.secho(f"Error writing to file {out_file}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

    if has_errors:
        raise typer.Exit(code=1)
