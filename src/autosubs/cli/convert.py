from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import load
from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
    get_generator_func,
    process_batch,
    write_content_to_file,
)
from autosubs.models.enums import EncodingErrorStrategy
from autosubs.models.formats import SubtitleFormat
from autosubs.models.subtitles import Subtitles


def convert(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="Path to a subtitle file (.srt, .vtt, .ass, .smi) or a directory of such files.",
        ),
    ],
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the converted subtitle file or directory. "
            "Defaults to the input path with a new extension.",
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
    encoding: Annotated[
        str | None,
        typer.Option(
            "--encoding",
            "-e",
            help="Encoding of the input file(s). Auto-detected if not specified.",
        ),
    ] = None,
    output_encoding: Annotated[
        str,
        typer.Option(
            "--output-encoding",
            help="Encoding for the output file(s). Defaults to utf-8.",
        ),
    ] = "utf-8",
    output_encoding_errors: Annotated[
        EncodingErrorStrategy,
        typer.Option(
            "--output-encoding-errors",
            case_sensitive=False,
            help="How to handle encoding errors for the output file(s). "
            "Defaults to 'replace', which substitutes unencodable characters.",
        ),
    ] = EncodingErrorStrategy.REPLACE,
) -> None:
    """Convert subtitle files to a different format."""
    target_format = determine_output_format(output_format, output_path, default=SubtitleFormat.SRT)
    typer.echo(f"Converting subtitles to {target_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.SUBTITLE)
    writer_func = get_generator_func(target_format)

    def _convert_single(in_file: Path, out_base: Path) -> None:
        typer.echo(f"Processing: {in_file.name}")

        final_out = out_base.with_suffix(f".{target_format.value}")
        subtitles: Subtitles = load(in_file, encoding=encoding)
        content = writer_func(subtitles)

        write_content_to_file(final_out, content, output_encoding, output_encoding_errors)

    process_batch(processor, _convert_single)
