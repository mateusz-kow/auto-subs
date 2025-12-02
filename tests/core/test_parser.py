import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core import parser


@pytest.mark.parametrize(
    ("timestamp", "expected_seconds"),
    [
        ("00:00:00,000", 0.0),
        ("00:01:01,525", 61.525),
        ("01:01:01,000", 3661.0),
    ],
)
def test_srt_timestamp_to_seconds(timestamp: str, expected_seconds: float) -> None:
    """Test conversion of valid SRT timestamps to seconds."""
    assert parser.srt_timestamp_to_seconds(timestamp) == expected_seconds


def test_srt_timestamp_to_seconds_invalid() -> None:
    """Test that invalid SRT timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser.srt_timestamp_to_seconds("00:00:00.000")
    with pytest.raises(ValueError):
        parser.srt_timestamp_to_seconds("0:0:0,0")


@pytest.mark.parametrize(
    ("timestamp", "expected_seconds"),
    [
        ("00:00.000", 0.0),
        ("01:01.525", 61.525),
        ("01:01:01.000", 3661.0),
    ],
)
def test_vtt_timestamp_to_seconds(timestamp: str, expected_seconds: float) -> None:
    """Test conversion of valid VTT timestamps to seconds."""
    assert parser.vtt_timestamp_to_seconds(timestamp) == expected_seconds


def test_vtt_timestamp_to_seconds_invalid() -> None:
    """Test that invalid VTT timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser.vtt_timestamp_to_seconds("00:00,000")
    with pytest.raises(ValueError):
        parser.vtt_timestamp_to_seconds("0:0:0.0")


@pytest.mark.parametrize(
    ("timestamp", "expected_seconds"),
    [
        ("0:00:00.00", 0.0),
        ("0:01:01.52", 61.52),
        ("1:01:01.00", 3661.0),
    ],
)
def test_ass_timestamp_to_seconds(timestamp: str, expected_seconds: float) -> None:
    """Test conversion of valid ASS timestamps to seconds."""
    assert parser.ass_timestamp_to_seconds(timestamp) == expected_seconds


def test_ass_timestamp_to_seconds_invalid() -> None:
    """Test that invalid ASS timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser.ass_timestamp_to_seconds("0:00:00,00")
    with pytest.raises(ValueError):
        parser.ass_timestamp_to_seconds("0:0:0.0")


def test_parse_srt_success(sample_srt_content: str) -> None:
    """Test successful parsing of a valid SRT file."""
    segments = parser.parse_srt(sample_srt_content)
    assert len(segments) == 2
    assert segments[0].start == 0.5
    assert segments[0].end == 1.5
    assert segments[0].text == "Hello world."
    assert segments[1].start == 2.0
    assert segments[1].end == 3.0
    assert str(segments[1].text) == "This is a test."


def test_parse_ass_skips_style_lines(caplog: LogCaptureFixture) -> None:
    """Test that ASS Style lines are now skipped with a warning."""
    content = "[V4+ Styles]\nStyle: Bad,Arial,20\nFormat: Name,Fontname,Fontsize\n"
    subs = parser.parse_ass(content)
    assert not hasattr(subs, "styles")
    assert "Parsing of [V4+ Styles] is deprecated" in caplog.text


def test_parse_ass_handles_nested_transform_tag() -> None:
    """Test that ASS parser correctly handles transform tags with nested parentheses."""
    content = (
        "[Events]\n"
        "Format: Start, End, Text\n"
        r"Dialogue: 0:00:00.00,0:00:01.00,{\t(0,500,\clip(0,0,10,10))}Test"
    )
    subs = parser.parse_ass(content)
    assert len(subs.segments) == 1
    segment = subs.segments[0]
    assert len(segment.words) == 1
    word = segment.words[0]
    assert word.text == "Test"
    assert len(word.styles) == 1
    style_range = word.styles[0]
    assert style_range.tag_block.transforms == [r"0,500,\clip(0,0,10,10)"]


def test_parse_srt_handles_short_blocks() -> None:
    """Test that blocks with fewer than 2 lines are skipped."""
    content = "1\n\n00:00:00,000 --> 00:00:01,000\nLine 2"
    segments = parser.parse_srt(content)
    assert len(segments) == 1
    assert segments[0].text == "Line 2"


def test_parse_srt_handles_no_timestamp_arrow() -> None:
    """Test that lines without '-->' are skipped."""
    content = "1\n00:00:00,000 00:00:01,000\nInvalid\n\n2\n00:00:02,000 --> 00:00:03,000\nValid"
    segments = parser.parse_srt(content)
    assert len(segments) == 1
    assert segments[0].text == "Valid"


def test_parse_srt_handles_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that blocks with start > end are skipped with a warning."""
    content = "1\n00:00:02,000 --> 00:00:01,000\nInverted"
    segments = parser.parse_srt(content)
    assert not segments
    assert "Skipping SRT block with invalid timestamp (start > end)" in caplog.text


def test_parse_srt_handles_malformed_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that blocks with malformed timestamps are skipped with a warning."""
    content = "1\n00:00:bad --> 00:00:01,000\nMalformed"
    segments = parser.parse_srt(content)
    assert not segments
    assert "Skipping malformed SRT block" in caplog.text


def test_parse_vtt_handles_no_timestamp_line() -> None:
    """Test that VTT blocks without a timestamp line are skipped."""
    content = "WEBVTT\n\nJust text\n\n00:00:02.000 --> 00:00:03.000\nValid"
    segments = parser.parse_vtt(content)
    assert len(segments) == 1
    assert segments[0].text == "Valid"


def test_parse_vtt_handles_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that VTT blocks with start > end are skipped with a warning."""
    content = "WEBVTT\n\n00:00:02.000 --> 00:00:01.000\nInverted"
    segments = parser.parse_vtt(content)
    assert not segments
    assert "Skipping VTT block with invalid timestamp (start > end)" in caplog.text


def test_parse_vtt_handles_malformed_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that VTT blocks with malformed timestamps are skipped with a warning."""
    content = "WEBVTT\n\n00:bad --> 00:00:01.000\nMalformed"
    segments = parser.parse_vtt(content)
    assert not segments
    assert "Skipping malformed VTT block" in caplog.text
