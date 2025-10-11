from collections.abc import Generator
from enum import Enum, auto
from pathlib import Path

import typer


class SupportedExtension(Enum):
    """Enumeration for supported file types for CLI commands."""

    MEDIA = auto()
    SUBTITLE = auto()
    JSON = auto()


_EXTENSION_MAP: dict[SupportedExtension, set[str]] = {
    SupportedExtension.MEDIA: {".mp3", ".mp4", ".m4a", ".mkv", ".avi", ".wav", ".flac"},
    SupportedExtension.SUBTITLE: {".srt", ".vtt", ".ass"},
    SupportedExtension.JSON: {".json"},
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
