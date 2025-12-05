from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import generate as generate_api
from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
    process_batch,
    write_content_to_file,
)
from autosubs.models.enums import EncodingErrorStrategy
from autosubs.models.formats import SubtitleFormat


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
        SubtitleFormat | None,
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Format for the output subtitles. Inferred from --output if not specified.",
        ),
    ] = None,
    max_chars: Annotated[int, typer.Option(help="Maximum characters per subtitle line.")] = 35,
    min_words: Annotated[
        int,
        typer.Option(help="Minimum words per line before allowing a punctuation break."),
    ] = 1,
    max_lines: Annotated[
        int,
        typer.Option(help="Maximum number of lines per subtitle segment."),
    ] = 1,
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
    """Generate subtitle file from a transcription JSON."""
    target_format = determine_output_format(output_format, output_path, default=SubtitleFormat.SRT)
    typer.echo(f"Generating subtitles in {target_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.JSON)

    def _generate_single(in_file: Path, out_base: Path) -> None:
        typer.echo(f"Processing: {in_file.name}")
        final_out = out_base.with_suffix(f".{target_format.value}")

        content = generate_api(
            in_file,
            output_format=target_format,
            max_chars=max_chars,
            min_words=min_words,
            max_lines=max_lines,
            style_config_path=style_config,
            encoding=encoding,
        )

        write_content_to_file(final_out, content, output_encoding, output_encoding_errors)

    process_batch(processor, _generate_single)
