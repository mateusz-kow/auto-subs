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
    process_batch,
    write_content_to_file,
)
from autosubs.models.formats import SubtitleFormat
from autosubs.models.whisper import WhisperModel


def _determine_output_path(in_file: Path, output_path: Path | None, media_path: Path) -> Path:
    if output_path and not output_path.is_dir() and not media_path.is_dir():
        return output_path
    elif output_path and output_path.is_dir():
        return output_path / in_file.name
    return in_file.with_stem(f"{in_file.stem}_burned")


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
    """Transcribe media and generate subtitles."""
    if burn:
        check_ffmpeg_installed()

    target_format = determine_output_format(output_format, output_path, default=SubtitleFormat.SRT)

    verbose_level: bool | None = True if whisper_verbose else (False if stream else None)

    processor = PathProcessor(media_path, output_path, SupportedExtension.MEDIA)

    def _transcribe_single(in_file: Path, out_base: Path) -> None:
        if verbose_level is None:
            typer.echo(f"Transcribing: {in_file.name} (model: {model.value})")

        content = transcribe_api(
            in_file,
            output_format=target_format,
            model_name=model,
            max_chars=max_chars,
            min_words=min_words,
            max_lines=max_lines,
            style_config_path=style_config,
            verbose=verbose_level,
            encoding=encoding,
        )

        if burn:
            video_exts = _EXTENSION_MAP[SupportedExtension.VIDEO]
            if in_file.suffix.lower() not in video_exts:
                typer.secho(f"Skipping burn for non-video: {in_file.name}", fg=typer.colors.YELLOW)
                return

            video_out = _determine_output_path(in_file, output_path, media_path)
            handle_burn_operation(in_file, video_out, content, target_format, bool(style_config))
        else:
            final_out = out_base.with_suffix(f".{target_format.value}")
            write_content_to_file(final_out, content)

    process_batch(processor, _transcribe_single)
