import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from autosubs.cli import app

runner = CliRunner()


@patch("shutil.which", return_value="/usr/bin/ffmpeg")
@patch("subprocess.run")
def test_cli_burn_success_with_output_path(
    mock_run: MagicMock, mock_which: MagicMock, fake_video_file: Path, tmp_srt_file: Path
) -> None:
    """Test successful burning when an explicit output path is provided."""
    output_file = fake_video_file.with_suffix(".burned.mp4")
    result = runner.invoke(app, ["burn", str(fake_video_file), str(tmp_srt_file), "-o", str(output_file)])

    assert result.exit_code == 0
    assert "Successfully burned subtitles" in result.stdout
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert str(fake_video_file) in args[0]
    assert str(output_file) in args[0]


@patch("autosubs.cli.burn.handle_burn_operation")
@patch("autosubs.cli.burn.check_ffmpeg_installed")
def test_cli_burn_default_output_name_is_stem_burned(
    mock_check_ffmpeg: MagicMock,
    mock_handle_burn: MagicMock,
    fake_video_file: Path,
    tmp_srt_file: Path,
) -> None:
    """Test that the default output name uses the '_burned' suffix."""
    result = runner.invoke(app, ["burn", str(fake_video_file), str(tmp_srt_file)])

    assert result.exit_code == 0
    mock_handle_burn.assert_called_once()
    _, kwargs = mock_handle_burn.call_args

    expected_output_path = fake_video_file.with_stem(f"{fake_video_file.stem}_burned")
    assert kwargs["video_output"] == expected_output_path


@patch("shutil.which", return_value=None)
def test_cli_burn_ffmpeg_not_found(mock_which: MagicMock, fake_video_file: Path, tmp_srt_file: Path) -> None:
    """Test that burn command fails gracefully if FFmpeg is not found."""
    result = runner.invoke(app, ["burn", str(fake_video_file), str(tmp_srt_file)])
    assert result.exit_code == 1
    assert "Error: FFmpeg executable not found" in result.stdout


@patch(
    "subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "ffmpeg", stderr="FFmpeg error"),
)
@patch("shutil.which", return_value="/usr/bin/ffmpeg")
def test_cli_burn_ffmpeg_fails(
    mock_which: MagicMock, mock_run: MagicMock, fake_video_file: Path, tmp_srt_file: Path
) -> None:
    """Test that the CLI reports an error if the FFmpeg process fails."""
    result = runner.invoke(app, ["burn", str(fake_video_file), str(tmp_srt_file)])

    assert result.exit_code == 1
    assert "An unexpected error occurred while burning subtitles" in result.stdout
    assert "FFmpeg error" in result.stdout


# --- New Comprehensive Tests ---


@pytest.mark.parametrize(
    "subtitle_fixture",
    [
        "tmp_srt_file",
        "tmp_vtt_file",
        "tmp_ass_file",
    ],
)
@patch("shutil.which", return_value="/usr/bin/ffmpeg")
@patch("autosubs.cli.burn.handle_burn_operation")
def test_cli_burn_with_all_supported_subtitle_formats(
    mock_handle_burn: MagicMock,
    mock_which: MagicMock,
    fake_video_file: Path,
    subtitle_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the burn command accepts .srt, .vtt, and .ass files."""
    subtitle_file = request.getfixturevalue(subtitle_fixture)
    result = runner.invoke(app, ["burn", str(fake_video_file), str(subtitle_file)])
    assert result.exit_code == 0
    mock_handle_burn.assert_called_once()


@patch("shutil.which", return_value="/usr/bin/ffmpeg")
@patch("autosubs.cli.burn.handle_burn_operation")
def test_cli_burn_with_path_containing_spaces(
    mock_handle_burn: MagicMock, mock_which: MagicMock, tmp_path: Path
) -> None:
    """Test that files with spaces in their names are handled correctly."""
    video_with_spaces = tmp_path / "my test video.mp4"
    subs_with_spaces = tmp_path / "my subs file.srt"
    video_with_spaces.touch()
    subs_with_spaces.write_text("dummy content")

    result = runner.invoke(app, ["burn", str(video_with_spaces), str(subs_with_spaces)])

    assert result.exit_code == 0
    mock_handle_burn.assert_called_once()
    _, kwargs = mock_handle_burn.call_args
    assert kwargs["video_input"] == video_with_spaces
    assert kwargs["subtitle_content"] == "dummy content"


def test_cli_burn_input_file_does_not_exist(tmp_path: Path) -> None:
    """Test that Typer's built-in validation catches non-existent files."""
    existing_video = tmp_path / "video.mp4"
    existing_video.touch()
    non_existent_file = "non_existent_file.srt"

    result = runner.invoke(app, ["burn", str(existing_video), non_existent_file])
    assert result.exit_code == 2

    assert "Invalid value for 'SUBTITLE_INPUT'" in result.stderr


@patch("shutil.which", return_value="/usr/bin/ffmpeg")
def test_cli_burn_output_path_is_a_directory(
    mock_which: MagicMock, fake_video_file: Path, tmp_srt_file: Path, tmp_path: Path
) -> None:
    """Test that the command fails if the output path is a directory."""
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()

    # The underlying OS error might differ, but it should fail.
    # We expect a failure during the subprocess call.
    result = runner.invoke(app, ["burn", str(fake_video_file), str(tmp_srt_file), "-o", str(output_dir)])

    assert result.exit_code == 1
    assert "An unexpected error occurred" in result.stdout
