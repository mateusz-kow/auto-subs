from typing import Any

import pytest

from auto_subs.api import generate
from auto_subs.models.formats import SubtitleFormat


@pytest.fixture
def invalid_format() -> str:
    return "abc"


@pytest.fixture
def srt_format() -> str:
    return SubtitleFormat.SRT


@pytest.fixture
def ass_format() -> str:
    return SubtitleFormat.ASS


@pytest.fixture
def txt_format() -> str:
    return SubtitleFormat.TXT


def test_invalid_format_is_invalid(invalid_format: str) -> None:
    for format_str in SubtitleFormat:
        assert invalid_format != format_str


def test_invalid_output_format(invalid_format: str, sample_transcription: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="Invalid output format"):
        generate(transcription_dict=sample_transcription, output_format=invalid_format)


def test_srt_output_format(srt_format: str, sample_transcription: dict[str, Any]) -> None:
    srt_subtitles = generate(transcription_dict=sample_transcription, output_format=srt_format)
    assert "This is a test" in srt_subtitles


def test_ass_output_format(ass_format: str, sample_transcription: dict[str, Any]) -> None:
    ass_subtitles = generate(transcription_dict=sample_transcription, output_format=ass_format)
    assert "This is a test" in ass_subtitles


def test_txt_output_format(txt_format: str, sample_transcription: dict[str, Any]) -> None:
    txt_subtitles = generate(transcription_dict=sample_transcription, output_format=txt_format)
    assert "This is a test" in txt_subtitles
