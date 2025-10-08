from logging import getLogger

from auto_subs.models.settings import AssSettings, AssStyleSettings
from auto_subs.models.subtitles import Subtitles

logger = getLogger(__name__)

HIGHLIGHT_END = r"{\\r}"


# --- Helper Functions (remain the same) ---


def _format_srt_timestamp(seconds: float) -> str:
    """Formats seconds to SRT timestamp format (hh:mm:ss,ms)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def _format_ass_timestamp(seconds: float) -> str:
    """Formats seconds to ASS timestamp format (h:mm:ss.cs)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def _build_ass_highlight_tag(style: AssStyleSettings) -> str:
    """Builds ASS highlight tags from a style object."""
    tag_parts = []
    if style.text_color:
        tag_parts.append(rf"\1c{style.text_color}")
    if style.border_color:
        tag_parts.append(rf"\3c{style.border_color}")
    if style.fade:
        tag_parts.append(r"\fad(50,50)")
    return f"{{{''.join(tag_parts)}}}"


# --- Public API Functions (no longer in a class) ---


def to_ass(subtitles: Subtitles, settings: AssSettings) -> str:
    """Generate the content for an ASS subtitle file."""
    lines = [settings.to_ass_header()]

    if settings.highlight_style:
        highlight_tag = _build_ass_highlight_tag(settings.highlight_style)
        for segment in subtitles.segments:
            words = [word.text for word in segment.words]
            for i, word in enumerate(segment.words):
                start = _format_ass_timestamp(word.start)
                next_word_start = segment.words[i + 1].start if i + 1 < len(segment.words) else segment.end
                end = _format_ass_timestamp(next_word_start)

                highlighted_words = words.copy()
                highlighted_words[i] = f"{highlight_tag}{word.text}{HIGHLIGHT_END}"
                text_line = " ".join(highlighted_words)

                lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text_line}")
    else:
        for segment in subtitles.segments:
            start = _format_ass_timestamp(segment.start)
            end = _format_ass_timestamp(segment.end)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{segment}")

    lines.append("")
    return "\n".join(lines)


def to_srt(subtitles: Subtitles) -> str:
    """Generate the content for an SRT subtitle file."""
    srt_blocks = []
    for i, segment in enumerate(subtitles.segments, 1):
        start_time = _format_srt_timestamp(segment.start)
        end_time = _format_srt_timestamp(segment.end)
        srt_blocks.append(f"{i}\n{start_time} --> {end_time}\n{segment}\n")
    return "\n".join(srt_blocks)


def to_txt(subtitles: Subtitles) -> str:
    """Generate plain text content from the given subtitles."""
    return str(subtitles)
