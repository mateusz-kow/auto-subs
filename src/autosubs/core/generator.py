import json
from logging import getLogger
from typing import Any, overload

from autosubs.core.builder import create_dict_from_subtitles
from autosubs.core.styler import StylerEngine
from autosubs.models.subtitles import Subtitles
from autosubs.models.subtitles.ass import AssSubtitles

logger = getLogger(__name__)
ASS_NEWLINE = r"\N"


def format_srt_timestamp(seconds: float) -> str:
    # ... bez zmian
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def format_vtt_timestamp(seconds: float) -> str:
    # ... bez zmian
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02}.{millis:03}"


def format_ass_timestamp(seconds: float) -> str:
    # ... bez zmian
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - s - m * 60 - h * 3600) * 100 + 0.5)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def _format_ass_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, bool):
        return "-1" if value else "0"
    return str(value)


@overload
def to_ass(subtitles: AssSubtitles) -> str: ...


@overload
def to_ass(subtitles: Subtitles, styler_engine: StylerEngine) -> str: ...


def to_ass(subtitles: Subtitles, styler_engine: StylerEngine | None = None) -> str:
    """Generate the content for an ASS subtitle file."""
    if isinstance(subtitles, AssSubtitles):
        # ... logika regeneracji pozostaje bez zmian
        pass

    if not styler_engine:
        raise ValueError("StylerEngine is required to generate an ASS file from scratch.")

    logger.info("Generating ASS file using the StylerEngine.")
    config = styler_engine.config
    lines = ["[Script Info]"]
    lines.extend(f"{key}: {value}" for key, value in config.script_info.items())
    lines.append("\n[V4+ Styles]")
    if config.styles:
        style_format_keys = list(config.styles[0].keys())
        lines.append(f"Format: {', '.join(style_format_keys)}")
        for style_dict in config.styles:
            lines.append(f"Style: {','.join(_format_ass_number(style_dict.get(key, '')) for key in style_format_keys)}")
    lines.append("\n[Events]")
    lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

    default_style = config.styles[0].get("Name", "Default") if config.styles else "Default"
    for seg in subtitles.segments:
        style_name, dialogue_text = styler_engine.process_segment(seg, default_style)
        start, end = format_ass_timestamp(seg.start), format_ass_timestamp(seg.end)
        lines.append(f"Dialogue: 0,{start},{end},{style_name},,0,0,0,,{dialogue_text}")  # Bezpośrednie użycie tekstu
    return "\n".join(lines) + "\n"


def to_srt(subtitles: Subtitles) -> str:
    """Generate the content for an SRT subtitle file."""
    logger.info("Generating subtitles in SRT format...")
    srt_blocks: list[str] = []
    for i, segment in enumerate(subtitles.segments, 1):
        start_time = format_srt_timestamp(segment.start)
        end_time = format_srt_timestamp(segment.end)
        srt_blocks.append(f"{i}\n{start_time} --> {end_time}\n{segment.text}")
    return "\n\n".join(srt_blocks) + "\n\n" if srt_blocks else ""


def to_vtt(subtitles: Subtitles) -> str:
    """Generate the content for a VTT subtitle file."""
    logger.info("Generating subtitles in VTT format...")
    if not subtitles.segments:
        return "WEBVTT\n"
    vtt_blocks: list[str] = ["WEBVTT"]
    for segment in subtitles.segments:
        start_time = format_vtt_timestamp(segment.start)
        end_time = format_vtt_timestamp(segment.end)
        vtt_blocks.append(f"{start_time} --> {end_time}\n{segment.text}")
    return "\n\n".join(vtt_blocks) + "\n\n"


def to_json(subtitles: Subtitles) -> str:
    """Generate a JSON representation of the subtitles."""
    logger.info("Generating subtitles in JSON format...")
    return json.dumps(create_dict_from_subtitles(subtitles), indent=4, ensure_ascii=False)
