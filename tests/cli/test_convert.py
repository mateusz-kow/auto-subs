from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autosubs.cli import app

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


def test_cli_convert_batch(tmp_path: Path, tmp_srt_file: Path, tmp_vtt_file: Path, sample_ass_content: str) -> None:
    """Test successful conversion of a directory of subtitle files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    ass_file_name = (
        "very long name that might be too long for some operational systems and "
        "it even contains spaces and is very very very very very very long.ass"
    )

    # Move the fixture files into the input directory
    tmp_srt_file.rename(input_dir / tmp_srt_file.name)
    tmp_vtt_file.rename(input_dir / tmp_vtt_file.name)
    (input_dir / ass_file_name).write_text(sample_ass_content)

    result = runner.invoke(app, ["convert", str(input_dir), "-o", str(output_dir), "-f", "srt"])

    assert result.exit_code == 0
    assert "Processing: test.srt" in result.stdout
    assert "Processing: test.vtt" in result.stdout
    assert f"Processing: {ass_file_name}" in result.stdout
    assert (output_dir / "test.srt").exists()
    assert (output_dir / "test.srt").read_text().strip().endswith("This is a test.")
    assert (output_dir / "test.vtt.srt").exists()
    assert (output_dir / f"{ass_file_name}.srt").exists()


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
