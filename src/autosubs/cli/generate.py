from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import generate as generate_api
from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
)
from autosubs.models.formats import SubtitleFormat


class EncodingErrorStrategy(StrEnum):
    REPLACE = "replace"
    IGNORE = "ignore"
    STRICT = "strict"
    XMLCHARREFREPLACE = "xmlcharrefreplace"
    BACKSLASHREPLACE = "backslashreplace"
    NAMEREPLACE = "namereplace"


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
            help="How to handle encoding errors for the output file(s).",
        ),
    ] = EncodingErrorStrategy.REPLACE,
) -> None:
    """Generate a subtitle file from a transcription JSON."""
    final_output_format = determine_output_format(output_format, output_path)

    typer.echo(f"Generating subtitles in {final_output_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.JSON)
    is_batch = input_path.is_dir()
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Processing: {in_file.name}")
        if is_batch:
            out_file = out_file_base.with_name(f"{in_file.stem}.{final_output_format.value}")
        else:
            out_file = out_file_base.with_suffix(f".{final_output_format.value}")

        try:
            content = generate_api(
                in_file,
                output_format=final_output_format,
                max_chars=max_chars,
                min_words=min_words,
                max_lines=max_lines,
                style_config_path=style_config,
                encoding=encoding,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding=output_encoding, errors=output_encoding_errors.value)
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)

        except UnicodeEncodeError as e:
            typer.secho(
                f"Error processing file {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True
        except ValueError as e:
            typer.secho(
                f"Input file validation error for {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True
        except (OSError, ImportError, LookupError) as e:
            typer.secho(
                f"Error processing file {in_file.name}: {e}",
                fg=typer.colors.RED,
            )
            has_errors = True

    if has_errors:
        raise typer.Exit(code=1)
