import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autosubs.cli import app
from autosubs.models.settings import AssSettings

runner = CliRunner()


def test_cli_generate_srt_success(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
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
    assert "Error reading or parsing input file" in result.stdout


def test_cli_validation_error(tmp_path: Path) -> None:
    """Test error handling for JSON that fails schema validation."""
    input_file = tmp_path / "invalid_schema.json"
    # Valid JSON, but invalid transcription schema (missing 'segments')
    input_file.write_text(json.dumps({"text": "hello", "language": "en"}))

    result = runner.invoke(app, ["generate", str(input_file)])
    assert result.exit_code == 1
    assert "Input file validation error" in result.stdout


def test_cli_write_error(tmp_path: Path, sample_transcription: dict[str, Any]) -> None:
    """Test error handling for an OSError during file writing."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    # Create a directory where the file should be, causing an OSError on write
    (input_file.with_suffix(".srt")).mkdir()

    result = runner.invoke(app, ["generate", str(input_file), "-f", "srt"])

    assert result.exit_code == 1
    assert f"Error reading or parsing input file {input_file.name}" in result.stdout


@patch("autosubs.cli.generate.generate_api")
def test_cli_generate_karaoke_with_ass(
    mock_generate_api: MagicMock, tmp_path: Path, sample_transcription: dict[str, Any]
) -> None:
    """Test --karaoke flag correctly applies ASS karaoke style."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))
    mock_generate_api.return_value = "[Script Info]\nDialogue: Test"

    result = runner.invoke(app, ["generate", str(input_file), "-f", "ass", "--karaoke"])

    assert result.exit_code == 0
    mock_generate_api.assert_called_once()
    _, kwargs = mock_generate_api.call_args
    assert isinstance(kwargs["ass_settings"], AssSettings)
    assert kwargs["ass_settings"].highlight_style is not None


@patch("autosubs.cli.generate.generate_api")
def test_cli_generate_karaoke_non_ass(
    mock_generate_api: MagicMock, tmp_path: Path, sample_transcription: dict[str, Any]
) -> None:
    """Test --karaoke flag with non-ASS format shows a warning and still generates output."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))
    mock_generate_api.return_value = "1\n00:00:00,000 --> 00:00:02,000\nHello"

    result = runner.invoke(app, ["generate", str(input_file), "-f", "srt", "--karaoke"])

    assert result.exit_code == 0
    assert "Warning: --karaoke flag is only applicable for ASS format." in result.stdout
    assert "Successfully saved subtitles" in result.stdout
    _, kwargs = mock_generate_api.call_args
    assert kwargs["ass_settings"] is None


@patch("autosubs.cli.generate.generate_api")
def test_cli_generate_ass_with_style_file(
    mock_generate_api: MagicMock, tmp_path: Path, sample_transcription: dict[str, Any]
) -> None:
    """Test that --style-file correctly loads and applies ASS style settings."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    style_file = tmp_path / "styles.json"
    custom_styles = {
        "font_name": "Impact",
        "font_size": 72,
        "primary_color": "&H0000FFFF&",  # Yellow
    }
    style_file.write_text(json.dumps(custom_styles))

    mock_generate_api.return_value = "dummy ass content"

    result = runner.invoke(app, ["generate", str(input_file), "-f", "ass", "--style-file", str(style_file)])

    assert result.exit_code == 0
    mock_generate_api.assert_called_once()
    _, kwargs = mock_generate_api.call_args

    passed_settings = kwargs.get("ass_settings")
    assert isinstance(passed_settings, AssSettings)

    # Verify that the custom settings from the file were applied
    assert passed_settings.font == "Impact"
    assert passed_settings.font_size == 72
    assert passed_settings.primary_color == "&H0000FFFF&"
