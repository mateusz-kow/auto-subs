import json
from pathlib import Path
from typing import Annotated

import typer

from autosubs.api import transcribe as transcribe_api
from autosubs.cli.utils import PathProcessor, SupportedExtension
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings, AssStyleSettings
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
    # ASS Options
    karaoke: Annotated[
        bool,
        typer.Option(help="[ASS] Enable karaoke-style word highlighting."),
    ] = False,
    style_file: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="[ASS] Path to a JSON file with ASS style settings.",
        ),
    ] = None,
    font_name: Annotated[str | None, typer.Option(help="[ASS] Font name.")] = None,
    font_size: Annotated[int | None, typer.Option(help="[ASS] Font size.")] = None,
    primary_color: Annotated[str | None, typer.Option(help="[ASS] Primary color.")] = None,
    secondary_color: Annotated[str | None, typer.Option(help="[ASS] Secondary color.")] = None,
    outline_color: Annotated[str | None, typer.Option(help="[ASS] Outline color.")] = None,
    back_color: Annotated[str | None, typer.Option(help="[ASS] Back color (shadow).")] = None,
    bold: Annotated[bool | None, typer.Option(help="[ASS] Enable bold text.")] = None,
    italic: Annotated[bool | None, typer.Option(help="[ASS] Enable italic text.")] = None,
    underline: Annotated[bool | None, typer.Option(help="[ASS] Enable underlined text.")] = None,
    alignment: Annotated[int | None, typer.Option(help="[ASS] Numpad alignment (e.g., 2 for bottom-center).")] = None,
    margin_v: Annotated[int | None, typer.Option(help="[ASS] Vertical margin.")] = None,
) -> None:
    """Transcribe a media file and generate subtitles."""
    final_output_format = output_format
    if output_path and not final_output_format:
        suffix = output_path.suffix.lower().strip(".")
        if suffix and suffix in SubtitleFormat.__members__.values():
            final_output_format = SubtitleFormat(suffix)

    if not final_output_format:
        final_output_format = SubtitleFormat.SRT
        typer.secho("No output format specified. Defaulting to SRT.", fg=typer.colors.YELLOW)

    ass_settings: AssSettings | None = None
    if final_output_format == SubtitleFormat.ASS:
        settings_dict = {}
        if style_file:
            with style_file.open("r", encoding="utf-8") as f:
                settings_dict = json.load(f)

        cli_opts = {
            "font": font_name,
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
    elif karaoke:
        typer.secho(
            "Warning: --karaoke flag is only applicable for ASS format.",
            fg=typer.colors.YELLOW,
        )

    processor = PathProcessor(media_path, output_path, SupportedExtension.MEDIA)
    is_batch = media_path.is_dir()
    has_errors = False

    for in_file, out_file_base in processor.process():
        typer.echo(f"Transcribing: {in_file.name} (using '{model.value}' model)")

        if is_batch:
            out_file = out_file_base.with_name(f"{in_file.stem}.{final_output_format.value}")
        else:
            out_file = out_file_base.with_suffix(f".{final_output_format.value}")

        try:
            content = transcribe_api(
                in_file,
                output_format=final_output_format,
                model_name=model,
                max_chars=max_chars,
                min_words=min_words,
                ass_settings=ass_settings,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")
            typer.secho(f"Successfully saved subtitles to: {out_file}", fg=typer.colors.GREEN)
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
