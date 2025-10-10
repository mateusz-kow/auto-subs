import json
from pathlib import Path

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
