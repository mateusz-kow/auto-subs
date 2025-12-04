from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import _DEFAULT_STYLE_CONFIG, load
from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
)
from autosubs.core import generator
from autosubs.core.styler import AssStyler
from autosubs.models.formats import SubtitleFormat
from autosubs.models.subtitles import Subtitles


def _get_default_styler_engine() -> AssStyler:
    """Creates an AssStyler with a minimal default configuration."""
    domain_config = _DEFAULT_STYLE_CONFIG.to_domain()
    return AssStyler(domain_config)


_format_map: dict[SubtitleFormat, Callable[..., str]] = {
    SubtitleFormat.SRT: generator.to_srt,
    SubtitleFormat.VTT: generator.to_vtt,
    SubtitleFormat.ASS: lambda subs: generator.to_ass(subs, styler_engine=_get_default_styler_engine()),
    SubtitleFormat.JSON: generator.to_json,
}


class EncodingErrorStrategy(StrEnum):
    REPLACE = "replace"
    IGNORE = "ignore"
    STRICT = "strict"
    XMLCHARREFREPLACE = "xmlcharrefreplace"
    BACKSLASHREPLACE = "backslashreplace"
    NAMEREPLACE = "namereplace"


def convert(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="Path to a subtitle file (.srt, .vtt, .ass) or a directory of such files.",
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
            help="How to handle encoding errors for the output file(s).",
        ),
    ] = EncodingErrorStrategy.REPLACE,
) -> None:
    """Convert an existing subtitle file to a different format."""
    final_output_format = determine_output_format(output_format, output_path)

    typer.echo(f"Converting subtitles to {final_output_format.upper()} format...")

    processor = PathProcessor(input_path, output_path, SupportedExtension.SUBTITLE)
    is_batch = input_path.is_dir()
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Processing: {in_file.name}")

        if is_batch:
            out_file = out_file_base.with_name(f"{in_file.name}.{final_output_format.value}")
        else:
            out_file = out_file_base.with_suffix(f".{final_output_format.value}")

        try:
            subtitles: Subtitles = load(in_file, encoding=encoding)
            writer_func = _format_map[final_output_format]
            content = writer_func(subtitles)

            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding=output_encoding, errors=output_encoding_errors.value)
            typer.secho(
                f"Successfully saved converted subtitles to: {out_file}",
                fg=typer.colors.GREEN,
            )
        except (OSError, ValueError, ImportError, LookupError) as e:
            typer.secho(f"Error processing file {in_file.name}: {e}", fg=typer.colors.RED)
            has_errors = True
            continue

    if has_errors:
        raise typer.Exit(code=1)
