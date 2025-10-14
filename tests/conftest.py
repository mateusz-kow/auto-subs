import json
from pathlib import Path
from typing import Any, cast

import pytest


@pytest.fixture
def sample_transcription() -> dict[str, Any]:
    """Load a sample transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "sample_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def empty_transcription() -> dict[str, Any]:
    """Load an empty transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "empty_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def inverted_timestamps_transcription() -> dict[str, Any]:
    """Load a sample transcription with inverted timestamps."""
    path = Path(__file__).parent / "fixtures" / "inverted_timestamps_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def fake_media_file(tmp_path: Path) -> Path:
    """Create a dummy media file for testing transcription paths."""
    media_file = tmp_path / "test.mp4"
    media_file.touch()
    return media_file


@pytest.fixture
def sample_srt_content() -> str:
    """Load sample SRT content from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "sample.srt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_vtt_content() -> str:
    """Load sample VTT content from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "sample.vtt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_ass_content() -> str:
    """Load sample ASS content from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "sample.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def tmp_srt_file(tmp_path: Path, sample_srt_content: str) -> Path:
    """Create a temporary SRT file for testing."""
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(sample_srt_content, encoding="utf-8")
    return srt_file


@pytest.fixture
def tmp_vtt_file(tmp_path: Path, sample_vtt_content: str) -> Path:
    """Create a temporary VTT file for testing."""
    vtt_file = tmp_path / "test.vtt"
    vtt_file.write_text(sample_vtt_content, encoding="utf-8")
    return vtt_file


@pytest.fixture
def tmp_ass_file(tmp_path: Path, sample_ass_content: str) -> Path:
    """Create a temporary ASS file for testing."""
    ass_file = tmp_path / "test.ass"
    ass_file.write_text(sample_ass_content, encoding="utf-8")
    return ass_file


@pytest.fixture
def fake_video_file(tmp_path: Path) -> Path:
    """Create a dummy video file for testing burn paths."""
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()
    return video_file
