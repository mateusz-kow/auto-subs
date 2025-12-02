from pathlib import Path

import pytest

from autosubs.api import load
from autosubs.core.generator import to_mpl2, to_srt
from autosubs.core.parser import parse_mpl2
from autosubs.models.subtitles import Subtitles


@pytest.fixture
def sample_mpl2_path() -> Path:
    """Provides the path to the sample MPL2 fixture file."""
    return Path(__file__).parent.parent / "fixtures" / "mpl2" / "sample.mpl2.txt"


@pytest.fixture
def sample_mpl2_content(sample_mpl2_path: Path) -> str:
    """Provides the content of the sample MPL2 fixture file."""
    return sample_mpl2_path.read_text(encoding="utf-8")


# Parser Tests
def test_parse_mpl2_basic(sample_mpl2_content: str) -> None:
    """Tests basic parsing of a valid MPL2 file."""
    segments = parse_mpl2(sample_mpl2_content)
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


def test_parse_mpl2_edge_cases() -> None:
    """Tests the MPL2 parser with edge cases and malformed content."""
    assert not parse_mpl2(""), "Parser should return empty list for empty string"

    malformed_content = (
        "[abc][100]Malformed start\n"
        "[10][xyz]Malformed end\n"
        "Just some random text without timestamps\n"
        "[10][5]Timestamp start > end\n"
        "[100][100]\n"  # This is an invalid line because it has no text content
    )
    segments = parse_mpl2(malformed_content)
    assert not segments, "Parser should skip all malformed lines"


# Round-trip and cross-format tests
def test_mpl2_round_trip(sample_mpl2_path: Path, tmp_path: Path) -> None:
    """Tests if parsing, generating, and re-parsing MPL2 preserves data."""
    original_subs = load(sample_mpl2_path)
    assert len(original_subs.segments) == 3

    generated_content = to_mpl2(original_subs)

    round_trip_file = tmp_path / "roundtrip.mpl2.txt"
    round_trip_file.write_text(generated_content, encoding="utf-8")

    reparsed_subs = load(round_trip_file)

    assert len(reparsed_subs.segments) == len(original_subs.segments)
    for original_seg, reparsed_seg in zip(original_subs.segments, reparsed_subs.segments):
        assert original_seg.start == pytest.approx(reparsed_seg.start, abs=0.1)
        assert original_seg.end == pytest.approx(reparsed_seg.end, abs=0.1)
        assert original_seg.text == reparsed_seg.text


def test_srt_to_mpl2_to_srt_round_trip(tmp_path: Path) -> None:
    """Tests conversion from SRT to MPL2 and back, checking for data integrity."""
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

    # Generate MPL2
    mpl2_content = to_mpl2(original_srt_subs)
    mpl2_file = tmp_path / "test.mpl2.txt"
    mpl2_file.write_text(mpl2_content, encoding="utf-8")

    # Load MPL2
    converted_mpl2_subs = load(mpl2_file)

    # Check timings and text (with tolerance for MPL2's precision)
    assert len(converted_mpl2_subs.segments) == len(original_srt_subs.segments)
    for srt_seg, mpl2_seg in zip(original_srt_subs.segments, converted_mpl2_subs.segments):
        assert srt_seg.start == pytest.approx(mpl2_seg.start, abs=0.1)
        assert srt_seg.end == pytest.approx(mpl2_seg.end, abs=0.1)
        assert srt_seg.text == mpl2_seg.text

    # Generate SRT again from the converted subs
    reconstructed_srt_content = to_srt(converted_mpl2_subs)
    reconstructed_srt_file = tmp_path / "reconstructed.srt"
    reconstructed_srt_file.write_text(reconstructed_srt_content, encoding="utf-8")

    reconstructed_srt_subs = load(reconstructed_srt_file)

    # Compare original SRT with reconstructed SRT
    assert len(reconstructed_srt_subs.segments) == len(original_srt_subs.segments)
    for srt_seg, reconstructed_seg in zip(original_srt_subs.segments, reconstructed_srt_subs.segments):
        assert srt_seg.start == pytest.approx(reconstructed_seg.start, abs=0.1)
        assert srt_seg.end == pytest.approx(reconstructed_seg.end, abs=0.1)
        assert srt_seg.text == reconstructed_seg.text
