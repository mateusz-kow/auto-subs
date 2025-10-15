"""Core module for parsing subtitle file formats."""

import re
from logging import getLogger

from autosubs.models import AssSubtitles
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)

# Regex for timestamps
SRT_TIMESTAMP_REGEX = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
VTT_TIMESTAMP_REGEX = re.compile(r"(?:(\d{1,2}):)?(\d{2}):(\d{2})\.(\d{3})")
ASS_TIMESTAMP_REGEX = re.compile(r"(\d):(\d{2}):(\d{2})\.(\d{2})")
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


def parse_ass(file_content: str) -> AssSubtitles:
    """Parses content from an ASS file into a rich AssSubtitles object.

    Args:
        file_content: The full content of the ASS file.

    Returns:
        An AssSubtitles object representing the file content.
    """
    raise NotImplementedError("The ASS parser has not been implemented yet.")
