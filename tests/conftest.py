import json
from pathlib import Path
from typing import Any, cast

import pytest


@pytest.fixture
def sample_style_config() -> dict[str, Any]:
    """
    Provides a sample style engine configuration compatible with
    the new Style Engine Schema v2.
    """
    return {
        "script_info": {
            "Title": "Styled by Auto Subs",
            "ScriptType": "v4.00+",
            "PlayResX": 1920,
            "PlayResY": 1080,
        },
        "styles": [
            {
                "Name": "Default",
                "Fontname": "Arial",
                "Fontsize": 48,
                "PrimaryColour": "&H00FFFFFF",
                "SecondaryColour": "&H00000000",
                "OutlineColour": "&H00000000",
                "BackColour": "&H00000000",
                "Bold": -1,
                "BorderStyle": 1,
                "Outline": 3,
                "Shadow": 0,
                "Alignment": 2,
            },
            {
                "Name": "Highlight",
                "Fontname": "Impact",
                "Fontsize": 52,
                "PrimaryColour": "&H0000FFFF",
                "SecondaryColour": "&H00000000",
                "OutlineColour": "&H00000000",
                "BackColour": "&H00000000",
                "Bold": -1,
                "BorderStyle": 1,
                "Outline": 3,
                "Shadow": 0,
                "Alignment": 2,
            },
        ],
        "rules": [
            {
                "name": "Highlight specific word",
                "priority": 10,
                "apply_to": "word",
                "regex": r"(library|test)",
                "operators": [{"target": "word", "regex": r"(library|test)"}],
                "style_override": {"primary_color": "&H0000FFFF", "bold": True},
                "transforms": [
                    {"start": 0, "end": 150, "scale_x": 110, "scale_y": 110},
                    {"start": 150, "end": 300, "scale_x": 100, "scale_y": 100},
                ],
            }
        ],
        "effects": [],
        "karaoke": {"type": "word-by-word", "style_name": "Default"},
    }


@pytest.fixture
def tmp_style_config_file(tmp_path: Path, sample_style_config: dict[str, Any]) -> Path:
    """Creates a temporary JSON file for a style engine configuration."""
    config_file = tmp_path / "style_config.json"
    config_file.write_text(json.dumps(sample_style_config), encoding="utf-8")
    return config_file


@pytest.fixture
def sample_transcription() -> dict[str, Any]:
    """Load a sample transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "transcription" / "sample_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def empty_transcription() -> dict[str, Any]:
    """Load an empty transcription from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "transcription" / "empty_transcription.json"
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def inverted_timestamps_transcription() -> dict[str, Any]:
    """Load a sample transcription with inverted timestamps."""
    path = Path(__file__).parent / "fixtures" / "transcription" / "inverted_timestamps_transcription.json"
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
    path = Path(__file__).parent / "fixtures" / "srt" / "sample.srt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_vtt_content() -> str:
    """Load sample VTT content from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "vtt" / "sample.vtt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_ass_content() -> str:
    """Load sample ASS content from a fixture file."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample2_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample2.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample2.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample3_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample3.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample3.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample4_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample4.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample4.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample5_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample5.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample5.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample6_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample6.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample6.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample7_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample7.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample7.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample8_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample8.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample8.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample9_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample9.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample9.ass"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample10_ass_content() -> str:
    """Load sample ASS content from a fixture file (sample10.ass)."""
    path = Path(__file__).parent / "fixtures" / "ass" / "sample10.ass"
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
