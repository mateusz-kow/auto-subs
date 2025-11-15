import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from autosubs.api import generate, load, transcribe
from autosubs.models.subtitles import Subtitles


def test_invalid_output_format(sample_transcription: dict[str, Any]) -> None:
    """Verify that an unsupported format raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid output format"):
        generate(transcription_source=sample_transcription, output_format="invalid-format")


@pytest.mark.parametrize("output_format", ["srt", "vtt", "ass", "json"])
def test_generate_valid_formats(output_format: str, sample_transcription: dict[str, Any]) -> None:
    """Test generation for all supported subtitle formats with default settings."""
    result = generate(
        transcription_source=sample_transcription,
        output_format=output_format,
        max_chars=200,
    )

    assert isinstance(result, str)
    assert "This is a test transcription" in result
    assert "{\\k" not in result

    if output_format == "srt":
        assert "1\n00:00:00,100 --> 00:00:04,200" in result
    elif output_format == "ass":
        assert "[Script Info]" in result
        assert "Dialogue: 0," in result
    elif output_format == "vtt":
        assert "WEBVTT" in result
        assert "00:00:00.100 --> 00:00:04.200" in result


def test_ass_output_with_style_config(sample_transcription: dict[str, Any], tmp_style_config_file: Path) -> None:
    """Verify that a style config correctly modifies the ASS output."""
    result = generate(
        transcription_source=sample_transcription,
        output_format="ass",
        style_config_path=tmp_style_config_file,
    )

    assert "[Script Info]" in result
    assert "Title: Styled by Auto Subs" in result
    assert "Style: Highlight,Impact,52" in result
    assert r"{\c&H0000FFFF&}{\b1}test{\b0}{\c}" in result
    assert r"{\c&H0000FFFF&}{\b1}library.{\b0}{\c}" in result


@patch("autosubs.api.run_transcription")
def test_transcribe_api_success(
    mock_run_transcription: MagicMock,
    fake_media_file: Path,
    sample_transcription: dict[str, Any],
) -> None:
    """Test the transcribe API function with mocked transcription."""
    mock_run_transcription.return_value = sample_transcription

    result = transcribe(fake_media_file, "srt", model_name="base")

    mock_run_transcription.assert_called_once_with(fake_media_file, "base", verbose=None)
    assert "This is a test transcription" in result
    assert "-->" in result


def test_transcribe_api_file_not_found() -> None:
    """Test that transcribe API raises FileNotFoundError."""
    non_existent_file = Path("non_existent_file.mp4")
    with pytest.raises(FileNotFoundError):
        transcribe(non_existent_file, "srt")


@patch.dict("sys.modules", {"whisper": None})
def test_transcribe_api_whisper_not_installed(fake_media_file: Path) -> None:
    """Test that transcribe API raises ImportError if whisper is not installed."""
    with pytest.raises(ImportError, match="Whisper is not installed"):
        transcribe(fake_media_file, "base")


def test_load_api_success(tmp_srt_file: Path, tmp_vtt_file: Path, tmp_ass_file: Path) -> None:
    """Test that `load` successfully parses supported subtitle formats."""
    for file_path in [tmp_srt_file, tmp_vtt_file, tmp_ass_file]:
        subtitles = load(file_path)
        assert isinstance(subtitles, Subtitles)
        assert len(subtitles.segments) > 0
        assert "Hello world" in subtitles.text


def test_load_api_file_not_found() -> None:
    """Test that `load` raises FileNotFoundError for non-existent files."""
    non_existent_file = Path("non_existent_file.srt")
    with pytest.raises(FileNotFoundError):
        load(non_existent_file)


def test_load_api_unsupported_format(tmp_path: Path) -> None:
    """Test that `load` raises ValueError for unsupported file formats."""
    unsupported_file = tmp_path / "test.txt"
    unsupported_file.touch()
    with pytest.raises(ValueError, match="Unsupported format"):
        load(unsupported_file)


def test_generate_from_file_path(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
    """Test that `generate` can load a transcription from a valid file path."""
    json_path = tmp_path / "transcription.json"
    json_path.write_text(json.dumps(sample_transcription), encoding="utf-8")

    result = generate(json_path, "srt")
    assert isinstance(result, str)
    assert "This is a test transcription" in result
    assert "-->" in result


def test_generate_api_file_not_found() -> None:
    """Test that `generate` raises FileNotFoundError for a non-existent path."""
    non_existent_path = Path("non_existent_transcription.json")
    with pytest.raises(FileNotFoundError, match="Transcription file not found"):
        generate(non_existent_path, "srt")


def test_load_api_with_word_timing_generation(tmp_srt_file: Path) -> None:
    """Test that `load` with generate_word_timings=True splits segments into words."""
    subs_no_timings = load(tmp_srt_file)
    assert len(subs_no_timings.segments[0].words) == 1
    assert subs_no_timings.segments[0].words[0].text == "Hello world."
    assert len(subs_no_timings.segments[1].words) == 1
    assert subs_no_timings.segments[1].words[0].text == "This is a test."

    subs_with_timings = load(tmp_srt_file, generate_word_timings=True)
    assert len(subs_with_timings.segments[0].words) == 2
    assert subs_with_timings.segments[0].words[0].text == "Hello"
    assert len(subs_with_timings.segments[1].words) == 4
    assert subs_with_timings.segments[1].words[0].text == "This"

    first_word = subs_with_timings.segments[0].words[0]
    segment = subs_with_timings.segments[0]
    assert segment.start <= first_word.start < first_word.end <= segment.end
