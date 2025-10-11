from pathlib import Path
from typing import Annotated

import typer

from auto_subs.api import transcribe as transcribe_api
from auto_subs.cli.utils import PathProcessor, SupportedExtension
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings, AssStyleSettings
from auto_subs.models.whisper import WhisperModel


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
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Format for the output subtitles.",
        ),
    ] = SubtitleFormat.SRT,
    model: Annotated[
        WhisperModel, typer.Option(case_sensitive=False, help="Whisper model to use.")
    ] = WhisperModel.BASE,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    karaoke: Annotated[
        bool,
        typer.Option(help="Enable karaoke-style word highlighting for ASS format."),
    ] = False,
) -> None:
    """Transcribe a media file and generate subtitles."""
    ass_settings = AssSettings()
    if karaoke:
        if output_format != SubtitleFormat.ASS:
            typer.secho("Warning: --karaoke flag is only applicable for ASS format.", fg=typer.colors.YELLOW)
        else:
            ass_settings.highlight_style = AssStyleSettings()

    processor = PathProcessor(media_path, output_path, SupportedExtension.MEDIA)
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Transcribing: {in_file.name} (using '{model}' model)")
        out_file = out_file_base.with_suffix(f".{output_format.value}")

        try:
            content = transcribe_api(
                in_file,
                output_format=output_format,
                model_name=model,
                max_chars=max_chars,
                ass_settings=ass_settings,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)
        except (ImportError, FileNotFoundError) as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
            typer.secho(
                "Please ensure 'auto-subs[transcribe]' is installed and ffmpeg is in your PATH.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1) from e
        except Exception as e:
            typer.secho(f"An unexpected error occurred while processing {in_file.name}: {e}", fg=typer.colors.RED)
            has_errors = True

    if has_errors:
        raise typer.Exit(code=1)
