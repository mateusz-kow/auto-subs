import os
import shutil
import tempfile
from collections.abc import Callable, Generator
from enum import Enum, auto
from pathlib import Path

import typer

from autosubs.api import _DEFAULT_STYLE_CONFIG
from autosubs.core import generator
from autosubs.core.burner import FFmpegError, burn_subtitles
from autosubs.core.styler import AssStyler
from autosubs.models.enums import EncodingErrorStrategy
from autosubs.models.formats import SubtitleFormat
from autosubs.models.subtitles import Subtitles


class SupportedExtension(Enum):
    """Enumeration for supported file types for CLI commands."""

    MEDIA = auto()
    SUBTITLE = auto()
    JSON = auto()
    VIDEO = auto()


_EXTENSION_MAP: dict[SupportedExtension, set[str]] = {
    SupportedExtension.MEDIA: {".mp3", ".mp4", ".m4a", ".mkv", ".avi", ".wav", ".flac", ".mov", ".webm"},
    SupportedExtension.SUBTITLE: {".srt", ".vtt", ".ass", ".txt", ".sub", ".smi"},
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
        """Initializes the path processor."""
        self.input_path = input_path
        self.output_path = output_path
        self.extensions = _EXTENSION_MAP[extension_type]
        self._validate_paths()

    def _validate_paths(self) -> None:
        if self.input_path.is_dir() and self.output_path and not self.output_path.is_dir():
            typer.secho(
                "Error: If input is a directory, output must also be a directory.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    def _get_files_from_dir(self) -> list[Path]:
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
        """Yields tuples of (input_file, output_file_base_path) for processing."""
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
                out_base = (
                    self.output_path / file.stem if self.output_path.is_dir() else self.output_path.with_suffix("")
                )
            else:
                out_base = file.with_suffix("")
            yield file, out_base


def determine_output_format(
    output_format_option: SubtitleFormat | None,
    output_path_option: Path | None,
    input_path: Path | None = None,
    default: SubtitleFormat | None = None,
) -> SubtitleFormat:
    """Unified logic to determine output format from flags, filenames, or defaults."""
    if output_format_option:
        return output_format_option

    # Try checking the explicitly provided output path extension
    if output_path_option and not output_path_option.is_dir():
        suffix = output_path_option.suffix.lstrip(".").lower()
        if suffix:
            try:
                return SubtitleFormat(suffix)
            except ValueError:
                pass

    # If allowed, try checking the input path extension (e.g. for conversions)
    if input_path:
        suffix = input_path.suffix.lstrip(".").lower()
        try:
            return SubtitleFormat(suffix)
        except ValueError:
            pass

    if default:
        typer.secho(f"No output format specified or inferred. Defaulting to {default.upper()}.", fg=typer.colors.YELLOW)
        return default

    raise typer.BadParameter(
        "Cannot determine output format. Please specify --format or provide an output path with a valid extension."
    )


def get_default_styler_engine() -> AssStyler:
    """Creates an AssStyler with a minimal default configuration."""
    domain_config = _DEFAULT_STYLE_CONFIG.to_domain()
    return AssStyler(domain_config)


def get_generator_func(fmt: SubtitleFormat) -> Callable[[Subtitles], str]:
    """Returns the appropriate generator function for the format."""
    _map = {
        SubtitleFormat.SRT: generator.to_srt,
        SubtitleFormat.VTT: generator.to_vtt,
        SubtitleFormat.ASS: lambda s: generator.to_ass(s, styler_engine=get_default_styler_engine()),
        SubtitleFormat.JSON: generator.to_json,
        SubtitleFormat.MPL2: generator.to_mpl2,
        SubtitleFormat.MICRODVD: lambda s: generator.to_microdvd(
            s, fps=23.976
        ),  # Fallback FPS; frame-based formats require explicit FPS
    }
    if fmt not in _map:
        raise ValueError(f"Unsupported format for generation: {fmt}")
    return _map[fmt]


def write_content_to_file(
    path: Path, content: str, encoding: str = "utf-8", errors: EncodingErrorStrategy = EncodingErrorStrategy.REPLACE
) -> None:
    """Helper to ensure parent dirs exist and write content."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding, errors=errors)
        typer.secho(f"Successfully saved to: {path}", fg=typer.colors.GREEN)
    except OSError as e:
        typer.secho(f"Error writing file {path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


def process_batch(
    processor: PathProcessor, process_func: Callable[[Path, Path], None], continue_on_error: bool = True
) -> None:
    """Generic loop for processing a batch of files.

    Args:
        processor: The initialized PathProcessor.
        process_func: A callback taking (input_file, output_base_path).
                      It should raise specific exceptions or handle logic.
        continue_on_error: Determines whether function should continue on error
    """
    has_errors = False

    for in_file, out_base in processor.process():
        try:
            process_func(in_file, out_base)
        except Exception as e:
            typer.secho(f"Error processing {in_file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            if not continue_on_error:
                break

    if has_errors:
        raise typer.Exit(code=1)


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
    """Helper function for handling burn operation."""
    if styling_options_used and subtitle_format in {SubtitleFormat.SRT, SubtitleFormat.VTT}:
        typer.secho("Warning: Burning SRT/VTT ignores style config.", fg=typer.colors.YELLOW)

    typer.secho("Starting video burn process...", fg=typer.colors.CYAN)

    temp_sub = None
    try:
        suffix = f".{subtitle_format.value}"
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as f:
            temp_sub = Path(f.name)
            f.write(subtitle_content)

        burn_subtitles(video_input, temp_sub, video_output)
        typer.secho(f"Successfully burned into: {video_output}", fg=typer.colors.GREEN)
    except (FFmpegError, Exception) as e:
        typer.secho(f"Burn failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    finally:
        if temp_sub and temp_sub.exists():
            os.remove(temp_sub)
