import json
from logging import getLogger
from typing import Any, overload

from autosubs.core.builder import create_dict_from_subtitles
from autosubs.core.styler import AssStyler
from autosubs.models.subtitles import Subtitles
from autosubs.models.subtitles.ass import AssSubtitles, AssSubtitleSegment

logger = getLogger(__name__)
ASS_NEWLINE = r"\N"


def format_srt_timestamp(seconds: float) -> str:
    """Formats srt timestamps."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def format_vtt_timestamp(seconds: float) -> str:
    """Formats vtt timestamps."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02}:{mins:02}:{secs:02}.{millis:03}"


def format_ass_timestamp(seconds: float) -> str:
    """Formats ass timestamps."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - s - m * 60 - h * 3600) * 100 + 0.5)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def seconds_to_microdvd_frame(seconds: float, fps: float) -> int:
    """Converts seconds to a MicroDVD frame number."""
    return round(seconds * fps)


def format_mpl2_timestamp(seconds: float) -> str:
    """Formats mpl2 timestamps."""
    return str(int(round(seconds * 10)))


def _reconstruct_dialogue_text(segment: AssSubtitleSegment) -> str:
    parts: list[str] = []
    for word in segment.words:
        tag_string = "".join(style.tag_block.to_ass_string() for style in word.styles)
        text = word.text.replace("\n", r"\N")
        parts.append(f"{tag_string}{text}")
    return "".join(parts)


def _format_ass_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, bool):
        return "-1" if value else "0"
    return str(value)


@overload
def to_ass(subtitles: AssSubtitles) -> str: ...


@overload
def to_ass(subtitles: Subtitles, styler_engine: AssStyler) -> str: ...


def to_ass(subtitles: Subtitles, styler_engine: AssStyler | None = None) -> str:
    """Generate the content for an ASS subtitle file."""
    if isinstance(subtitles, AssSubtitles):
        logger.info("Regenerating ASS file from AssSubtitles object...")
        lines: list[str] = []

        lines.append("[Script Info]")
        lines.extend(f"{key}: {value}" for key, value in sorted(subtitles.script_info.items()))
        lines.append("")

        lines.append("[V4+ Styles]")
        styles_to_use = []
        if styler_engine and styler_engine.config.styles:
            styles_to_use = styler_engine.config.styles
            format_keys = list(styles_to_use[0].keys())
        elif subtitles.styles:
            styles_to_use = subtitles.styles
            format_keys = subtitles.style_format_keys or list(styles_to_use[0].keys())

        if styles_to_use:
            lines.append(f"Format: {', '.join(format_keys)}")
            for style_dict in styles_to_use:
                values = [_format_ass_number(style_dict.get(key, "")) for key in format_keys]
                lines.append(f"Style: {','.join(values)}")
        else:
            logger.warning("No styles found in model or styler; [V4+ Styles] section will be empty.")

        lines.append("[Events]")
        if subtitles.segments:
            events_format_keys = subtitles.events_format_keys
            if not events_format_keys:
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
                dialogue_data = {
                    "Layer": segment.layer,
                    "Start": format_ass_timestamp(segment.start),
                    "End": format_ass_timestamp(segment.end),
                    "Style": segment.style_name,
                    "Name": segment.actor_name,
                    "MarginL": segment.margin_l,
                    "MarginR": segment.margin_r,
                    "MarginV": segment.margin_v,
                    "Effect": segment.effect,
                    "Text": _reconstruct_dialogue_text(segment),
                }
                values = [str(dialogue_data.get(key, "")) for key in events_format_keys]
                lines.append(f"Dialogue: {','.join(values)}")

        # Add custom sections
        for section_name, section_lines in subtitles.custom_sections.items():
            lines.append("")
            lines.append(section_name)
            lines.extend(section_lines)

        return "\n".join(lines) + "\n"

    if not styler_engine:
        raise ValueError("AssStyler is required to generate an ASS file from scratch.")

    logger.info("Generating ASS file using the AssStyler.")
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
        result = styler_engine.process_segment(seg, default_style)
        start, end = format_ass_timestamp(seg.start), format_ass_timestamp(seg.end)

        # We can assume it's AssStylingResult because we are in to_ass
        lines.append(f"Dialogue: 0,{start},{end},{result.style_name},,0,0,0,,{result.text}")
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


def to_microdvd(subtitles: Subtitles, fps: float, include_fps_header: bool = False) -> str:
    """Generate the content for a MicroDVD subtitle file."""
    if not fps or fps <= 0:
        raise ValueError("A positive FPS value is required to generate MicroDVD files.")

    logger.info(f"Generating subtitles in MicroDVD format with FPS={fps}...")
    microdvd_lines: list[str] = []
    if include_fps_header:
        microdvd_lines.append(f"{{1}}{{1}}{fps}")
    for segment in subtitles.segments:
        start_frame = seconds_to_microdvd_frame(segment.start, fps)
        end_frame = seconds_to_microdvd_frame(segment.end, fps)
        text = segment.text.replace("\n", "|")
        microdvd_lines.append(f"{{{start_frame}}}{{{end_frame}}}{text}")
    return "\n".join(microdvd_lines) + "\n" if microdvd_lines else ""


def to_mpl2(subtitles: Subtitles) -> str:
    """Generate the content for an MPL2 subtitle file."""
    logger.info("Generating subtitles in MPL2 format...")
    mpl2_lines: list[str] = []
    for segment in subtitles.segments:
        start_time = format_mpl2_timestamp(segment.start)
        end_time = format_mpl2_timestamp(segment.end)
        text = segment.text.replace("\n", "|")
        mpl2_lines.append(f"[{start_time}][{end_time}]{text}")
    return "\n".join(mpl2_lines) + "\n" if mpl2_lines else ""


def to_json(subtitles: Subtitles) -> str:
    """Generate a JSON representation of the subtitles."""
    logger.info("Generating subtitles in JSON format...")
    return json.dumps(create_dict_from_subtitles(subtitles), indent=4, ensure_ascii=False)
