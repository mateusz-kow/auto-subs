from pathlib import Path

import pytest

from autosubs.api import load
from autosubs.core.generator import to_sami, to_srt
from autosubs.core.parser import parse_sami
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


@pytest.fixture
def sample_sami_path() -> Path:
    """Provides the path to the sample SAMI fixture file."""
    return Path(__file__).parent.parent / "fixtures" / "sami" / "sample.smi"


@pytest.fixture
def sample_sami_content(sample_sami_path: Path) -> str:
    """Provides the content of the sample SAMI fixture file."""
    return sample_sami_path.read_text(encoding="utf-8")


# Parser Tests
def test_parse_sami_basic(sample_sami_content: str) -> None:
    """Tests basic parsing of a valid SAMI file."""
    segments = parse_sami(sample_sami_content)
    assert len(segments) == 3

    assert segments[0].start == pytest.approx(1.0)
    assert segments[0].end == pytest.approx(6.0)
    assert segments[0].text == "Hello, world."

    assert segments[1].start == pytest.approx(6.0)
    assert segments[1].end == pytest.approx(15.5)
    assert segments[1].text == "This is a test\nwith multiple lines."

    assert segments[2].start == pytest.approx(15.5)
    assert segments[2].end == pytest.approx(20.0)
    assert segments[2].text == "Another line here."


def test_parse_sami_with_html_entities() -> None:
    """Tests that HTML entities are properly decoded."""
    content = """<SAMI>
<BODY>
<SYNC Start=1000>
  <P Class=ENCC>Test &amp; example &lt;tag&gt; &quot;quotes&quot;
<SYNC Start=3000>
  <P Class=ENCC>&nbsp;
</BODY>
</SAMI>"""
    segments = parse_sami(content)
    assert len(segments) == 1
    assert segments[0].text == 'Test & example <tag> "quotes"'


def test_parse_sami_minimal() -> None:
    """Tests parsing of minimal SAMI content."""
    content = """<SAMI>
<BODY>
<SYNC Start=0>
  <P>First subtitle
<SYNC Start=2000>
  <P>Second subtitle
<SYNC Start=4000>
  <P>&nbsp;
</BODY>
</SAMI>"""
    segments = parse_sami(content)
    assert len(segments) == 2
    assert segments[0].start == 0.0
    assert segments[0].end == 2.0
    assert segments[0].text == "First subtitle"
    assert segments[1].start == 2.0
    assert segments[1].end == 4.0
    assert segments[1].text == "Second subtitle"


def test_parse_sami_empty_syncs() -> None:
    """Tests that empty SYNC tags with only &nbsp; are skipped."""
    content = """<SAMI>
<BODY>
<SYNC Start=1000>
  <P>Valid subtitle
<SYNC Start=2000>
  <P>&nbsp;
<SYNC Start=3000>
  <P>Another valid subtitle
<SYNC Start=4000>
  <P>&nbsp;
</BODY>
</SAMI>"""
    segments = parse_sami(content)
    assert len(segments) == 2
    assert segments[0].text == "Valid subtitle"
    assert segments[1].text == "Another valid subtitle"


def test_parse_sami_malformed() -> None:
    """Tests parsing of malformed SAMI with regex fallback."""
    # This is not well-formed XML but should still parse
    content = """<SAMI>
<BODY>
<SYNC Start=1000>
  <P Class=ENCC>Line without closing P tag
<SYNC Start=3000>
  <P>Another line
</BODY>
</SAMI>"""
    segments = parse_sami(content)
    # Should parse using regex fallback
    assert len(segments) >= 1


def test_parse_sami_edge_cases() -> None:
    """Tests the SAMI parser with edge cases."""
    assert not parse_sami(""), "Parser should return empty list for empty string"
    assert not parse_sami("<SAMI></SAMI>"), "Parser should return empty list for empty SAMI"


# Generator Tests


@pytest.fixture
def sample_subtitles() -> Subtitles:
    """Provides a sample Subtitles object for testing."""
    return Subtitles(
        segments=[
            SubtitleSegment(words=[SubtitleWord(text="Hello, world.", start=1.0, end=6.0)]),
            SubtitleSegment(words=[SubtitleWord(text="This is a test\nwith multiple lines.", start=6.0, end=15.5)]),
            SubtitleSegment(words=[SubtitleWord(text="Another line here.", start=15.5, end=20.0)]),
        ]
    )


def test_generate_sami_basic(sample_subtitles: Subtitles) -> None:
    """Test basic generation of a SAMI file."""
    result = to_sami(sample_subtitles)
    
    # Check structure
    assert result.startswith("<SAMI>")
    assert "</SAMI>" in result
    assert "<HEAD>" in result
    assert "<BODY>" in result
    
    # Check timing
    assert "<SYNC Start=1000>" in result
    assert "<SYNC Start=6000>" in result
    assert "<SYNC Start=15500>" in result
    assert "<SYNC Start=20000>" in result  # Final clear
    
    # Check content
    assert "Hello, world." in result
    assert "This is a test<br>with multiple lines." in result
    assert "Another line here." in result


def test_generate_sami_html_escaping() -> None:
    """Test that special characters are properly escaped."""
    subs = Subtitles(
        segments=[
            SubtitleSegment(words=[SubtitleWord(text='Test & example <tag> "quotes"', start=1.0, end=3.0)])
        ]
    )
    result = to_sami(subs)
    assert "Test &amp; example &lt;tag&gt; &quot;quotes&quot;" in result


def test_generate_sami_empty_subtitles() -> None:
    """Test generating from an empty Subtitles object."""
    result = to_sami(Subtitles(segments=[]))
    assert "<SAMI>" in result
    assert "</SAMI>" in result
    # Should not have any subtitle SYNC tags, only structure


# Round-trip Tests


def test_sami_round_trip(sample_sami_path: Path, tmp_path: Path) -> None:
    """Tests if parsing, generating, and re-parsing SAMI preserves data."""
    original_subs = load(sample_sami_path)
    assert len(original_subs.segments) == 3

    generated_content = to_sami(original_subs)

    round_trip_file = tmp_path / "roundtrip.smi"
    round_trip_file.write_text(generated_content, encoding="utf-8")

    reparsed_subs = load(round_trip_file)

    assert len(reparsed_subs.segments) == len(original_subs.segments)
    for original_seg, reparsed_seg in zip(original_subs.segments, reparsed_subs.segments, strict=False):
        assert original_seg.start == pytest.approx(reparsed_seg.start, abs=0.01)
        assert original_seg.end == pytest.approx(reparsed_seg.end, abs=0.01)
        assert original_seg.text == reparsed_seg.text


def test_srt_to_sami_to_srt_round_trip(tmp_path: Path) -> None:
    """Tests conversion from SRT to SAMI and back, checking for data integrity.
    
    Note: SAMI format doesn't encode end times explicitly. Each subtitle lasts until
    the next SYNC tag, so gaps between subtitles will be filled. This test verifies
    that text content and start times are preserved, while acknowledging that end
    times may differ due to format limitations.
    """
    srt_content = (
        "1\n"
        "00:00:01,500 --> 00:00:05,000\n"
        "Hello, world.\n"
        "\n"
        "2\n"
        "00:00:06,250 --> 00:00:12,100\n"
        "This is a test\n"
        "with multiple lines.\n"
    )
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(srt_content, encoding="utf-8")

    # Load SRT
    original_srt_subs = load(srt_file)

    # Generate SAMI
    sami_content = to_sami(original_srt_subs)
    sami_file = tmp_path / "test.smi"
    sami_file.write_text(sami_content, encoding="utf-8")

    # Load SAMI
    converted_sami_subs = load(sami_file)

    # Check that we have the same number of segments
    assert len(converted_sami_subs.segments) == len(original_srt_subs.segments)
    
    # Check start times and text content
    for srt_seg, sami_seg in zip(original_srt_subs.segments, converted_sami_subs.segments, strict=False):
        assert srt_seg.start == pytest.approx(sami_seg.start, abs=0.01)
        assert srt_seg.text == sami_seg.text
    
    # Note: End times will differ because SAMI format extends subtitles until the next SYNC
    # The first subtitle will end at the start of the second (6.25s) instead of its original end (5.0s)
    assert converted_sami_subs.segments[0].end == pytest.approx(6.25, abs=0.01)
    assert converted_sami_subs.segments[1].end == pytest.approx(12.1, abs=0.01)

    # Generate SRT again from the converted subs
    reconstructed_srt_content = to_srt(converted_sami_subs)
    reconstructed_srt_file = tmp_path / "reconstructed.srt"
    reconstructed_srt_file.write_text(reconstructed_srt_content, encoding="utf-8")

    reconstructed_srt_subs = load(reconstructed_srt_file)

    # Compare SAMI-converted SRT with reconstructed SRT (should match exactly)
    assert len(reconstructed_srt_subs.segments) == len(converted_sami_subs.segments)
    for sami_seg, reconstructed_seg in zip(converted_sami_subs.segments, reconstructed_srt_subs.segments, strict=False):
        assert sami_seg.start == pytest.approx(reconstructed_seg.start, abs=0.01)
        assert sami_seg.end == pytest.approx(reconstructed_seg.end, abs=0.01)
        assert sami_seg.text == reconstructed_seg.text
