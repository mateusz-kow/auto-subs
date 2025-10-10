import json
from pathlib import Path
from typing import Any

import pytest

from auto_subs.typing.transcription import TranscriptionDict


@pytest.fixture
def sample_transcription() -> TranscriptionDict:
    """Load a sample transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "sample_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def empty_transcription() -> TranscriptionDict:
    """Load an empty transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "empty_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def inverted_timestamps_transcription() -> dict[str, Any]:
    """Load a sample transcription with inverted timestamps."""
    path = Path(__file__).parent / "fixtures" / "inverted_timestamps_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def fake_media_file(tmp_path: Path) -> Path:
    """Create a dummy media file for testing transcription paths."""
    media_file = tmp_path / "test.mp4"
    media_file.touch()
    return media_file
