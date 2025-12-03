from pathlib import Path

import pytest

from autosubs.api import load


def test_load_microdvd_with_fps_from_header() -> None:
    """Test loading a MicroDVD file where FPS is read from the header."""
    fixture_path = Path("tests/fixtures/microdvd/sample.sub")
    subtitles = load(fixture_path)
    assert len(subtitles.segments) == 2

    seg1 = subtitles.segments[0]
    assert seg1.start == pytest.approx(24 / 23.976)
    assert seg1.end == pytest.approx(48 / 23.976)
    assert seg1.text == "Hello world."

    seg2 = subtitles.segments[1]
    assert seg2.start == pytest.approx(50 / 23.976)
    assert seg2.end == pytest.approx(72 / 23.976)
    assert seg2.text == "This is a test\nwith a pipe."


def test_load_microdvd_with_explicit_fps(tmp_path: Path) -> None:
    """Test loading a MicroDVD file using an explicit FPS parameter."""
    content = "{24}{48}Hello world."
    file_path = tmp_path / "sample_no_header.sub"
    file_path.write_text(content)

    subtitles = load(file_path, fps=24)
    assert len(subtitles.segments) == 1
    segment = subtitles.segments[0]
    assert segment.start == 1.0
    assert segment.end == 2.0
    assert segment.text == "Hello world."


def test_load_microdvd_raises_error_if_no_fps(tmp_path: Path) -> None:
    """Test that load raises a ValueError if FPS is not available."""
    content = "{24}{48}Hello world."
    file_path = tmp_path / "sample_no_header.sub"
    file_path.write_text(content)
    with pytest.raises(ValueError, match="FPS must be provided to parse MicroDVD files."):
        load(file_path)
