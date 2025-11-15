from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from autosubs.cli import app
from autosubs.models.formats import SubtitleFormat

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
def test_cli_transcribe_ass_with_style_config(
    mock_transcribe_api: MagicMock, fake_media_file: Path, tmp_style_config_file: Path
) -> None:
    """Test that --style-config correctly passes the path to the API for transcribe."""
    mock_transcribe_api.return_value = "dummy ass content"

    result = runner.invoke(
        app,
        [
            "transcribe",
            str(fake_media_file),
            "-f",
            "ass",
            "--style-config",
            str(tmp_style_config_file),
        ],
    )

    assert result.exit_code == 0
    mock_transcribe_api.assert_called_once()
    _, kwargs = mock_transcribe_api.call_args
    assert kwargs.get("style_config_path") == tmp_style_config_file


@patch("shutil.which", return_value="/usr/bin/ffmpeg")
@patch("subprocess.run")
@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_burn_success(
    mock_transcribe: MagicMock,
    mock_run: MagicMock,
    mock_which: MagicMock,
    fake_video_file: Path,
) -> None:
    """Test successful end-to-end transcription and burning."""
    mock_transcribe.return_value = "1\n00:00:00,100 --> 00:00:01,200\nHello"
    result = runner.invoke(app, ["transcribe", str(fake_video_file), "--burn"])

    assert result.exit_code == 0
    mock_transcribe.assert_called_once()
    mock_run.assert_called_once()
    assert "Successfully burned subtitles into video" in result.stdout


@pytest.mark.parametrize(
    ("flags", "expected_verbose"),
    [
        ([], None),
        (["--stream"], False),
        (["--whisper-verbose"], True),
    ],
)
@patch("autosubs.cli.transcribe.transcribe_api")
def test_cli_transcribe_verbose_and_stream_flags(
    mock_api_transcribe: MagicMock,
    fake_media_file: Path,
    flags: list[str],
    expected_verbose: bool | None,
) -> None:
    """Test that --stream and --whisper-verbose set the correct verbosity level."""
    mock_api_transcribe.return_value = "dummy"
    runner.invoke(app, ["transcribe", str(fake_media_file), *flags])
    mock_api_transcribe.assert_called_once()
    _, kwargs = mock_api_transcribe.call_args
    assert kwargs["verbose"] == expected_verbose


@patch("autosubs.cli.utils.handle_burn_operation")
@patch("autosubs.cli.transcribe.transcribe_api")
@patch("shutil.which", return_value="/usr/bin/ffmpeg")
def test_cli_transcribe_burn_skips_non_video_files(
    mock_which: MagicMock,
    mock_api: MagicMock,
    mock_burn: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that --burn skips audio files and does not call the burn handler."""
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    mock_api.return_value = "dummy srt"

    result = runner.invoke(app, ["transcribe", str(audio_file), "--burn"])

    assert result.exit_code == 0
    assert "Skipping non-video file for burning: test.mp3" in result.stdout
    mock_burn.assert_not_called()


@patch("autosubs.cli.transcribe.handle_burn_operation")
@patch("autosubs.cli.transcribe.transcribe_api")
@patch("shutil.which", return_value="/usr/bin/ffmpeg")
def test_cli_transcribe_burn_batch_preserves_extension(
    mock_which: MagicMock,
    mock_api: MagicMock,
    mock_burn: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that batch transcription with burning preserves the original video extension."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    video_file = input_dir / "video.mkv"
    video_file.touch()

    mock_api.return_value = "dummy srt content"

    result = runner.invoke(app, ["transcribe", str(input_dir), "-o", str(output_dir), "--burn", "-f", "srt"])

    assert result.exit_code == 0
    mock_burn.assert_called_once()
    _, kwargs = mock_burn.call_args
    expected_output_path = output_dir / "video.mkv"
    assert kwargs["video_output"] == expected_output_path
    assert kwargs["subtitle_format"] == SubtitleFormat.SRT
