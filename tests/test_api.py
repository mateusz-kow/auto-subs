from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import auto_subs
from auto_subs.api import generate, transcribe
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings, AssStyleSettings


def test_invalid_output_format(sample_transcription: dict[str, Any]) -> None:
    """Verify that an unsupported format raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid output format specified"):
        generate(transcription_dict=sample_transcription, output_format="invalid-format")


@pytest.mark.parametrize("output_format", SubtitleFormat)
def test_generate_valid_formats(output_format: str, sample_transcription: dict[str, Any]) -> None:
    """Test generation for all supported subtitle formats with default settings."""
    result = generate(
        transcription_dict=sample_transcription,
        output_format=output_format,
        max_chars=200,
    )

    assert isinstance(result, str)
    assert "This is a test transcription" in result

    if output_format == "srt":
        assert "1\n00:00:00,100 --> 00:00:04,200" in result
        assert "{\\k" not in result
    elif output_format == "ass":
        assert "[Script Info]" in result
        assert "Dialogue: 0," in result
        assert "{\\k" not in result  # Karaoke should be off by default
    elif output_format == "txt":
        assert "-->" not in result
        assert "[Script Info]" not in result
        assert "WEBVTT" not in result
    elif output_format == "vtt":
        assert "WEBVTT" in result
        assert "00:00:00.100 --> 00:00:04.200" in result
        assert "{\\k" not in result


def test_ass_output_with_karaoke(sample_transcription: dict[str, Any]) -> None:
    """Verify that enabling karaoke mode for ASS format adds timing tags."""
    ass_settings = AssSettings(highlight_style=AssStyleSettings())
    result = generate(
        transcription_dict=sample_transcription,
        output_format="ass",
        ass_settings=ass_settings,
    )

    assert "[Script Info]" in result
    assert "Dialogue: 0," in result
    assert "{\\k" in result  # The key assertion for karaoke mode
    assert "{\\k20}This" in result
    assert "{\\k10}is" in result


@patch("auto_subs.api.run_transcription")
def test_transcribe_api_success(
    mock_run_transcription: MagicMock,
    fake_media_file: Path,
    sample_transcription: dict[str, Any],
) -> None:
    """Test the transcribe API function with mocked transcription."""
    mock_run_transcription.return_value = sample_transcription

    result = transcribe(fake_media_file, "srt", model_name="base")

    mock_run_transcription.assert_called_once_with(fake_media_file, "base")
    assert "This is a test transcription" in result
    assert "-->" in result


@patch("auto_subs.api.run_transcription")
def test_transcribe_api_file_not_found(mock_run_transcription: MagicMock) -> None:
    """Test that transcribe API raises FileNotFoundError."""
    non_existent_file = Path("non_existent_file.mp4")
    with pytest.raises(FileNotFoundError):
        transcribe(non_existent_file, "srt")
    mock_run_transcription.assert_not_called()


@patch.dict("sys.modules", {"whisper": None})
def test_transcribe_api_whisper_not_installed(fake_media_file: Path) -> None:
    """Test that transcribe API raises ImportError if whisper is not installed."""
    with pytest.raises(ImportError, match="Whisper is not installed"):
        auto_subs.core.transcriber.run_transcription(fake_media_file, "base")
