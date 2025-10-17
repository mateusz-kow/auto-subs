import json
from logging import getLogger
from typing import Any, overload

from autosubs.core.builder import create_dict_from_subtitles
from autosubs.models.settings import AssSettings
from autosubs.models.subtitles import Subtitles
from autosubs.models.subtitles.ass import AssSubtitles, AssSubtitleSegment

logger = getLogger(__name__)
ASS_NEWLINE = r"\\N"  # Can't put these in f-strings for compatibility issues with python 3.11


def format_srt_timestamp(seconds: float) -> str:
    """Formats seconds to SRT timestamp format (hh:mm:ss,ms).

    Args:
        seconds: The time in seconds.

    Returns:
        The formatted timestamp string.
    """
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def format_vtt_timestamp(seconds: float) -> str:
    """Formats seconds to VTT timestamp format (hh:mm:ss.ms).

    Args:
        seconds: The time in seconds.

    Returns:
        The formatted timestamp string.
    """
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02}.{millis:03}"


def format_ass_timestamp(seconds: float) -> str:
    """Formats seconds to ASS timestamp format (h:mm:ss.cs).

    Args:
        seconds: The time in seconds.

    Returns:
        The formatted timestamp string.
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    # Correctly round 0.5 up instead of to the nearest even number.
    cs = int((seconds - s - m * 60 - h * 3600) * 100 + 0.5)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def _reconstruct_dialogue_text(segment: AssSubtitleSegment) -> str:
    parts: list[str] = []
    for word in segment.words:
        tag_string = "".join(style.ass_tag for style in word.styles)
        text = word.text.replace("\n", r"\N")
        parts.append(f"{tag_string}{text}")
    return "".join(parts)


def _format_ass_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


@overload
def to_ass(subtitles: AssSubtitles) -> str: ...
@overload
def to_ass(subtitles: Subtitles, settings: AssSettings) -> str: ...
def to_ass(subtitles: Subtitles, settings: AssSettings | None = None) -> str:
    """Generate the content for an ASS subtitle file.

    This function is overloaded. If given an AssSubtitles object, it performs
    a lossless regeneration. If given a generic Subtitles object, it generates
    a new ASS file from scratch using the provided settings.

    Args:
        subtitles: The Subtitles or AssSubtitles object.
        settings: Settings for generation from scratch. Ignored for AssSubtitles.

    Returns:
        The full content of the .ass file as a string.
    """
    if isinstance(subtitles, AssSubtitles):
        logger.info("Regenerating subtitles from AssSubtitles object (lossless)...")
        lines: list[str] = []

        lines.append("[Script Info]")
        for key, value in sorted(subtitles.script_info.items()):
            lines.append(f"{key}: {value}")
        lines.append("")

        lines.append("[V4+ Styles]")
        if subtitles.styles:
            style_format_keys = subtitles.style_format_keys
            if not style_format_keys:
                # Fallback for programmatically created objects
                style_format_keys = [
                    field.alias or name for name, field in type(subtitles.styles[0]).model_fields.items()
                ]
            lines.append(f"Format: {', '.join(style_format_keys)}")

            for style in subtitles.styles:
                style_dict = style.model_dump(by_alias=True)
                values: list[str] = []
                for key in style_format_keys:
                    # Use .get() with a default of None to handle keys present in format but not in model
                    style_value: Any = style_dict.get(key)
                    if isinstance(style_value, bool):
                        values.append("-1" if style_value else "0")
                    elif isinstance(style_value, (float, int)):
                        values.append(_format_ass_number(style_value))
                    else:
                        values.append(str(style_value) if style_value is not None else "")
                lines.append(f"Style: {','.join(values)}")
        lines.append("")

        lines.append("[Events]")
        if subtitles.segments:
            events_format_keys = subtitles.events_format_keys
            if not events_format_keys:
                # Fallback for programmatically created objects
                events_format_keys = [
                    "Layer",
                    "Start",
                    "End",
                    "Style",
                    "Name",
                    "MarginL",
                    "MarginR",
                    "MarginV",
                    "Effect",
                    "Text",
                ]
            lines.append(f"Format: {', '.join(events_format_keys)}")

            for segment in subtitles.segments:
                start_ts = format_ass_timestamp(segment.start)
                end_ts = format_ass_timestamp(segment.end)
                text = _reconstruct_dialogue_text(segment)
                dialogue_data = {
                    "Layer": str(segment.layer),
                    "Start": start_ts,
                    "End": end_ts,
                    "Style": segment.style_name,
                    "Name": segment.actor_name,
                    "MarginL": str(segment.margin_l),
                    "MarginR": str(segment.margin_r),
                    "MarginV": str(segment.margin_v),
                    "Effect": segment.effect,
                    "Text": text,
                }
                values = [dialogue_data.get(key, "") for key in events_format_keys]
                lines.append(f"Dialogue: {','.join(values)}")

        return "\n".join(lines) + "\n"

    logger.info("Generating subtitles in ASS format from scratch...")
    actual_settings = settings or AssSettings()
    lines = [actual_settings.to_ass_header()]

    if actual_settings.highlight_style:
        for seg in subtitles.segments:
            start = format_ass_timestamp(seg.start)
            end = format_ass_timestamp(seg.end)
            karaoke_text = "".join(
                f"{{\\k{int(round((word.end - word.start) * 100))}}}{word.text} " for word in seg.words
            ).rstrip()
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{karaoke_text}")
    else:
        for seg in subtitles.segments:
            start = format_ass_timestamp(seg.start)
            end = format_ass_timestamp(seg.end)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{seg.text.replace(chr(10), ASS_NEWLINE)}")

    result = "\n".join(lines)
    return f"{result}\n" if subtitles.segments else result


def to_srt(subtitles: Subtitles) -> str:
    """Generate the content for an SRT subtitle file.

    Args:
        subtitles: The Subtitles object containing the segments.

    Returns:
        The full content of the .srt file as a string.
    """
    logger.info("Generating subtitles in SRT format...")
    srt_blocks: list[str] = []
    for i, segment in enumerate(subtitles.segments, 1):
        start_time = format_srt_timestamp(segment.start)
        end_time = format_srt_timestamp(segment.end)
        srt_blocks.append(f"{i}\n{start_time} --> {end_time}\n{segment.text}")

    if not srt_blocks:
        return ""

    return "\n\n".join(srt_blocks) + "\n\n"


def to_vtt(subtitles: Subtitles) -> str:
    """Generate the content for a VTT subtitle file.

    Args:
        subtitles: The Subtitles object containing the segments.

    Returns:
        The full content of the .vtt file as a string.
    """
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
    """Generate a JSON representation of the subtitles.

    The output format is compatible with Whisper's transcription result.

    Args:
        subtitles: The Subtitles object containing the segments.

    Returns:
        A JSON string representing the subtitles.
    """
    logger.info("Generating subtitles in JSON format...")
    return json.dumps(create_dict_from_subtitles(subtitles), indent=4, ensure_ascii=False)
