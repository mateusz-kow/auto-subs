from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from autosubs.cli.main import app
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord
from tests.utils import strip_ansi

runner = CliRunner()


@pytest.fixture
def mock_subtitles() -> Subtitles:
    """Provides a mock Subtitles object for testing."""
    segments = [
        SubtitleSegment(words=[SubtitleWord("Hello", 1.0, 2.0)]),
        SubtitleSegment(words=[SubtitleWord("world", 3.0, 4.0)]),
    ]
    subtitles = Subtitles(segments=segments)
    subtitles.transform_framerate = MagicMock(return_value=subtitles)  # type: ignore[method-assign]
    return subtitles


@patch("autosubs.cli.framerate.load")
def test_cli_framerate_success(mock_load: MagicMock, mock_subtitles: Subtitles, tmp_path: Path) -> None:
    """Test successful framerate conversion with explicit output path."""
    mock_load.return_value = mock_subtitles
    input_file = tmp_path / "input.srt"
    input_file.touch()
    output_file = tmp_path / "output.srt"

    result = runner.invoke(
        app,
        [
            "framerate",
            str(input_file),
            "--fps-from",
            "23.976",
            "--fps-to",
            "25",
            "-o",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Successfully saved to:" in result.stdout
    mock_load.assert_called_once_with(input_file, encoding=None)
    mock_subtitles.transform_framerate.assert_called_once()  # type: ignore[attr-defined]
    _args, kwargs = mock_subtitles.transform_framerate.call_args  # type: ignore[attr-defined]
    assert kwargs["source_fps"] == pytest.approx(23.976)
    assert kwargs["target_fps"] == pytest.approx(25.0)
    assert output_file.exists()
    # The subtitles object returned by the fixture is real, so we can check real output
    assert "Hello" in output_file.read_text(encoding="utf-8")


@patch("autosubs.cli.framerate.load")
def test_cli_framerate_default_output(mock_load: MagicMock, mock_subtitles: Subtitles, tmp_path: Path) -> None:
    """Test framerate conversion using the default output path."""
    mock_load.return_value = mock_subtitles
    input_file = tmp_path / "video.srt"
    input_file.touch()
    expected_output = tmp_path / "video_newfps.srt"

    result = runner.invoke(
        app,
        ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25"],
    )

    assert result.exit_code == 0, result.stdout
    assert f"Successfully saved to: {expected_output}" in result.stdout
    assert expected_output.exists()


@patch("autosubs.cli.framerate.load")
def test_cli_framerate_format_inference(mock_load: MagicMock, mock_subtitles: Subtitles, tmp_path: Path) -> None:
    """Test that output format is correctly inferred."""
    mock_load.return_value = mock_subtitles
    input_file = tmp_path / "input.srt"
    input_file.touch()

    # Case 1: Inferred from output path extension
    output_vtt = tmp_path / "output.vtt"
    runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25", "-o", str(output_vtt)])
    assert "WEBVTT" in output_vtt.read_text()

    # Case 2: Inferred from input path when output is not specified
    expected_srt = tmp_path / "input_newfps.srt"
    runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25"])
    assert "-->" in expected_srt.read_text()

    # Case 3: Explicit --format overrides everything
    output_ass = tmp_path / "output.ass"
    runner.invoke(
        app,
        ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25", "-o", str(output_ass), "-f", "ass"],
    )
    assert "[Events]" in output_ass.read_text()


@patch("autosubs.cli.utils.get_default_styler_engine")
@patch("autosubs.cli.framerate.load")
def test_cli_framerate_ass_format_uses_styler(
    mock_load: MagicMock, mock_styler: MagicMock, mock_subtitles: Subtitles, tmp_path: Path
) -> None:
    """Test that ASS output format correctly invokes the styler engine."""
    mock_load.return_value = mock_subtitles
    input_file = tmp_path / "input.srt"
    input_file.touch()

    runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25", "-f", "ass"])
    mock_styler.assert_called_once()


def test_cli_framerate_invalid_fps_values(tmp_path: Path) -> None:
    """Test that the CLI rejects invalid FPS values."""
    input_file = tmp_path / "input.srt"
    input_file.touch()

    result = runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "24"])
    assert result.exit_code != 0
    assert "Source and target framerates cannot be the same" in strip_ansi(result.stderr)

    result = runner.invoke(app, ["framerate", str(input_file), "--fps-from", "-1", "--fps-to", "25"])
    assert result.exit_code != 0
    assert "Framerate values must be positive" in strip_ansi(result.stderr)

    result = runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "0"])
    assert result.exit_code != 0
    assert "Framerate values must be positive" in strip_ansi(result.stderr)


def test_cli_framerate_missing_fps_options(tmp_path: Path) -> None:
    """Test that Typer correctly reports missing required FPS options."""
    input_file = tmp_path / "input.srt"
    input_file.touch()

    result = runner.invoke(app, ["framerate", str(input_file), "--fps-to", "25"])
    assert result.exit_code != 0
    assert "Missing option '--fps-from'" in strip_ansi(result.stderr)

    result = runner.invoke(app, ["framerate", str(input_file), "--fps-from", "24"])
    assert result.exit_code != 0
    assert "Missing option '--fps-to'" in strip_ansi(result.stderr)


@patch("autosubs.cli.framerate.load")
def test_cli_framerate_encoding(mock_load: MagicMock, mock_subtitles: Subtitles, tmp_path: Path) -> None:
    """Test that the encoding parameter is correctly handled."""
    mock_load.return_value = mock_subtitles
    input_file = tmp_path / "input.srt"
    input_file.write_text("hello", encoding="latin-1")
    output_file = tmp_path / "output.srt"

    # Mock write_text to check encoding
    with patch.object(Path, "write_text") as mock_write_text:
        runner.invoke(
            app,
            [
                "framerate",
                str(input_file),
                "--fps-from",
                "24",
                "--fps-to",
                "25",
                "-o",
                str(output_file),
                "-e",
                "latin-1",
            ],
        )
        mock_load.assert_called_with(input_file, encoding="latin-1")
        mock_write_text.assert_called_once()
        # The first arg is content, the second is kwargs dict
        assert mock_write_text.call_args[1].get("encoding") == "latin-1"

    # Test default encoding (utf-8)
    with patch.object(Path, "write_text") as mock_write_text:
        runner.invoke(
            app,
            ["framerate", str(input_file), "--fps-from", "24", "--fps-to", "25", "-o", str(output_file)],
        )
        mock_load.assert_called_with(input_file, encoding=None)  # Called with None
        mock_write_text.assert_called_once()
        assert mock_write_text.call_args[1].get("encoding") == "utf-8"
