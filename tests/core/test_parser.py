import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core import parser
from autosubs.models.subtitles import AssSubtitles


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
        parser.srt_timestamp_to_seconds("00:00:00.000")  # Wrong separator
    with pytest.raises(ValueError):
        parser.srt_timestamp_to_seconds("0:0:0,0")  # Wrong padding


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
        parser.vtt_timestamp_to_seconds("00:00,000")  # Wrong separator
    with pytest.raises(ValueError):
        parser.vtt_timestamp_to_seconds("0:0:0.0")  # Wrong padding on some parts


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
        parser.ass_timestamp_to_seconds("0:00:00,00")  # Wrong separator
    with pytest.raises(ValueError):
        parser.ass_timestamp_to_seconds("0:0:0.0")  # Wrong padding


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


def test_parse_srt_skips_block_without_arrow() -> None:
    """Test that an SRT block is skipped if the timestamp line lacks '-->'."""
    content = "1\n00:00:00,500 00:00:01,500\nNo arrow\n\n2\n00:00:02,000 --> 00:00:03,000\nGood block"
    segments = parser.parse_srt(content)
    assert len(segments) == 1
    assert str(segments[0].text) == "Good block"


def test_parse_srt_handles_malformed_timestamps_and_continues() -> None:
    """Test that the SRT parser skips blocks with bad timestamps and continues."""
    content = (
        "1\n00:00:00,500 --> 00:00:01,500\nFirst good block\n\n"
        "2\n00:00:02.000 --> 00:00:03.000\nBad timestamp format\n\n"
        "3\n00:00:04,000 --> 00:00:05,000\nSecond good block"
    )
    segments = parser.parse_srt(content)
    assert len(segments) == 2
    assert str(segments[0].text) == "First good block"
    assert str(segments[1].text) == "Second good block"


def test_parse_vtt_success(sample_vtt_content: str) -> None:
    """Test successful parsing of a valid VTT file."""
    segments = parser.parse_vtt(sample_vtt_content)
    assert len(segments) == 2
    assert segments[0].start == 0.5
    assert segments[0].end == 1.5
    assert str(segments[0].text) == "Hello world."
    assert segments[1].start == 2.0
    assert segments[1].end == 3.0
    assert str(segments[1].text) == "This is a test."


def test_parse_vtt_with_metadata(sample_vtt_content: str) -> None:
    """Test that the VTT parser ignores metadata and still parses correctly."""
    content_with_metadata = "WEBVTT - Test File\n\nNOTE\nThis is a note.\n\n" + sample_vtt_content.replace("WEBVTT", "")
    segments = parser.parse_vtt(content_with_metadata)
    assert len(segments) == 2
    assert str(segments[0].text) == "Hello world."


def test_parse_vtt_handles_malformed_blocks_and_continues() -> None:
    """Test that the VTT parser skips blocks with bad timestamps and continues."""
    content = (
        "WEBVTT\n\n"
        "00:00:00.500 --> 00:00:01.500\nFirst good block\n\n"
        "00:00:02,000 --> 00:00:03,000\nBad timestamp format\n\n"
        "00:00:04.000 --> 00:00:05.000\nSecond good block"
    )
    segments = parser.parse_vtt(content)
    assert len(segments) == 2
    assert str(segments[0].text) == "First good block"
    assert str(segments[1].text) == "Second good block"


def test_parse_ass_success(sample_ass_content: str) -> None:
    """Test successful parsing of a valid ASS file."""
    subs = parser.parse_ass(sample_ass_content)
    assert isinstance(subs, AssSubtitles)
    assert len(subs.segments) == 3
    assert subs.segments[0].start == 0.5
    assert pytest.approx(subs.segments[0].end) == 1.5
    assert subs.segments[0].text == "Hello world."
    # Test that style tags are stripped from the .text property
    assert subs.segments[1].start == 2.0
    assert pytest.approx(subs.segments[1].end) == 3.0
    assert subs.segments[1].text == "This is a test with bold tags."
    # Test that \N is converted to a newline
    assert subs.segments[2].start == 4.1
    assert pytest.approx(subs.segments[2].end) == 5.9
    assert subs.segments[2].text == "And a\nnew line."


def test_parse_ass_stops_at_new_section() -> None:
    """Test that the ASS parser stops reading events at a new section."""
    content = (
        "[Events]\nFormat: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,First line\n"
        "[Fonts]\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Should be ignored"
    )
    subs = parser.parse_ass(content)
    assert len(subs.segments) == 1
    assert str(subs.segments[0].text) == "First line"


def test_parse_ass_raises_on_missing_required_format_fields() -> None:
    """Test that ASS parser raises ValueError if Format line is missing key fields."""
    content = "[Events]\nFormat: Layer, Style, Effect\nDialogue: 0,Default,,"
    with pytest.raises(ValueError, match="ASS 'Format' line is missing required fields"):
        parser.parse_ass(content)


def test_parse_ass_skips_malformed_dialogue_line() -> None:
    """Test that the ASS parser skips a malformed Dialogue line and continues."""
    content = (
        "[Events]\nFormat: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,First line\n"
        "Dialogue: 0:00:03.00,bad-timestamp,Malformed line\n"
        "Dialogue: 0:00:05.00,0:00:06.00,Third line\n"
    )
    subs = parser.parse_ass(content)
    assert len(subs.segments) == 2
    assert str(subs.segments[0].text) == "First line"
    assert str(subs.segments[1].text) == "Third line"


def test_parse_srt_skips_incomplete_blocks() -> None:
    """Test that the SRT parser skips blocks with fewer than 2 lines."""
    content = (
        "1\n00:00:00,500 --> 00:00:01,500\nFirst good block\n\n"
        "2\n\n"  # Malformed block with only one line
        "3\n00:00:04,000 --> 00:00:05,000\nSecond good block"
    )
    segments = parser.parse_srt(content)
    assert len(segments) == 2
    assert str(segments[0].text) == "First good block"
    assert str(segments[1].text) == "Second good block"


def test_parse_srt_skips_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that SRT blocks with start > end are skipped with a warning."""
    content = "1\n00:00:02,000 --> 00:00:01,000\nInverted timestamp\n\n2\n00:00:03,000 --> 00:00:04,000\nGood block"
    segments = parser.parse_srt(content)
    assert len(segments) == 1
    assert str(segments[0].text) == "Good block"
    assert "Skipping SRT block with invalid timestamp (start > end)" in caplog.text


def test_parse_vtt_skips_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that VTT blocks with start > end are skipped with a warning."""
    content = "WEBVTT\n\n00:02.000 --> 00:01.000\nInverted timestamp\n\n00:03.000 --> 00:04.000\nGood block"
    segments = parser.parse_vtt(content)
    assert len(segments) == 1
    assert str(segments[0].text) == "Good block"
    assert "Skipping VTT block with invalid timestamp (start > end)" in caplog.text


def test_parse_ass_skips_dialogue_before_format(caplog: LogCaptureFixture) -> None:
    """Test that the ASS parser skips Dialogue lines that appear before the Format line."""
    content = (
        "[Events]\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Should be ignored\n"
        "Format: Start, End, Text\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Should be parsed"
    )
    subs = parser.parse_ass(content)
    assert len(subs.segments) == 1
    assert str(subs.segments[0].text) == "Should be parsed"
    assert "Skipping Dialogue line found before Format line" in caplog.text


def test_parse_ass_skips_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that ASS Dialogue lines with start > end are skipped with a warning."""
    content = (
        "[Events]\n"
        "Format: Start, End, Text\n"
        "Dialogue: 0:00:02.00,0:00:01.00,Inverted timestamp\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Good dialogue"
    )
    subs = parser.parse_ass(content)
    assert len(subs.segments) == 1
    assert str(subs.segments[0].text) == "Good dialogue"
    assert "Skipping ASS Dialogue with invalid timestamp (start > end)" in caplog.text
