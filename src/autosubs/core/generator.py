import json
from logging import getLogger

from autosubs.models.settings import AssSettings
from autosubs.models.subtitles import Subtitles

logger = getLogger(__name__)


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


def to_ass(subtitles: Subtitles, settings: AssSettings) -> str:
    """Generate the content for an ASS subtitle file.

    Args:
        subtitles: The Subtitles object containing the segments.
        settings: The settings for the ASS file.

    Returns:
        The full content of the .ass file as a string.
    """
    logger.info("Generating subtitles in ASS format...")
    lines: list[str] = [settings.to_ass_header()]

    if settings.highlight_style:
        for segment in subtitles.segments:
            start = format_ass_timestamp(segment.start)
            end = format_ass_timestamp(segment.end)
            karaoke_text = "".join(
                f"{{\\k{int(round((word.end - word.start) * 100))}}}{word.text} " for word in segment.words
            ).rstrip()
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{karaoke_text}")
    else:
        for segment in subtitles.segments:
            start = format_ass_timestamp(segment.start)
            end = format_ass_timestamp(segment.end)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{segment}")

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
        srt_blocks.append(f"{i}\n{start_time} --> {end_time}\n{segment}")

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
        vtt_blocks.append(f"{start_time} --> {end_time}\n{segment}")

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
    return json.dumps(subtitles.to_transcription_dict(), indent=2, ensure_ascii=False)
