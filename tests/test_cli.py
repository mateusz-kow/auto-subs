import json
from pathlib import Path

from typer.testing import CliRunner

from auto_subs import __version__
from auto_subs.cli import app
from auto_subs.typing.transcription import TranscriptionDict

runner = CliRunner()


def test_cli_version() -> None:
    """Test the --version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"auto-subs version: {__version__}" in result.stdout


def test_cli_generate_srt_success(tmp_path: Path, sample_transcription: TranscriptionDict) -> None:
    """Test successful generation of an SRT file."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.srt"
    input_file.write_text(json.dumps(sample_transcription))

    result = runner.invoke(app, ["generate", str(input_file), "-o", str(output_file), "-f", "srt"])

    assert result.exit_code == 0
    assert "Successfully saved subtitles" in result.stdout
    assert output_file.exists()
    content = output_file.read_text()
    assert "-->" in content
    assert "This is a test transcription for" in content


def test_cli_generate_ass_default_output(tmp_path: Path, sample_transcription: TranscriptionDict) -> None:
    """Test successful generation with a default output path."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    result = runner.invoke(app, ["generate", str(input_file), "-f", "ass"])

    output_file = tmp_path / "input.ass"
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "[Script Info]" in content
    assert "Dialogue:" in content


def test_cli_file_not_found() -> None:
    """Test error handling for a non-existent input file."""
    # Use an environment that disables rich formatting for predictable, plain-text errors.
    env = {"TERM": "dumb", "NO_COLOR": "1"}
    result = runner.invoke(app, ["generate", "non_existent_file.json"], env=env)
    assert result.exit_code == 2  # typer's exit code for bad parameters

    # In a plain-text environment, the error message is simple and predictable.
    assert "Invalid value" in result.stderr
    assert "non_existent_file.json" in result.stderr


def test_cli_invalid_json(tmp_path: Path) -> None:
    """Test error handling for a file with invalid JSON."""
    input_file = tmp_path / "invalid.json"
    input_file.write_text("{'not': 'valid json'}")

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    assert "Error reading or parsing input file" in result.stdout


def test_cli_validation_error(tmp_path: Path) -> None:
    """Test error handling for JSON that fails schema validation."""
    input_file = tmp_path / "invalid_schema.json"
    # Valid JSON, but invalid transcription schema (missing 'segments')
    input_file.write_text(json.dumps({"text": "hello", "language": "en"}))

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    assert "Input file validation error" in result.stdout


def test_cli_write_error(tmp_path: Path, sample_transcription: TranscriptionDict) -> None:
    """Test error handling for an OSError during file writing."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    # Create a directory where the output file should be, to cause a write error
    output_path_as_dir = tmp_path / "output.srt"
    output_path_as_dir.mkdir()

    result = runner.invoke(app, ["generate", str(input_file), "-o", str(output_path_as_dir)])

    assert result.exit_code == 1
    assert f"Error writing to file {output_path_as_dir}" in result.stdout
