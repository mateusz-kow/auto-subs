import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autosubs.cli import app

runner = CliRunner()


def test_cli_generate_srt_success(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
    """Test successful generation of an SRT file."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.srt"
    input_file.write_text(json.dumps(sample_transcription))

    result = runner.invoke(app, ["generate", str(input_file), "-o", str(output_file), "-f", "srt"])

    assert result.exit_code == 0
    assert "Successfully saved to:" in result.stdout
    assert output_file.exists()
    content = output_file.read_text()
    assert "-->" in content
    assert "This is a test transcription for" in content


def test_cli_generate_ass_default_output(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
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


def test_cli_generate_batch(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
    """Test successful generation for a directory of JSON files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / "test1.json").write_text(json.dumps(sample_transcription))
    (input_dir / "test2.json").write_text(json.dumps(sample_transcription))

    result = runner.invoke(app, ["generate", str(input_dir), "-o", str(output_dir), "-f", "vtt"])

    assert result.exit_code == 0
    assert "Processing: test1.json" in result.stdout
    assert "Processing: test2.json" in result.stdout
    assert (output_dir / "test1.vtt").exists()
    assert (output_dir / "test2.vtt").exists()


def test_cli_invalid_json(tmp_path: Path) -> None:
    """Test error handling for a file with invalid JSON."""
    input_file = tmp_path / "invalid.json"
    input_file.write_text("{'not': 'valid json'}")

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    assert "Error processing" in result.stdout
    assert "Failed to parse JSON" in result.stdout


def test_cli_validation_error(tmp_path: Path) -> None:
    """Test error handling for JSON that fails schema validation."""
    input_file = tmp_path / "invalid_schema.json"
    input_file.write_text(json.dumps({"text": "hello", "language": "en"}))

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    assert "Error processing" in result.stdout
    assert "validation error" in result.stdout


def test_cli_write_error(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
    """Test error handling for an OSError during file writing."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    (input_file.with_suffix(".srt")).mkdir()

    result = runner.invoke(app, ["generate", str(input_file), "-f", "srt"])

    assert result.exit_code == 1
    assert f"Error processing {input_file.name}" in result.stdout


@patch("autosubs.cli.generate.generate_api")
def test_cli_generate_ass_with_style_config(
    mock_generate_api: MagicMock,
    tmp_path: Path,
    sample_transcription: dict[str, Any],
    tmp_style_config_file: Path,
) -> None:
    """Test that --style-config correctly passes the path to the API."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))
    mock_generate_api.return_value = "dummy ass content"

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "-f",
            "ass",
            "--style-config",
            str(tmp_style_config_file),
        ],
    )

    assert result.exit_code == 0
    mock_generate_api.assert_called_once()
    _, kwargs = mock_generate_api.call_args
    assert kwargs.get("style_config_path") == tmp_style_config_file
