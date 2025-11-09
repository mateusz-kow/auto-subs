"""Core module for parsing subtitle file formats."""

import re
from logging import getLogger
from typing import Any

from autosubs.models import AssSubtitles, AssSubtitleSegment, AssSubtitleWord
from autosubs.models.styles import AssStyle, WordStyleRange
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)

# Regex for timestamps
SRT_TIMESTAMP_REGEX = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
VTT_TIMESTAMP_REGEX = re.compile(r"(?:(\d{1,2}):)?(\d{2}):(\d{2})\.(\d{3})")
ASS_TIMESTAMP_REGEX = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{2})")
ASS_STYLE_TAG_REGEX = re.compile(r"{[^}]+}")


def srt_timestamp_to_seconds(timestamp: str) -> float:
    """Converts an SRT timestamp string to seconds.

    Args:
        timestamp: The timestamp string in hh:mm:ss,ms format.

    Returns:
        The time in seconds.

    Raises:
        ValueError: If the timestamp format is invalid.
    """
    match = SRT_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid SRT timestamp format: {timestamp}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def vtt_timestamp_to_seconds(timestamp: str) -> float:
    """Converts a VTT timestamp string to seconds.

    Args:
        timestamp: The timestamp string in [hh:]mm:ss.ms format.

    Returns:
        The time in seconds.

    Raises:
        ValueError: If the timestamp format is invalid.
    """
    match = VTT_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid VTT timestamp format: {timestamp}")
    h_str, m_str, s_str, ms_str = match.groups()
    h = int(h_str) if h_str else 0
    m, s, ms = int(m_str), int(s_str), int(ms_str)
    return h * 3600 + m * 60 + s + ms / 1000


def ass_timestamp_to_seconds(timestamp: str) -> float:
    """Converts an ASS timestamp string to seconds.

    Args:
        timestamp: The timestamp string in h:mm:ss.cs format.

    Returns:
        The time in seconds.

    Raises:
        ValueError: If the timestamp format is invalid.
    """
    match = ASS_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid ASS timestamp format: {timestamp}")
    h, m, s, cs = map(int, match.groups())
    return h * 3600 + m * 60 + s + cs / 100


def parse_srt(file_content: str) -> list[SubtitleSegment]:
    """Parses content from an SRT file into subtitle segments.

    Args:
        file_content: The full content of the SRT file.

    Returns:
        A list of parsed subtitle segments.
    """
    logger.info("Parsing SRT file content.")
    segments: list[SubtitleSegment] = []
    blocks = file_content.strip().replace("\r\n", "\n").split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 2:
            continue

        try:
            timestamp_line_index = 1 if lines[0].isdigit() else 0
            timestamp_line = lines[timestamp_line_index]
            text = "\n".join(lines[timestamp_line_index + 1 :])
            if "-->" not in timestamp_line:
                continue

            start_str, end_str = (part.strip() for part in timestamp_line.split("-->"))
            start_time = srt_timestamp_to_seconds(start_str)
            end_time = srt_timestamp_to_seconds(end_str)

            if start_time > end_time:
                logger.warning(f"Skipping SRT block with invalid timestamp (start > end): {block}")
                continue

            word = SubtitleWord(text=text, start=start_time, end=end_time)
            segments.append(SubtitleSegment(words=[word]))
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed SRT block: {block} ({e})")
            continue
    return segments


def parse_vtt(file_content: str) -> list[SubtitleSegment]:
    """Parses content from a VTT file into subtitle segments.

    Args:
        file_content: The full content of the VTT file.

    Returns:
        A list of parsed subtitle segments.
    """
    logger.info("Parsing VTT file content.")
    segments: list[SubtitleSegment] = []
    content = re.sub(r"^WEBVTT.*\n", "", file_content).strip()
    blocks = content.replace("\r\n", "\n").split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        timestamp_line = ""
        text_start_index = -1
        for i, line in enumerate(lines):
            if "-->" in line:
                timestamp_line = line
                text_start_index = i + 1
                break
        if not timestamp_line:
            continue

        try:
            start_str, end_str_full = timestamp_line.split("-->")
            end_str = end_str_full.strip().split(" ")[0]
            start_time = vtt_timestamp_to_seconds(start_str.strip())
            end_time = vtt_timestamp_to_seconds(end_str)
            text = "\n".join(lines[text_start_index:])

            if start_time > end_time:
                logger.warning(f"Skipping VTT block with invalid timestamp (start > end): {block}")
                continue

            word = SubtitleWord(text=text, start=start_time, end=end_time)
            segments.append(SubtitleSegment(words=[word]))
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed VTT block: {block} ({e})")
            continue
    return segments


def _parse_dialogue_text(text: str, start: float, end: float) -> list[AssSubtitleWord]:
    processed_text = text.replace(r"\N", "\n").replace(r"\n", "\n")
    tokens = [t for t in re.split(r"({[^}]+})", processed_text) if t]
    text_content = ASS_STYLE_TAG_REGEX.sub("", processed_text)
    total_chars = len(text_content)
    duration = end - start

    words: list[AssSubtitleWord] = []
    current_time = start
    pending_tags: list[str] = []

    for token in tokens:
        if token.startswith("{") and token.endswith("}"):
            pending_tags.append(token)
        else:
            char_count = len(token)
            word_duration = (duration * char_count / total_chars) if total_chars > 0 else 0
            word = AssSubtitleWord(text=token, start=current_time, end=current_time + word_duration)
            if pending_tags:
                word.styles = [WordStyleRange(0, len(token), tag) for tag in pending_tags]
                pending_tags.clear()
            words.append(word)
            current_time += word_duration

    if pending_tags:
        final_word = AssSubtitleWord(text="", start=end, end=end)
        final_word.styles = [WordStyleRange(0, 0, tag) for tag in pending_tags]
        words.append(final_word)

    return words


def parse_ass(file_content: str) -> AssSubtitles:
    """Parses content from an ASS file into a rich AssSubtitles object.

    Args:
        file_content: The full content of the ASS file.

    Returns:
        An AssSubtitles object representing the file content.
    """
    logger.info("Parsing ASS file content.")
    subs = AssSubtitles()
    current_section = ""

    for raw_line in file_content.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line
            continue

        key, _, value = line.partition(":")
        value = value.strip()

        if current_section == "[Script Info]":
            subs.script_info[key.strip()] = value
        elif current_section == "[V4+ Styles]":
            if key.lower() == "format":
                subs.style_format_keys = [k.strip() for k in value.split(",")]
            elif key.lower() == "style":
                if not subs.style_format_keys:
                    logger.warning("Skipping Style line found before Format line.")
                    continue
                style_values = [v.strip() for v in value.split(",", len(subs.style_format_keys) - 1)]
                style_dict: dict[str, Any] = dict(zip(subs.style_format_keys, style_values, strict=False))
                for bool_key in ["Bold", "Italic", "Underline", "StrikeOut"]:
                    if bool_key in style_dict:
                        try:
                            style_dict[bool_key] = bool(int(style_dict[bool_key]))
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse boolean value for {bool_key}: {style_dict[bool_key]}")
                            style_dict.pop(bool_key)
                subs.styles.append(AssStyle.model_validate(style_dict, from_attributes=True))
        elif current_section == "[Events]":
            if key.lower() == "format":
                subs.events_format_keys = [k.strip() for k in value.split(",")]
            elif key.lower() == "dialogue":
                if not subs.events_format_keys:
                    logger.warning("Skipping Dialogue line found before Format line.")
                    continue

                required_fields = {"Start", "End", "Text"}
                if not required_fields.issubset(subs.events_format_keys):
                    raise ValueError(
                        f"ASS 'Format' line is missing required fields: "
                        f"{required_fields - set(subs.events_format_keys)}"
                    )

                try:
                    dialogue_values = [v.strip() for v in value.split(",", len(subs.events_format_keys) - 1)]
                    dialogue_dict = dict(zip(subs.events_format_keys, dialogue_values, strict=False))

                    start_time = ass_timestamp_to_seconds(dialogue_dict["Start"])
                    end_time = ass_timestamp_to_seconds(dialogue_dict["End"])
                    if start_time > end_time:
                        logger.warning(f"Skipping ASS Dialogue with invalid timestamp (start > end): {line}")
                        continue

                    words = _parse_dialogue_text(dialogue_dict["Text"], start_time, end_time)
                    segment = AssSubtitleSegment(
                        words=words,
                        layer=int(dialogue_dict.get("Layer", 0)),
                        style_name=dialogue_dict.get("Style", "Default"),
                        actor_name=dialogue_dict.get("Name", ""),
                        margin_l=int(dialogue_dict.get("MarginL", 0)),
                        margin_r=int(dialogue_dict.get("MarginR", 0)),
                        margin_v=int(dialogue_dict.get("MarginV", 0)),
                        effect=dialogue_dict.get("Effect", ""),
                    )
                    subs.segments.append(segment)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping malformed ASS Dialogue line: {line} ({e})")
                    continue
    return subs
