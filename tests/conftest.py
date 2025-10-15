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


@pytest.fixture
def simple_ass_content() -> str:
    """Provide minimal, valid ASS content for basic parsing tests."""
    return (
        "[Script Info]\n"
        "Title: Test Script\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize\n"
        "Style: Default,Arial,48\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,Hello world\n"
    )


@pytest.fixture
def complex_ass_content() -> str:
    """Provide complex ASS content with various tags for advanced parsing tests."""
    return (
        "[Script Info]\n"
        "; This is a comment\n"
        "Title: Complex Test\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour\n"
        "Style: Default,Arial,48,&H00FFFFFF\n"
        "Style: Highlight,Impact,52,&H0000FFFF\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:05.10,0:00:08.50,Default,,0,0,0,,This line has {\\b1}bold{\\b0} text.\n"
        "Dialogue: 1,0:00:10.00,0:00:12.00,Highlight,ActorName,10,10,10,Banner;"
        "Text banner,Mid-word st{\\i1}y{\\i0}le.\n"
        "Dialogue: 0,0:00:15.00,0:00:18.00,Default,,0,0,0,,{\\k20}Kara{\\k40}oke{\\k50} test.\n"
    )


@pytest.fixture
def malformed_ass_content() -> str:
    """Provide malformed ASS content to test parser robustness."""
    return (
        "[Script Info]\n"
        "Title: Malformed\n"
        "\n"
        "[Events]\n"
        "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,This line is before the Format line.\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Default,This line is good.\n"
        "Dialogue: 0:00:05.00,bad-time,Default,This line has a bad timestamp.\n"
    )


@pytest.fixture
def weird_ass_content() -> str:
    return r"""[Script Info]
PlayResY: 600
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Code, monospace,20,&H00B0B0B0,&H00B0B0B0,&H00303030,&H80000008,-1,0,0,0,100,100,0.00,0.00,1,1.00,2.00, 7 ,30,10,30,0
Style: Expl, Arial,28,&H00FFB0B0,&H00B0B0B0,&H00303030,&H80000008,-1,0,0,0,100,100,0.00,0.00,1,1.00,2.00, 7 ,30,10,30,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,00:00:00.00,00:03:00.00,Expl, NTP,0,0,0,,{\pos(20,20)}To split audio stream into several bands, you can use `lowpass', `bandpass', `highpass', etc., but in recent ffmpeg you can also use `acrossover'.\N\NThough it is unclear how to use it due to the lack of explanation of the official document, it seems to be used like this.
Dialogue: 0,00:00:00.00,00:03:00.00,Code, NTP,0,0,0,,{\pos(40,160)}#! /bin/sh\Nifn="Air on the G String (from Orchestral Suite no. 3, BWV 1068).mp3"\Nifnb="`basename \"$\{ifn\}\" .mp3`"\Npref="`basename $0 .sh`"\N#\N"/c/Program Files/ffmpeg-4.1-win64-shared/bin/ffmpeg" -y \\N    -i "$\{ifn\}" -filter_complex "\N\N[0:a]acrossover=split='500 2000'[div1][div2][div3];\N\N[div1]asplit[div1_1][div1_2];\N[div2]asplit[div2_1][div2_2];\N[div3]asplit[div3_1][div3_2];\N\N[div1_2]showcqt=s=1920x1080[v1];\N[div2_2]showcqt=s=1920x1080[v2];\N[div3_2]showcqt=s=1920x1080[v3]" \\N    -map '[v1]' -map '[div1_1]' "$\{pref\}_$\{ifnb\}_1.mp4" \\N    -map '[v2]' -map '[div2_1]' "$\{pref\}_$\{ifnb\}_2.mp4" \\N    -map '[v3]' -map '[div3_1]' "$\{pref\}_$\{ifnb\}_3.mp4"
Dialogue: 0,00:00:00.00,00:03:00.00,Expl, NTP,0,0,0,,{\pos(20,550)}(Note: Uploaded video is of `div2'.)"""
