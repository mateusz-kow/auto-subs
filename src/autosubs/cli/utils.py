import json
import os
import shutil
import tempfile
from collections.abc import Generator
from enum import Enum, auto
from pathlib import Path

import typer

from autosubs.core.burner import FFmpegError, burn_subtitles
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings, AssStyleSettings


# Add this new function to the end of src/autosubs/cli/utils.py
def parse_ass_settings_from_cli(
    style_file: Path | None,
    karaoke: bool,
    # Pass all the CLI options directly
    font_name: str | None,
    font_size: int | None,
    primary_color: str | None,
    secondary_color: str | None,
    outline_color: str | None,
    back_color: str | None,
    bold: bool | None,
    italic: bool | None,
    underline: bool | None,
    alignment: int | None,
    margin_v: int | None,
) -> AssSettings:
    """Parses all ASS-related CLI options into an AssSettings object."""
    settings_dict = {}
    if style_file:
        with style_file.open("r", encoding="utf-8") as f:
            settings_dict = json.load(f)

    cli_opts = {
        "font_name": font_name,
        "font_size": font_size,
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "outline_color": outline_color,
        "back_color": back_color,
        "bold": -1 if bold else (0 if bold is False else None),
        "italic": -1 if italic else (0 if italic is False else None),
        "underline": -1 if underline else (0 if underline is False else None),
        "alignment": alignment,
        "margin_v": margin_v,
    }
    settings_dict.update({k: v for k, v in cli_opts.items() if v is not None})
    ass_settings = AssSettings.model_validate(settings_dict)

    if karaoke:
        ass_settings.highlight_style = AssStyleSettings()

    return ass_settings


def determine_output_format(
    output_format_option: SubtitleFormat | None,
    output_path_option: Path | None,
    default: SubtitleFormat = SubtitleFormat.SRT,
) -> SubtitleFormat:
    """Determines the final subtitle format based on user options.

    The priority is:
    1. The explicit --format option.
    2. The extension of the --output path.
    3. The specified default format.
    """
    if output_format_option:
        return output_format_option

    if output_path_option:
        suffix = output_path_option.suffix.lower().strip(".")
        if suffix in SubtitleFormat.__members__.values():
            return SubtitleFormat(suffix)

    typer.secho(
        f"No output format specified or inferred. Defaulting to {default.upper()}.",
        fg=typer.colors.YELLOW,
    )
    return default


class SupportedExtension(Enum):
    """Enumeration for supported file types for CLI commands."""

    MEDIA = auto()
    SUBTITLE = auto()
    JSON = auto()
    VIDEO = auto()


_EXTENSION_MAP: dict[SupportedExtension, set[str]] = {
    SupportedExtension.MEDIA: {
        ".mp3",
        ".mp4",
        ".m4a",
        ".mkv",
        ".avi",
        ".wav",
        ".flac",
        ".mov",
        ".webm",
    },
    SupportedExtension.SUBTITLE: {".srt", ".vtt", ".ass"},
    SupportedExtension.JSON: {".json"},
    SupportedExtension.VIDEO: {".mp4", ".mkv", ".avi", ".mov", ".webm"},
}


class PathProcessor:
    """Handles processing of input and output paths for CLI commands."""

    def __init__(
        self,
        input_path: Path,
        output_path: Path | None,
        extension_type: SupportedExtension,
    ):
        """Handles processing of input and output paths for CLI commands."""
        self.input_path = input_path
        self.output_path = output_path
        self.extensions = _EXTENSION_MAP[extension_type]
        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validates that if input is a dir, output is also a dir."""
        if self.input_path.is_dir() and self.output_path and not self.output_path.is_dir():
            typer.secho(
                "Error: If input is a directory, output must also be a directory.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    def _get_files_from_dir(self) -> list[Path]:
        """Gathers and sorts all files with supported extensions from a directory."""
        files: list[Path] = []
        for ext in self.extensions:
            files.extend(self.input_path.glob(f"*{ext}"))
        if not files:
            typer.secho(
                f"No supported files found in directory: {self.input_path}",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit()
        return sorted(files)

    def process(self) -> Generator[tuple[Path, Path], None, None]:
        """Yields tuples of (input_file, output_file_base) for processing.

        The `output_file_base` is the intended output file path before the
        final extension is applied by the command.
        """
        files_to_process: list[Path] = []
        if self.input_path.is_dir():
            files_to_process.extend(self._get_files_from_dir())
        else:
            if self.input_path.suffix.lower() not in self.extensions:
                typer.secho(
                    f"Error: Unsupported input file format: {self.input_path.suffix}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)
            files_to_process.append(self.input_path)

        for file in files_to_process:
            if self.output_path:
                out_file = self.output_path / file.name if self.output_path.is_dir() else self.output_path
            else:
                out_file = file
            yield file, out_file


def check_ffmpeg_installed() -> None:
    """Checks for FFmpeg executable and exits if not found."""
    if not shutil.which("ffmpeg"):
        typer.secho(
            "Error: FFmpeg executable not found. This feature requires FFmpeg to be "
            "installed and available in your system's PATH.",
            fg=typer.colors.RED,
        )
        typer.secho(
            "Visit https://ffmpeg.org/download.html for installation instructions.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)


def handle_burn_operation(
    video_input: Path,
    video_output: Path,
    subtitle_content: str,
    subtitle_format: SubtitleFormat,
    styling_options_used: bool,
) -> None:
    """Central handler for burning subtitles into video."""
    if styling_options_used and subtitle_format in {
        SubtitleFormat.SRT,
        SubtitleFormat.VTT,
    }:
        typer.secho(
            "Warning: Burning in SRT/VTT format. All styling options (--font-name, --karaoke, etc.) "
            "will be ignored. For styled subtitles, use the ASS format.",
            fg=typer.colors.YELLOW,
        )

    typer.secho(
        "Starting video burn process. This may take a significant amount of time...",
        fg=typer.colors.CYAN,
    )

    temp_sub_file = None
    try:
        suffix = f".{subtitle_format.value}"
        # Create a temporary file, ensuring it's closed before FFmpeg accesses it.
        with tempfile.NamedTemporaryFile(
            "w",
            suffix=suffix,
            delete=False,
            encoding="utf-8",
        ) as f:
            temp_sub_file = Path(f.name)
            f.write(subtitle_content)

        burn_subtitles(video_input, temp_sub_file, video_output)

        typer.secho(
            f"Successfully burned subtitles into video: {video_output}",
            fg=typer.colors.GREEN,
        )
    except (FFmpegError, Exception) as e:
        typer.secho(
            f"An unexpected error occurred while burning subtitles: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1) from e
    finally:
        # Guarantee cleanup of the temporary file.
        if temp_sub_file and temp_sub_file.exists():
            os.remove(temp_sub_file)
