from typing import Any

import pytest

from auto_subs.api import generate
from auto_subs.models.formats import SubtitleFormat
from auto_subs.models.settings import AssSettings, AssStyleSettings


def test_invalid_output_format(sample_transcription: dict[str, Any]) -> None:
    """Verify that an unsupported format raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid output format specified"):
        generate(transcription_dict=sample_transcription, output_format="invalid-format")


@pytest.mark.parametrize("output_format", SubtitleFormat)
def test_generate_valid_formats(output_format: str, sample_transcription: dict[str, Any]) -> None:
    """Test generation for all supported subtitle formats with default settings."""
    result = generate(transcription_dict=sample_transcription, output_format=output_format, max_chars=200)

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
