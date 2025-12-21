"""Tests for TTML (Timed Text Markup Language) / IMSC1 parsing and generation."""

from pathlib import Path

import pytest

from autosubs.api import load
from autosubs.core.generator import to_ttml
from autosubs.core.parser import parse_ttml, ttml_timestamp_to_seconds
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_ttml_path() -> Path:
    """Provides the path to the sample TTML fixture file."""
    return Path(__file__).parent.parent / "fixtures" / "ttml" / "sample.ttml"


@pytest.fixture
def sample_ttml_content(sample_ttml_path: Path) -> str:
    """Provides the content of the sample TTML fixture file."""
    return sample_ttml_path.read_text(encoding="utf-8")


# Timestamp Tests
def test_ttml_timestamp_to_seconds() -> None:
    """Tests conversion of TTML timestamps to seconds."""
    assert ttml_timestamp_to_seconds("00:00:01.000") == pytest.approx(1.0)
    assert ttml_timestamp_to_seconds("00:00:05.500") == pytest.approx(5.5)
    assert ttml_timestamp_to_seconds("00:01:30.250") == pytest.approx(90.25)
    assert ttml_timestamp_to_seconds("01:05:45.123") == pytest.approx(3945.123)
    # Test without milliseconds
    assert ttml_timestamp_to_seconds("00:00:10") == pytest.approx(10.0)
    # Test with 1 or 2 digit milliseconds
    assert ttml_timestamp_to_seconds("00:00:01.5") == pytest.approx(1.5)
    assert ttml_timestamp_to_seconds("00:00:01.50") == pytest.approx(1.5)


def test_ttml_timestamp_invalid_format() -> None:
    """Tests that invalid TTML timestamps raise ValueError."""
    with pytest.raises(ValueError, match="Invalid TTML timestamp format"):
        ttml_timestamp_to_seconds("invalid")
    with pytest.raises(ValueError, match="Invalid TTML timestamp format"):
        ttml_timestamp_to_seconds("1:2:3")  # Not enough digits


# Parser Tests
def test_parse_ttml_basic(sample_ttml_content: str) -> None:
    """Tests basic parsing of a valid TTML file."""
    segments = parse_ttml(sample_ttml_content)
    assert len(segments) == 3

    assert segments[0].start == pytest.approx(1.0)
    assert segments[0].end == pytest.approx(5.0)
    assert segments[0].text == "Hello, world."

    assert segments[1].start == pytest.approx(6.0)
    assert segments[1].end == pytest.approx(12.0)
    assert segments[1].text == "This is a test\nwith multiple lines."

    assert segments[2].start == pytest.approx(15.5)
    assert segments[2].end == pytest.approx(20.0)
    assert segments[2].text == "Another line here."


def test_parse_ttml_empty() -> None:
    """Tests parsing an empty TTML file."""
    minimal_ttml = """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div></div>
  </body>
</tt>"""
    segments = parse_ttml(minimal_ttml)
    assert len(segments) == 0


def test_parse_ttml_malformed_xml() -> None:
    """Tests that malformed XML returns empty segments list."""
    malformed = "<tt><body><div><p>Unclosed tag"
    segments = parse_ttml(malformed)
    assert len(segments) == 0


def test_parse_ttml_missing_timestamps() -> None:
    """Tests that elements without timestamps are skipped."""
    ttml_missing = """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:00:01.000" end="00:00:02.000">Valid subtitle</p>
      <p begin="00:00:03.000">Missing end</p>
      <p end="00:00:04.000">Missing begin</p>
      <p>No timestamps</p>
    </div>
  </body>
</tt>"""
    segments = parse_ttml(ttml_missing)
    assert len(segments) == 1
    assert segments[0].text == "Valid subtitle"


def test_parse_ttml_invalid_timestamp_order() -> None:
    """Tests that segments with start > end are skipped."""
    ttml_invalid = """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:00:05.000" end="00:00:01.000">Invalid order</p>
      <p begin="00:00:01.000" end="00:00:02.000">Valid</p>
    </div>
  </body>
</tt>"""
    segments = parse_ttml(ttml_invalid)
    assert len(segments) == 1
    assert segments[0].text == "Valid"


# Generator Tests
def test_to_ttml_basic() -> None:
    """Tests basic TTML generation."""
    subtitles = Subtitles(
        segments=[
            SubtitleSegment(words=[SubtitleWord(text="Hello, world.", start=1.0, end=5.0)]),
            SubtitleSegment(words=[SubtitleWord(text="Test subtitle", start=6.0, end=10.0)]),
        ]
    )

    ttml_output = to_ttml(subtitles)

    # Verify XML declaration
    assert ttml_output.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    # Verify timestamps are present
    assert "00:00:01.000" in ttml_output
    assert "00:00:05.000" in ttml_output
    assert "00:00:06.000" in ttml_output
    assert "00:00:10.000" in ttml_output

    # Verify text content
    assert "Hello, world." in ttml_output
    assert "Test subtitle" in ttml_output

    # Verify namespace declarations
    assert 'xmlns="http://www.w3.org/ns/ttml"' in ttml_output
    assert 'xmlns:tts="http://www.w3.org/ns/ttml#styling"' in ttml_output


def test_to_ttml_multiline() -> None:
    """Tests TTML generation with multi-line text."""
    subtitles = Subtitles(
        segments=[
            SubtitleSegment(words=[SubtitleWord(text="Line one\nLine two", start=1.0, end=3.0)]),
        ]
    )

    ttml_output = to_ttml(subtitles)

    # Verify <br/> element is used for line breaks
    assert "<br />" in ttml_output or "<br/>" in ttml_output
    assert "Line one" in ttml_output
    assert "Line two" in ttml_output


def test_to_ttml_empty() -> None:
    """Tests TTML generation with no segments."""
    subtitles = Subtitles(segments=[])
    ttml_output = to_ttml(subtitles)

    # Should still have valid XML structure
    assert ttml_output.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<body>" in ttml_output
    assert "</body>" in ttml_output


# Round-trip Tests
def test_ttml_round_trip(sample_ttml_content: str) -> None:
    """Tests that parsing and generating TTML preserves content."""
    # Parse the original
    original_segments = parse_ttml(sample_ttml_content)

    # Generate TTML from parsed segments
    subtitles = Subtitles(segments=original_segments)
    generated_ttml = to_ttml(subtitles)

    # Parse the generated TTML
    reparsed_segments = parse_ttml(generated_ttml)

    # Verify same number of segments
    assert len(reparsed_segments) == len(original_segments)

    # Verify content matches
    for orig, reparsed in zip(original_segments, reparsed_segments, strict=False):
        assert reparsed.start == pytest.approx(orig.start)
        assert reparsed.end == pytest.approx(orig.end)
        assert reparsed.text == orig.text


# API Integration Tests
def test_load_ttml_file(sample_ttml_path: Path) -> None:
    """Tests loading a TTML file using the load API."""
    subtitles = load(sample_ttml_path)

    assert len(subtitles.segments) == 3
    assert subtitles.segments[0].text == "Hello, world."
    assert subtitles.segments[1].text == "This is a test\nwith multiple lines."
    assert subtitles.segments[2].text == "Another line here."


def test_load_netflix_style_ttml() -> None:
    """Tests loading a more complex Netflix-style TTML file."""
    netflix_path = Path(__file__).parent.parent / "fixtures" / "ttml" / "netflix_style.ttml"
    subtitles = load(netflix_path)

    assert len(subtitles.segments) == 4
    assert subtitles.segments[0].start == pytest.approx(1.0)
    assert subtitles.segments[0].end == pytest.approx(3.5)
    assert "Welcome to the video" in subtitles.segments[0].text

    # Verify multi-line subtitle
    assert "Important message at the top" in subtitles.segments[2].text
    assert "with multiple lines" in subtitles.segments[2].text
    assert "\n" in subtitles.segments[2].text


def test_ttml_with_different_extensions() -> None:
    """Tests that both .xml and .ttml extensions work."""
    import tempfile

    ttml_content = """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div>
      <p begin="00:00:01.000" end="00:00:02.000">Test subtitle</p>
    </div>
  </body>
</tt>"""

    # Test with .xml extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        f.write(ttml_content)
        xml_path = Path(f.name)

    try:
        subtitles_xml = load(xml_path)
        assert len(subtitles_xml.segments) == 1
        assert subtitles_xml.segments[0].text == "Test subtitle"
    finally:
        xml_path.unlink()

    # Test with .ttml extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttml', delete=False, encoding='utf-8') as f:
        f.write(ttml_content)
        ttml_path = Path(f.name)

    try:
        subtitles_ttml = load(ttml_path)
        assert len(subtitles_ttml.segments) == 1
        assert subtitles_ttml.segments[0].text == "Test subtitle"
    finally:
        ttml_path.unlink()
