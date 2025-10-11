import pytest

from auto_subs.core import generator
from auto_subs.models.settings import AssSettings
from auto_subs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_subtitles() -> Subtitles:
    """Provides a sample Subtitles object for testing."""
    words1 = [
        SubtitleWord("Hello", 0.5, 1.0),
        SubtitleWord("world.", 1.1, 1.5),
    ]
    words2 = [
        SubtitleWord("This", 2.0, 2.2),
        SubtitleWord("is", 2.3, 2.4),
        SubtitleWord("a", 2.5, 2.6),
        SubtitleWord("test.", 2.7, 3.0),
    ]
    segment1 = SubtitleSegment(words1)
    segment2 = SubtitleSegment(words2)
    return Subtitles([segment1, segment2])


@pytest.fixture
def empty_subtitles() -> Subtitles:
    """Provides an empty Subtitles object for testing."""
    return Subtitles([])


def test_to_srt(sample_subtitles: Subtitles) -> None:
    """Test SRT generation."""
    expected_srt = (
        "1\n00:00:00,500 --> 00:00:01,500\nHello world.\n\n2\n00:00:02,000 --> 00:00:03,000\nThis is a test.\n\n"
    )
    assert generator.to_srt(sample_subtitles) == expected_srt


def test_to_srt_empty(empty_subtitles: Subtitles) -> None:
    """Test SRT generation with empty subtitles."""
    expected_srt = ""
    assert generator.to_srt(empty_subtitles) == expected_srt


def test_to_ass(sample_subtitles: Subtitles) -> None:
    """Test ASS generation."""
    settings = AssSettings()
    header = settings.to_ass_header()
    expected_ass = (
        f"{header}\n"  # Add newline to match the join behavior in the function
        "Dialogue: 0,0:00:00.50,0:00:01.50,Default,,0,0,0,,Hello world.\n"
        "Dialogue: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,This is a test.\n"
    )
    assert generator.to_ass(sample_subtitles, settings) == expected_ass


def test_to_ass_empty(empty_subtitles: Subtitles) -> None:
    """Test empty ASS generation."""
    settings = AssSettings()
    header = settings.to_ass_header()
    expected_ass = f"{header}"  # Add newline to match the join behavior in the function
    assert generator.to_ass(empty_subtitles, settings) == expected_ass


def test_to_vtt(sample_subtitles: Subtitles) -> None:
    """Test VTT generation."""
    vtt_subtitles = generator.to_vtt(sample_subtitles)
    expected_subtitles = (
        "WEBVTT\n\n00:00:00.500 --> 00:00:01.500\nHello world.\n\n00:00:02.000 --> 00:00:03.000\nThis is a test.\n"
    )
    assert vtt_subtitles.strip() == expected_subtitles.strip()


def test_to_vtt_empty(empty_subtitles: Subtitles) -> None:
    """Test VTT generation with empty subtitles."""
    vtt_subtitles = generator.to_vtt(empty_subtitles)
    assert "WEBVTT" in vtt_subtitles
    assert vtt_subtitles == "WEBVTT\n"


def test_format_srt_timestamp() -> None:
    """Test SRT timestamp formatting."""
    assert generator._format_srt_timestamp(0) == "00:00:00,000"
    assert generator._format_srt_timestamp(61.525) == "00:01:01,525"
    assert generator._format_srt_timestamp(3661.0) == "01:01:01,000"


def test_format_ass_timestamp() -> None:
    """Test ASS timestamp formatting."""
    assert generator._format_ass_timestamp(0) == "0:00:00.00"
    assert generator._format_ass_timestamp(61.525) == "0:01:01.52"
    assert generator._format_ass_timestamp(3661.0) == "1:01:01.00"
