from auto_subs.models.settings import AssSettings
from auto_subs.models.subtitles import Subtitles


def _format_srt_timestamp(seconds: float) -> str:
    """Formats seconds to SRT timestamp format (hh:mm:ss,ms).

    Args:
        seconds: The time in seconds.

    Returns:
        The formatted timestamp string.
    """
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def _format_ass_timestamp(seconds: float) -> str:
    """Formats seconds to ASS timestamp format (h:mm:ss.cs).

    Args:
        seconds: The time in seconds.

    Returns:
        The formatted timestamp string.
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def to_ass(subtitles: Subtitles, settings: AssSettings) -> str:
    """Generate the content for an ASS subtitle file.

    Args:
        subtitles: The Subtitles object containing the segments.
        settings: The settings for the ASS file.

    Returns:
        The full content of the .ass file as a string.
    """
    lines: list[str] = [settings.to_ass_header()]

    for segment in subtitles.segments:
        start = _format_ass_timestamp(segment.start)
        end = _format_ass_timestamp(segment.end)
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{segment}")

    return "\n".join(lines)


def to_srt(subtitles: Subtitles) -> str:
    """Generate the content for an SRT subtitle file.

    Args:
        subtitles: The Subtitles object containing the segments.

    Returns:
        The full content of the .srt file as a string.
    """
    srt_blocks: list[str] = []
    for i, segment in enumerate(subtitles.segments, 1):
        start_time = _format_srt_timestamp(segment.start)
        end_time = _format_srt_timestamp(segment.end)
        srt_blocks.append(f"{i}\n{start_time} --> {end_time}\n{segment}\n")
    return "\n".join(srt_blocks)


def to_txt(subtitles: Subtitles) -> str:
    """Generate plain text content from the given subtitles.

    Args:
        subtitles: The Subtitles object containing the segments.

    Returns:
        The full transcription as a single string.
    """
    return str(subtitles)
