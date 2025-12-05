from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autosubs.cli import app
from autosubs.cli.utils import get_default_styler_engine
from autosubs.core.styler import BaseStyler

runner = CliRunner()


def test_cli_convert_success(tmp_srt_file: Path) -> None:
    """Test successful conversion of a single subtitle file."""
    output_file = tmp_srt_file.with_suffix(".vtt")
    result = runner.invoke(app, ["convert", str(tmp_srt_file), "-o", str(output_file), "-f", "vtt"])

    assert result.exit_code == 0
    assert "Successfully saved converted subtitles" in result.stdout
    assert output_file.exists()
    content = output_file.read_text()
    assert "WEBVTT" in content
    assert "00:00:00.500 --> 00:00:01.500" in content


def test_cli_convert_batch(tmp_path: Path, tmp_srt_file: Path, tmp_vtt_file: Path) -> None:
    """Test successful conversion of a directory of subtitle files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    tmp_srt_file.rename(input_dir / tmp_srt_file.name)
    tmp_vtt_file.rename(input_dir / tmp_vtt_file.name)

    result = runner.invoke(app, ["convert", str(input_dir), "-o", str(output_dir), "-f", "srt"])

    assert result.exit_code == 0
    assert "Processing: test.srt" in result.stdout
    assert "Processing: test.vtt" in result.stdout
    assert (output_dir / "test.srt.srt").exists()
    assert (output_dir / "test.vtt.srt").exists()


def test_cli_convert_batch_with_long_filename(tmp_path: Path, sample_srt_content: str) -> None:
    """Test that batch conversion correctly handles files with maximum-length names."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    # Create a filename close to the common 255-character limit
    long_name = "a" * 100 + ".srt"
    (input_dir / long_name).write_text(sample_srt_content)

    result = runner.invoke(app, ["convert", str(input_dir), "-o", str(output_dir), "-f", "vtt"])

    assert result.exit_code == 0
    assert f"Processing: {long_name}" in result.stdout
    expected_output_name = f"{long_name}.vtt"
    output_file = output_dir / expected_output_name
    assert output_file.exists()
    assert "WEBVTT" in output_file.read_text()


def test_cli_convert_unsupported_input(tmp_path: Path) -> None:
    """Test that `convert` fails for an unsupported input file type."""
    input_file = tmp_path / "test.txt"
    input_file.touch()

    result = runner.invoke(app, ["convert", str(input_file), "-f", "srt"])
    assert result.exit_code == 1
    assert "Error: Unsupported input file format: .txt" in result.stdout


def test_cli_convert_input_dir_output_file_error(tmp_path: Path) -> None:
    """Test that `convert` fails if input is a directory and output is a file."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_file = tmp_path / "output.srt"

    result = runner.invoke(app, ["convert", str(input_dir), "-o", str(output_file)])
    assert result.exit_code == 1
    assert "Error: If input is a directory, output must also be a directory." in result.stdout


@patch("autosubs.cli.convert.load", side_effect=ValueError("Corrupted subtitle file"))
def test_cli_convert_processing_error(mock_load: MagicMock, tmp_srt_file: Path) -> None:
    """Test that the CLI handles errors during file processing and exits correctly."""
    result = runner.invoke(app, ["convert", str(tmp_srt_file), "-f", "vtt"])

    assert result.exit_code == 1
    assert "Error processing file" in result.stdout
    assert "Corrupted subtitle file" in result.stdout


def test_get_default_styler_engine() -> None:
    """Test that _get_default_styler_engine returns a valid StylerEngine."""
    engine = get_default_styler_engine()
    assert isinstance(engine, BaseStyler)
    assert engine.config.styles
    assert engine.config.styles[0]["Name"] == "Default"
