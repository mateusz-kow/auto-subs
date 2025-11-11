from pathlib import Path
from typing import Annotated

import typer

from autosubs.cli.utils import (
    _EXTENSION_MAP,
    SupportedExtension,
    check_ffmpeg_installed,
    handle_burn_operation,
)
from autosubs.models.formats import SubtitleFormat


def burn(
    video_input: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the source video file.",
        ),
    ],
    subtitle_input: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the subtitle file to burn into the video.",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the output video file. Defaults to a new file with a '.burned' suffix in the name.",
        ),
    ] = None,
) -> None:
    """Burn an existing subtitle file into a video."""
    video_extensions = _EXTENSION_MAP[SupportedExtension.VIDEO]
    if video_input.suffix.lower() not in video_extensions:
        error_message = f"Error: Input video must be one of: {', '.join(sorted(video_extensions))}"
        typer.secho(error_message, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    subtitle_extensions = _EXTENSION_MAP[SupportedExtension.SUBTITLE]
    if subtitle_input.suffix.lower() not in subtitle_extensions:
        error_message = f"Error: Input subtitle must be one of: {', '.join(sorted(subtitle_extensions))}"
        typer.secho(error_message, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    check_ffmpeg_installed()

    final_output_path = output_path if output_path else video_input.with_stem(f"{video_input.stem}_burned")
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    subtitle_content = subtitle_input.read_text(encoding="utf-8")
    subtitle_format = SubtitleFormat(subtitle_input.suffix.lower().strip("."))

    handle_burn_operation(
        video_input=video_input,
        video_output=final_output_path,
        subtitle_content=subtitle_content,
        subtitle_format=subtitle_format,
        styling_options_used=False,  # Cannot know if styles were used when burning from file
    )
