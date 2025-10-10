import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_run_transcription_success(fake_media_file: Path) -> None:
    """Test that run_transcription successfully calls whisper."""
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value.transcribe.return_value = {"text": "hello", "segments": []}

    # Patch sys.modules BEFORE importing the module under test to prevent OSError
    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        from auto_subs.core.transcriber import run_transcription

        result = run_transcription(fake_media_file, "base")

    mock_whisper.load_model.assert_called_once_with("base")
    mock_whisper.load_model.return_value.transcribe.assert_called_once_with(str(fake_media_file), word_timestamps=True)
    assert result == {"text": "hello", "segments": []}


def test_run_transcription_import_error(fake_media_file: Path) -> None:
    """Test that an ImportError is raised if whisper is not installed."""
    # Hide the 'whisper' module to simulate it not being installed
    with patch.dict(sys.modules, {"whisper": None}), pytest.raises(ImportError, match="Whisper is not installed"):
        # We need to reload the module for the failed import to be detected,
        # as it was likely loaded by other tests.
        from importlib import reload

        from auto_subs.core import transcriber

        reload(transcriber)
        transcriber.run_transcription(fake_media_file, "base")
