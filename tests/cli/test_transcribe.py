import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autosubs.cli import app
from autosubs.models.settings import AssSettings

runner = CliRunner()


@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_success(mock_api_transcribe: MagicMock, fake_media_file: Path) -> None:
    """Test successful transcription of a single media file."""
    mock_api_transcribe.return_value = "WEBVTT\n\n00:00:00.100 --> 00:00:01.200\nHello world"
    output_file = fake_media_file.with_suffix(".vtt")

    result = runner.invoke(
        app,
        [
            "transcribe",
            str(fake_media_file),
            "-f",
            "vtt",
            "--model",
            "tiny",
            "-o",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    mock_api_transcribe.assert_called_once()
    args, kwargs = mock_api_transcribe.call_args
    assert args[0] == fake_media_file
    assert kwargs["output_format"] == "vtt"
    assert kwargs["model_name"] == "tiny"
    assert "Successfully saved subtitles" in result.stdout


@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_batch(mock_api_transcribe: MagicMock, tmp_path: Path) -> None:
    """Test successful transcription of a directory of media files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / "test1.mp3").touch()
    (input_dir / "test2.mp4").touch()
    (input_dir / "ignored.txt").touch()

    mock_api_transcribe.return_value = "1\n00:00:00,100 --> 00:00:01,200\nHello"

    result = runner.invoke(app, ["transcribe", str(input_dir), "-o", str(output_dir), "-f", "srt"])

    assert result.exit_code == 0
    assert mock_api_transcribe.call_count == 2
    assert "Transcribing: test1.mp3" in result.stdout
    assert "Transcribing: test2.mp4" in result.stdout
    assert "ignored.txt" not in result.stdout
    assert (output_dir / "test1.srt").exists()
    assert (output_dir / "test2.srt").exists()


@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_karaoke_with_ass(mock_transcribe_api: MagicMock, fake_media_file: Path) -> None:
    """Test that the --karaoke flag is correctly passed to the API for ASS format."""
    mock_transcribe_api.return_value = "[Script Info]\nDialogue: ..."
    runner.invoke(app, ["transcribe", str(fake_media_file), "-f", "ass", "--karaoke"])

    mock_transcribe_api.assert_called_once()
    _, kwargs = mock_transcribe_api.call_args
    assert isinstance(kwargs["ass_settings"], AssSettings)
    assert kwargs["ass_settings"].highlight_style is not None


@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_karaoke_with_non_ass_warning(mock_transcribe_api: MagicMock, fake_media_file: Path) -> None:
    """Test that a warning is shown when using --karaoke with a non-ASS format."""
    mock_transcribe_api.return_value = "1\n00:00:00,100 --> 00:00:01,200\nHello"
    result = runner.invoke(app, ["transcribe", str(fake_media_file), "-f", "srt", "--karaoke"])

    assert result.exit_code == 0
    assert "Warning: --karaoke flag is only applicable for ASS format." in result.stdout
    _, kwargs = mock_transcribe_api.call_args
    assert kwargs["ass_settings"] is None


@patch(
    "autosubs.cli.transcribe.transcribe_api",
    side_effect=ImportError("whisper not found"),
)
def test_cli_transcribe_import_error(mock_transcribe_api: MagicMock, fake_media_file: Path) -> None:
    """Test that a friendly message is shown on ImportError."""
    result = runner.invoke(app, ["transcribe", str(fake_media_file)])

    assert result.exit_code == 1
    assert "Error: whisper not found" in result.stdout
    assert "Please ensure 'auto-subs[transcribe]' is installed" in result.stdout


@patch(
    "autosubs.cli.transcribe.transcribe_api",
    side_effect=Exception("A generic error occurred"),
)
def test_cli_transcribe_generic_error(mock_transcribe_api: MagicMock, fake_media_file: Path) -> None:
    """Test that a generic error during transcription is caught and reported."""
    result = runner.invoke(app, ["transcribe", str(fake_media_file)])

    assert result.exit_code == 1
    assert f"An unexpected error occurred while processing {fake_media_file.name}" in result.stdout
    assert "A generic error occurred" in result.stdout


@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_ass_with_style_file(
    mock_transcribe_api: MagicMock, fake_media_file: Path, tmp_path: Path
) -> None:
    """Test that --style-file correctly loads and applies ASS style settings for transcribe."""
    mock_transcribe_api.return_value = "dummy ass content"

    style_file = tmp_path / "styles.json"
    custom_styles = {
        "font_name": "Impact",
        "font_size": 72,
        "primary_color": "&H0000FFFF&",  # Yellow
    }
    style_file.write_text(json.dumps(custom_styles))

    result = runner.invoke(
        app,
        [
            "transcribe",
            str(fake_media_file),
            "-f",
            "ass",
            "--style-file",
            str(style_file),
        ],
    )

    assert result.exit_code == 0
    mock_transcribe_api.assert_called_once()
    _, kwargs = mock_transcribe_api.call_args

    passed_settings = kwargs.get("ass_settings")
    assert isinstance(passed_settings, AssSettings)

    # Verify that the custom settings from the file were applied
    assert passed_settings.font == "Impact"
    assert passed_settings.font_size == 72
    assert passed_settings.primary_color == "&H0000FFFF&"
