"""Core module for parsing subtitle file formats."""

import dataclasses
from collections.abc import Callable
from logging import getLogger
from typing import Any

import regex as re

from autosubs.models import (
    AssSubtitles,
    AssSubtitleSegment,
    AssSubtitleWord,
    SubtitleSegment,
    SubtitleWord,
    WordStyleRange,
)
from autosubs.models.subtitles.ass import AssTagBlock

logger = getLogger(__name__)

SRT_TIMESTAMP_REGEX = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
VTT_TIMESTAMP_REGEX = re.compile(r"(?:(\d{1,2}):)?(\d{2}):(\d{2})\.(\d{3})")
ASS_TIMESTAMP_REGEX = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{2})")
MPL2_TIMESTAMP_REGEX = re.compile(r"\[(\d+)]\[(\d+)](.+)")
ASS_STYLE_TAG_REGEX = re.compile(r"{[^}]+}")
MICRODVD_TIMESTAMP_REGEX = re.compile(r"\{(\d+)\}\{(\d+)\}(.*)")


def srt_timestamp_to_seconds(timestamp: str) -> float:
    """Converts an SRT timestamp string to seconds."""
    match = SRT_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid SRT timestamp format: {timestamp}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def vtt_timestamp_to_seconds(timestamp: str) -> float:
    """Converts a VTT timestamp string to seconds."""
    match = VTT_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid VTT timestamp format: {timestamp}")
    h_str, m_str, s_str, ms_str = match.groups()
    h = int(h_str) if h_str else 0
    m, s, ms = int(m_str), int(s_str), int(ms_str)
    return h * 3600 + m * 60 + s + ms / 1000


def ass_timestamp_to_seconds(timestamp: str) -> float:
    """Converts an ASS timestamp string to seconds."""
    match = ASS_TIMESTAMP_REGEX.match(timestamp)
    if not match:
        raise ValueError(f"Invalid ASS timestamp format: {timestamp}")
    h, m, s, cs = map(int, match.groups())
    return h * 3600 + m * 60 + s + cs / 100


def microdvd_frames_to_seconds(start_frame: int, end_frame: int, fps: float) -> tuple[float, float]:
    """Converts MicroDVD frame numbers to start and end seconds."""
    return start_frame / fps, end_frame / fps


def mpl2_timestamp_to_seconds(deciseconds: str) -> float:
    """Converts an MPL2 timestamp (in deciseconds) string to seconds."""
    return int(deciseconds) / 10


def parse_srt(file_content: str) -> list[SubtitleSegment]:
    """Parses content from an SRT file into subtitle segments."""
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
    """Parses content from a VTT file into subtitle segments."""
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


def _parse_ass_tag_block(tag_content: str) -> AssTagBlock:
    """Parses the content of an ASS style tag block."""
    if not tag_content:
        return AssTagBlock()

    def _parse_bool(key: str) -> Callable[[str, dict[str, Any]], None]:
        return lambda value, kwargs: kwargs.update({key: value.endswith("1")})

    def _parse_float(key: str) -> Callable[[str, dict[str, Any]], None]:
        return lambda value, kwargs: kwargs.update({key: float(value)})

    def _parse_int(key: str) -> Callable[[str, dict[str, Any]], None]:
        return lambda value, kwargs: kwargs.update({key: int(value)})

    def _parse_str(key: str) -> Callable[[str, dict[str, Any]], None]:
        return lambda value, kwargs: kwargs.update({key: value})

    def _parse_pos(key_x: str, key_y: str) -> Callable[[str, dict[str, Any]], None]:
        def parser(value: str, kwargs: dict[str, Any]) -> None:
            x, y = [float(v) for v in value.split(",")]
            kwargs.update({key_x: x, key_y: y})

        return parser

    def _parse_fad(value: str, kwargs: dict[str, Any]) -> None:
        t1, t2 = [int(v) for v in value.split(",")]
        kwargs["fade"] = (t1, t2)

    _dispatch_table = {
        # Boolean styles
        "b": _parse_bool("bold"),
        "i": _parse_bool("italic"),
        "u": _parse_bool("underline"),
        "s": _parse_bool("strikeout"),
        # Font
        "fn": _parse_str("font_name"),
        "fs": _parse_float("font_size"),
        # Colors
        "c": _parse_str("primary_color"),
        "1c": _parse_str("primary_color"),
        "2c": _parse_str("secondary_color"),
        "3c": _parse_str("outline_color"),
        "4c": _parse_str("shadow_color"),
        "alpha": _parse_str("alpha"),
        # Layout
        "an": _parse_int("alignment"),
        "pos": _parse_pos("position_x", "position_y"),
        "org": _parse_pos("origin_x", "origin_y"),
        # Spacing/Scaling
        "fsp": _parse_float("spacing"),
        "fscx": _parse_float("scale_x"),
        "fscy": _parse_float("scale_y"),
        # Rotation
        "frx": _parse_float("rotation_x"),
        "fry": _parse_float("rotation_y"),
        "frz": _parse_float("rotation_z"),
        # Effects
        "bord": _parse_float("border"),
        "shad": _parse_float("shadow"),
        "blur": _parse_float("blur"),
        "fad": _parse_fad,
    }

    tag_pattern = re.compile(r"\\(t)\(((?:[^()]+|\((?2)\))*)\)|\\([1-4]c|[a-zA-Z]+)(?:\(([^)]*)\)|([^\\]*))")

    kwargs: dict[str, Any] = {}
    transforms: list[str] = []
    unknown_tags: list[str] = []

    for match in tag_pattern.finditer(tag_content):
        t_tag, t_val, tag, paren_val, simple_val = match.groups()

        if t_tag == "t":
            transforms.append(t_val)
            continue

        if tag == "r":
            kwargs.clear()
            transforms.clear()
            unknown_tags.clear()
            continue

        value_str = paren_val if paren_val is not None else simple_val
        if value_str is None:
            continue
        value_str = value_str.strip()

        parser = _dispatch_table.get(tag)
        if parser:
            try:
                parser(value_str, kwargs)
            except (ValueError, IndexError):
                logger.warning(f"Could not parse ASS tag: \\{tag}{value_str}")
        else:
            unknown_tags.append(match.group(0).lstrip("\\"))

    if transforms:
        kwargs["transforms"] = tuple(transforms)
    if unknown_tags:
        kwargs["unknown_tags"] = tuple(unknown_tags)

    return AssTagBlock(**kwargs)


def _parse_dialogue_text(text: str, start: float, end: float) -> list[AssSubtitleWord]:
    processed_text = text.replace(r"\N", "\n").replace(r"\n", "\n")
    tokens = [t for t in re.split(r"({[^}]+})", processed_text) if t]
    text_content = ASS_STYLE_TAG_REGEX.sub("", processed_text)
    total_chars = len(text_content)
    duration = end - start

    words: list[AssSubtitleWord] = []
    current_time = start
    pending_blocks: list[AssTagBlock] = []

    for token in tokens:
        if token.startswith("{") and token.endswith("}"):
            content = token[1:-1]
            pending_blocks.append(_parse_ass_tag_block(content))
        else:
            char_count = len(token)
            word_duration = (duration * char_count / total_chars) if total_chars > 0 else 0
            word = AssSubtitleWord(text=token, start=current_time, end=current_time + word_duration)
            if pending_blocks:
                merged_block = AssTagBlock()
                for block in pending_blocks:
                    changes = {
                        f.name: getattr(block, f.name)
                        for f in dataclasses.fields(block)
                        if getattr(block, f.name) is not None
                        and (not isinstance(getattr(block, f.name), list) or getattr(block, f.name))
                    }
                    if "transforms" in changes:
                        changes["transforms"] = merged_block.transforms + changes["transforms"]
                    if "unknown_tags" in changes:
                        changes["unknown_tags"] = merged_block.unknown_tags + changes["unknown_tags"]

                    if changes:
                        merged_block = dataclasses.replace(merged_block, **changes)

                word.styles = [WordStyleRange(0, len(token), merged_block)]
                pending_blocks.clear()
            words.append(word)
            current_time += word_duration

    if pending_blocks:
        final_word = AssSubtitleWord(text="", start=end, end=end)
        final_word.styles = [WordStyleRange(0, 0, block) for block in pending_blocks]
        words.append(final_word)

    return words


def parse_ass(file_content: str) -> AssSubtitles:
    """Parses content from an ASS file into a rich AssSubtitles object.

    This parser handles standard ASS sections ([Script Info], [V4+ Styles], [Events])
    as well as custom sections (e.g., [Fonts], [Graphics], [Aegisub Project Garbage]).

    Parsing behavior:
        - Empty lines are skipped in all sections
        - Comment lines (starting with semicolon) are skipped in all sections
        - Custom sections store raw line content with trailing whitespace stripped
        - Leading whitespace is preserved in custom sections

    Note: UUEncoded data in custom sections (like [Fonts] and [Graphics]) that
    happens to start with a semicolon on a line will be skipped. While rare in
    practice (UUEncoded lines typically start with 'M' or other characters), users
    should be aware that custom sections follow the same parsing rules as standard
    sections.

    Args:
        file_content: The complete text content of an ASS file.

    Returns:
        AssSubtitles object with parsed content including custom sections.
    """
    logger.info("Parsing ASS file content.")
    subs = AssSubtitles()
    current_section = ""

    for raw_line in file_content.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        # Skip empty lines and comments (lines starting with semicolon) in all sections.
        # This applies to standard sections and custom sections alike.
        if not line or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line
            # Initialize custom section storage if it's not a standard section
            if current_section not in ["[Script Info]", "[V4+ Styles]", "[Events]"]:
                subs.custom_sections[current_section] = []
            continue

        if current_section and current_section in subs.custom_sections:
            # Store raw line for custom sections (with trailing whitespace stripped).
            # Leading whitespace is preserved to maintain formatting of UUEncoded data.
            subs.custom_sections[current_section].append(raw_line.rstrip())
            continue

        key, _, value = line.partition(":")
        value = value.strip()

        if current_section == "[Script Info]":
            subs.script_info[key.strip()] = value
        elif current_section == "[V4+ Styles]":
            if key.lower() == "format":
                subs.style_format_keys = [k.strip() for k in value.split(",")]
            elif key.lower() == "style":
                logger.warning("Parsing of [V4+ Styles] is deprecated and will be removed.")
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


def parse_microdvd(file_content: str, fps: float | None = None) -> list[SubtitleSegment]:
    """Parses content from a MicroDVD file into subtitle segments."""
    logger.info("Parsing MicroDVD file content.")
    segments: list[SubtitleSegment] = []
    lines = file_content.strip().replace("\r\n", "\n").splitlines()

    if not lines:
        return segments

    # Check for FPS in the first line, e.g., {1}{1}23.976
    first_line_match = re.match(r"\{1\}\{1\}([\d\.]+)", lines[0])
    if first_line_match:
        if fps is None:
            try:
                fps = float(first_line_match.group(1))
                logger.info(f"Detected FPS from MicroDVD header: {fps}")
            except ValueError:
                logger.warning("Invalid FPS value in MicroDVD header, ignoring.")
        lines.pop(0)

    if fps is None:
        raise ValueError("FPS must be provided to parse MicroDVD files.")
    if fps <= 0:
        raise ValueError("FPS must be a positive number.")

    for line in lines:
        match = MICRODVD_TIMESTAMP_REGEX.match(line)
        if not match:
            logger.warning(f"Skipping malformed MicroDVD line: {line}")
            continue

        try:
            start_frame, end_frame, text = int(match.group(1)), int(match.group(2)), match.group(3)
            text = text.replace("|", "\n")

            start_time, end_time = microdvd_frames_to_seconds(start_frame, end_frame, fps)

            if start_time > end_time:
                logger.warning(f"Skipping MicroDVD line with invalid timestamp (start > end): {line}")
                continue

            word = SubtitleWord(text=text, start=start_time, end=end_time)
            segments.append(SubtitleSegment(words=[word]))
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed MicroDVD line: {line} ({e})")
            continue

    return segments


def parse_mpl2(file_content: str) -> list[SubtitleSegment]:
    """Parses content from an MPL2 file into subtitle segments."""
    logger.info("Parsing MPL2 file content.")
    segments: list[SubtitleSegment] = []
    lines = file_content.strip().replace("\r\n", "\n").split("\n")

    for line in lines:
        match = MPL2_TIMESTAMP_REGEX.match(line)
        if not match:
            if line.strip():
                logger.warning(f"Skipping malformed MPL2 line: {line}")
            continue

        try:
            start_ds, end_ds, text = match.groups()
            start_time = mpl2_timestamp_to_seconds(start_ds)
            end_time = mpl2_timestamp_to_seconds(end_ds)
            text = text.replace("|", "\n")

            if start_time > end_time:
                logger.warning(f"Skipping MPL2 line with invalid timestamp (start > end): {line}")
                continue

            word = SubtitleWord(text=text, start=start_time, end=end_time)
            segments.append(SubtitleSegment(words=[word]))
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed MPL2 line: {line} ({e})")
            continue
    return segments
