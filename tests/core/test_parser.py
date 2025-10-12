import pytest

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
    assert parser._srt_timestamp_to_seconds(timestamp) == expected_seconds


def test_srt_timestamp_to_seconds_invalid() -> None:
    """Test that invalid SRT timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser._srt_timestamp_to_seconds("00:00:00.000")  # Wrong separator
    with pytest.raises(ValueError):
        parser._srt_timestamp_to_seconds("0:0:0,0")  # Wrong padding


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
    assert parser._vtt_timestamp_to_seconds(timestamp) == expected_seconds


def test_vtt_timestamp_to_seconds_invalid() -> None:
    """Test that invalid VTT timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser._vtt_timestamp_to_seconds("00:00,000")  # Wrong separator
    with pytest.raises(ValueError):
        parser._vtt_timestamp_to_seconds("0:0:0.0")  # Wrong padding on some parts


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
    assert parser._ass_timestamp_to_seconds(timestamp) == expected_seconds


def test_ass_timestamp_to_seconds_invalid() -> None:
    """Test that invalid ASS timestamps raise ValueError."""
    with pytest.raises(ValueError):
        parser._ass_timestamp_to_seconds("0:00:00,00")  # Wrong separator
    with pytest.raises(ValueError):
        parser._ass_timestamp_to_seconds("0:0:0.0")  # Wrong padding


def test_parse_srt_success(sample_srt_content: str) -> None:
    """Test successful parsing of a valid SRT file."""
    segments = parser.parse_srt(sample_srt_content)
    assert len(segments) == 2
    assert segments[0].start == 0.5
    assert segments[0].end == 1.5
    assert str(segments[0]) == "Hello world."
    assert segments[1].start == 2.0
    assert segments[1].end == 3.0
    assert str(segments[1]) == "This is a test."


def test_parse_srt_skips_block_without_arrow() -> None:
    """Test that an SRT block is skipped if the timestamp line lacks '-->'."""
    content = "1\n00:00:00,500 00:00:01,500\nNo arrow\n\n2\n00:00:02,000 --> 00:00:03,000\nGood block"
    segments = parser.parse_srt(content)
    assert len(segments) == 1
    assert str(segments[0]) == "Good block"


def test_parse_srt_handles_malformed_timestamps_and_continues() -> None:
    """Test that the SRT parser skips blocks with bad timestamps and continues."""
    content = (
        "1\n00:00:00,500 --> 00:00:01,500\nFirst good block\n\n"
        "2\n00:00:02.000 --> 00:00:03.000\nBad timestamp format\n\n"
        "3\n00:00:04,000 --> 00:00:05,000\nSecond good block"
    )
    segments = parser.parse_srt(content)
    assert len(segments) == 2
    assert str(segments[0]) == "First good block"
    assert str(segments[1]) == "Second good block"


def test_parse_vtt_success(sample_vtt_content: str) -> None:
    """Test successful parsing of a valid VTT file."""
    segments = parser.parse_vtt(sample_vtt_content)
    assert len(segments) == 2
    assert segments[0].start == 0.5
    assert segments[0].end == 1.5
    assert str(segments[0]) == "Hello world."
    assert segments[1].start == 2.0
    assert segments[1].end == 3.0
    assert str(segments[1]) == "This is a test."


def test_parse_vtt_with_metadata(sample_vtt_content: str) -> None:
    """Test that the VTT parser ignores metadata and still parses correctly."""
    content_with_metadata = "WEBVTT - Test File\n\nNOTE\nThis is a note.\n\n" + sample_vtt_content.replace("WEBVTT", "")
    segments = parser.parse_vtt(content_with_metadata)
    assert len(segments) == 2
    assert str(segments[0]) == "Hello world."


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
    assert str(segments[0]) == "First good block"
    assert str(segments[1]) == "Second good block"


def test_parse_ass_success(sample_ass_content: str) -> None:
    """Test successful parsing of a valid ASS file."""
    segments = parser.parse_ass(sample_ass_content)
    assert len(segments) == 3
    assert segments[0].start == 0.5
    assert segments[0].end == 1.5
    assert str(segments[0]) == "Hello world."
    # Test that style tags are stripped
    assert segments[1].start == 2.0
    assert segments[1].end == 3.0
    assert str(segments[1]) == "This is a test with bold tags."
    # Test that \N is converted to a newline
    assert segments[2].start == 4.1
    assert segments[2].end == 5.9
    assert str(segments[2]) == r"And a\nnew line."


def test_parse_ass_stops_at_new_section() -> None:
    """Test that the ASS parser stops reading events at a new section."""
    content = (
        "[Events]\nFormat: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,First line\n"
        "[Fonts]\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Should be ignored"
    )
    segments = parser.parse_ass(content)
    assert len(segments) == 1
    assert str(segments[0]) == "First line"


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
    segments = parser.parse_ass(content)
    assert len(segments) == 2
    assert str(segments[0]) == "First line"
    assert str(segments[1]) == "Third line"
