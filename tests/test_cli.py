import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_cli_generate_batch(tmp_path: Path, sample_transcription: TranscriptionDict) -> None:
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


@patch("auto_subs.cli.transcribe_api")
def test_cli_transcribe_success(mock_api_transcribe: MagicMock, fake_media_file: Path) -> None:
    """Test successful transcription of a single media file."""
    mock_api_transcribe.return_value = "WEBVTT\n\n00:00:00.100 --> 00:00:01.200\nHello world"
    output_file = fake_media_file.with_suffix(".vtt")

    result = runner.invoke(
        app, ["transcribe", str(fake_media_file), "-f", "vtt", "--model", "tiny", "-o", str(output_file)]
    )

    assert result.exit_code == 0
    mock_api_transcribe.assert_called_once()
    args, kwargs = mock_api_transcribe.call_args
    assert args[0] == fake_media_file
    assert kwargs["output_format"] == "vtt"
    assert kwargs["model_name"] == "tiny"
    assert "Successfully saved subtitles" in result.stdout


@patch("auto_subs.cli.transcribe_api")
def test_cli_transcribe_batch(mock_api_transcribe: MagicMock, tmp_path: Path) -> None:
    """Test successful transcription of a directory of media files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / "test1.mp3").touch()
    (input_dir / "test2.mp4").touch()
    (input_dir / "ignored.txt").touch()  # Should be ignored

    mock_api_transcribe.return_value = "1\n00:00:00,100 --> 00:00:01,200\nHello"

    result = runner.invoke(app, ["transcribe", str(input_dir), "-o", str(output_dir), "-f", "srt"])

    assert result.exit_code == 0
    assert mock_api_transcribe.call_count == 2
    assert "Transcribing: test1.mp3" in result.stdout
    assert "Transcribing: test2.mp4" in result.stdout
    assert "ignored.txt" not in result.stdout
    assert (output_dir / "test1.srt").exists()
    assert (output_dir / "test2.srt").exists()


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

    # Determine the default output filename based on input and format (SRT default)
    target_output_file = input_file.with_suffix(".srt")

    # Create a directory at the target output path.
    # Attempting to write to a path that is a directory raises OSError.
    target_output_file.mkdir()

    result = runner.invoke(app, ["generate", str(input_file), "-f", "srt"])

    assert result.exit_code == 1
    assert f"Error writing to file {target_output_file}" in result.stdout


@patch("auto_subs.cli.auto_subs.generate", return_value="[Script Info]\nDialogue: Test")
def test_cli_generate_karaoke_with_ass(mock_generate, tmp_path: Path, sample_transcription) -> None:
    """Test --karaoke flag correctly applies ASS karaoke style."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "-f",
            "ass",
            "--karaoke",
        ],
    )

    assert result.exit_code == 0
    assert "Generating subtitles in ASS format" in result.stdout
    # Karaoke flag should not trigger a warning here
    assert "Warning" not in result.stdout
    # Ensure the generator was called once
    mock_generate.assert_called_once()
    # Karaoke ASS settings should be applied (highlight_style should exist)
    _, kwargs = mock_generate.call_args
    assert hasattr(kwargs["ass_settings"], "highlight_style")
    assert kwargs["ass_settings"].highlight_style is not None


@patch("auto_subs.cli.auto_subs.generate", return_value="1\n00:00:00,000 --> 00:00:02,000\nHello")
def test_cli_generate_karaoke_non_ass(mock_generate, tmp_path: Path, sample_transcription) -> None:
    """Test --karaoke flag with non-ASS format shows a warning and still generates output."""
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_transcription))

    result = runner.invoke(
        app,
        [
            "generate",
            str(input_file),
            "-f",
            "srt",
            "--karaoke",
        ],
    )

    assert result.exit_code == 0
    assert "Warning: --karaoke flag is only applicable for ASS format." in result.stdout
    assert "Successfully saved subtitles" in result.stdout
    # The karaoke highlight_style should NOT be applied for SRT
    _, kwargs = mock_generate.call_args
    assert not hasattr(kwargs["ass_settings"], "highlight_style") or kwargs["ass_settings"].highlight_style is None
