from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import transcribe as transcribe_api
from autosubs.cli.utils import (
    _EXTENSION_MAP,
    PathProcessor,
    SupportedExtension,
    check_ffmpeg_installed,
    determine_output_format,
    handle_burn_operation,
)
from autosubs.models.formats import SubtitleFormat
from autosubs.models.whisper import WhisperModel


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
        SubtitleFormat | None,
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Format for the output subtitles. Inferred from --output if not specified.",
        ),
    ] = None,
    model: Annotated[
        WhisperModel, typer.Option(case_sensitive=False, help="Whisper model to use.")
    ] = WhisperModel.BASE,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    min_words: Annotated[
        int,
        typer.Option(help="Minimum words per line before allowing a punctuation break."),
    ] = 1,
    max_lines: Annotated[
        int,
        typer.Option(help="Maximum number of lines per subtitle segment."),
    ] = 2,
    stream: Annotated[
        bool,
        typer.Option("--stream", help="Display a progress bar during transcription."),
    ] = False,
    whisper_verbose: Annotated[
        bool,
        typer.Option(help="Enable Whisper's detailed, real-time transcription output."),
    ] = False,
    style_config: Annotated[
        Path | None,
        typer.Option(
            "--style-config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="[ASS] Path to a JSON file with the style engine configuration.",
        ),
    ] = None,
    burn: Annotated[bool, typer.Option(help="Burn the subtitles directly into a video file.")] = False,
    encoding: Annotated[
        str | None,
        typer.Option(
            "--encoding",
            "-e",
            help="Encoding of the style config JSON file (if provided). Auto-detected if not specified.",
        ),
    ] = None,
) -> None:
    """Transcribe a media file and generate subtitles."""
    if burn:
        check_ffmpeg_installed()

    final_output_format = determine_output_format(output_format, output_path)

    verbose_level: bool | None = None
    if whisper_verbose:
        verbose_level = True
    elif stream:
        verbose_level = False

    processor = PathProcessor(media_path, output_path, SupportedExtension.MEDIA)
    is_batch = media_path.is_dir()
    has_errors = False

    for in_file, out_file_base in processor.process():
        try:
            if verbose_level is None:
                typer.echo(f"Transcribing: {in_file.name} (using '{model.value}' model)")

            content = transcribe_api(
                in_file,
                output_format=final_output_format,
                model_name=model,
                max_chars=max_chars,
                min_words=min_words,
                max_lines=max_lines,
                style_config_path=style_config,
                verbose=verbose_level,
                encoding=encoding,
            )

            if burn:
                video_extensions = _EXTENSION_MAP[SupportedExtension.VIDEO]
                if in_file.suffix.lower() not in video_extensions:
                    typer.secho(
                        f"Skipping non-video file for burning: {in_file.name}",
                        fg=typer.colors.YELLOW,
                    )
                    continue

                if is_batch:
                    video_output_path = out_file_base.with_suffix(in_file.suffix)
                else:
                    video_output_path = output_path or in_file.with_stem(f"{in_file.stem}_burned")

                handle_burn_operation(
                    video_input=in_file,
                    video_output=video_output_path,
                    subtitle_content=content,
                    subtitle_format=final_output_format,
                    styling_options_used=bool(style_config),
                )
            else:
                if is_batch:
                    out_file = out_file_base.with_name(f"{in_file.stem}.{final_output_format.value}")
                else:
                    out_file = out_file_base.with_suffix(f".{final_output_format.value}")

                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_text(content, encoding="utf-8")
                typer.secho(
                    f"Successfully saved subtitles to: {out_file}",
                    fg=typer.colors.GREEN,
                )
        except (ImportError, FileNotFoundError) as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
            typer.secho(
                "Please ensure 'auto-subs[transcribe]' is installed and ffmpeg is in your PATH.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1) from e
        except Exception as e:
            typer.secho(
                f"An unexpected error occurred while processing {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True

    if has_errors:
        raise typer.Exit(code=1)
