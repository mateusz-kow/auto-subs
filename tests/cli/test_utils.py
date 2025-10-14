import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from _pytest.capture import CaptureFixture
from typer import Exit

from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    determine_output_format,
    parse_ass_settings_from_cli,
)
from autosubs.models.formats import SubtitleFormat
from autosubs.models.settings import AssSettings


# --- Tests for PathProcessor (Existing) ---
def test_path_processor_single_file(tmp_path: Path) -> None:
    """Test processing a single valid file."""
    in_file = tmp_path / "test.mp4"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, in_file)


def test_path_processor_single_file_with_output(tmp_path: Path) -> None:
    """Test processing a single file with a specified output path."""
    in_file = tmp_path / "test.mp4"
    out_file = tmp_path / "output.srt"
    in_file.touch()
    processor = PathProcessor(in_file, out_file, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, out_file)


def test_path_processor_unsupported_file_type(tmp_path: Path) -> None:
    """Test that an unsupported file type raises an Exit exception."""
    in_file = tmp_path / "test.txt"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_directory(tmp_path: Path) -> None:
    """Test processing a directory of files."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    (in_dir / "test1.json").touch()
    (in_dir / "test2.json").touch()
    (in_dir / "ignored.txt").touch()

    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 2
    assert results[0] == (in_dir / "test1.json", in_dir / "test1.json")
    assert results[1] == (in_dir / "test2.json", in_dir / "test2.json")


def test_path_processor_directory_with_output_dir(tmp_path: Path) -> None:
    """Test processing a directory with a specified output directory."""
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "test1.json").touch()

    processor = PathProcessor(in_dir, out_dir, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_dir / "test1.json", out_dir / "test1.json")


def test_path_processor_empty_directory(tmp_path: Path) -> None:
    """Test that an empty directory raises an Exit exception."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_input_dir_output_file_error(tmp_path: Path) -> None:
    """Test that input dir with output file raises an Exit exception."""
    in_dir = tmp_path / "input"
    out_file = tmp_path / "output.txt"
    in_dir.mkdir()
    out_file.touch()

    with pytest.raises(Exit):
        PathProcessor(in_dir, out_file, SupportedExtension.JSON)


# --- Tests for determine_output_format (New) ---
def test_determine_output_format_explicit_option_wins() -> None:
    """Test that the explicit --format option has the highest priority."""
    # The output path suggests VTT, but the explicit format is SRT.
    result = determine_output_format(SubtitleFormat.SRT, Path("output.vtt"))
    assert result == SubtitleFormat.SRT


def test_determine_output_format_inferred_from_path() -> None:
    """Test that the format is correctly inferred from the output path extension."""
    result = determine_output_format(None, Path("video.ass"))
    assert result == SubtitleFormat.ASS


def test_determine_output_format_fallback_to_default(
    capsys: CaptureFixture[str],
) -> None:
    """Test that the function falls back to the default when no format can be determined."""
    # Case 1: No output path provided
    result1 = determine_output_format(None, None)
    assert result1 == SubtitleFormat.SRT
    assert "Defaulting to SRT" in capsys.readouterr().out

    # Case 2: Output path has an unrecognized extension
    result2 = determine_output_format(None, Path("output.txt"))
    assert result2 == SubtitleFormat.SRT
    assert "Defaulting to SRT" in capsys.readouterr().out


# --- Tests for parse_ass_settings_from_cli (New) ---
def test_parse_ass_settings_defaults() -> None:
    """Test that default AssSettings are returned when no options are provided."""
    settings = parse_ass_settings_from_cli(
        style_file=None,
        karaoke=False,
        font_name=None,
        font_size=None,
        primary_color=None,
        secondary_color=None,
        outline_color=None,
        back_color=None,
        bold=None,
        italic=None,
        underline=None,
        alignment=None,
        margin_v=None,
    )
    assert isinstance(settings, AssSettings)
    assert settings.font == "Arial"
    assert settings.font_size == 48
    assert settings.highlight_style is None


def test_parse_ass_settings_from_style_file(tmp_path: Path) -> None:
    """Test that settings are correctly loaded from a style file."""
    style_file = tmp_path / "styles.json"
    style_file.write_text(json.dumps({"font_name": "Impact", "font_size": 100}))

    settings = parse_ass_settings_from_cli(
        style_file=style_file,
        karaoke=False,
        font_name=None,
        font_size=None,
        primary_color=None,
        secondary_color=None,
        outline_color=None,
        back_color=None,
        bold=None,
        italic=None,
        underline=None,
        alignment=None,
        margin_v=None,
    )
    assert settings.font == "Impact"
    assert settings.font_size == 100


def test_parse_ass_settings_cli_overrides_style_file(tmp_path: Path) -> None:
    """Test that CLI arguments take precedence over style file settings."""
    style_file = tmp_path / "styles.json"
    style_file.write_text(json.dumps({"font_name": "Impact", "font_size": 100, "bold": -1}))

    settings = parse_ass_settings_from_cli(
        style_file=style_file,
        karaoke=False,
        font_name="Verdana",  # Override font name
        font_size=None,  # Do not override font size
        primary_color=None,
        secondary_color=None,
        outline_color=None,
        back_color=None,
        bold=False,  # Override bold to be false
        italic=None,
        underline=None,
        alignment=None,
        margin_v=None,
    )
    assert settings.font == "Verdana"  # Overridden
    assert settings.font_size == 100  # From file
    assert settings.bold == 0  # Overridden to be disabled


def test_parse_ass_settings_karaoke_flag() -> None:
    """Test that the karaoke flag enables the highlight style."""
    settings = parse_ass_settings_from_cli(
        style_file=None,
        karaoke=True,
        font_name=None,
        font_size=None,
        primary_color=None,
        secondary_color=None,
        outline_color=None,
        back_color=None,
        bold=None,
        italic=None,
        underline=None,
        alignment=None,
        margin_v=None,
    )
    assert settings.highlight_style is not None


@patch("shutil.which", return_value="/path/to/ffmpeg")
def test_check_ffmpeg_installed_success(mock_which: MagicMock) -> None:
    """Test that no error is raised when ffmpeg is found."""
    from autosubs.cli.utils import check_ffmpeg_installed

    try:
        check_ffmpeg_installed()
    except Exit:
        pytest.fail("check_ffmpeg_installed raised Exit unexpectedly.")


@patch("shutil.which", return_value=None)
def test_check_ffmpeg_installed_failure(mock_which: MagicMock) -> None:
    """Test that Exit is raised when ffmpeg is not found."""
    from autosubs.cli.utils import check_ffmpeg_installed

    with pytest.raises(Exit):
        check_ffmpeg_installed()
