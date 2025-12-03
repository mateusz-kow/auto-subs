import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autosubs.core.burner import FFmpegError, burn_subtitles


@patch("subprocess.run")
def test_burn_subtitles_success(mock_run: MagicMock, tmp_path: Path) -> None:
    """Test that burn_subtitles constructs the correct FFmpeg command."""
    video_in = tmp_path / "in.mp4"
    subs_in = tmp_path / "in.ass"
    video_out = tmp_path / "out.mp4"
    mock_run.return_value = MagicMock(stdout="", stderr="")

    burn_subtitles(video_in, subs_in, video_out)

    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    command = args[0]

    assert command[0] == "ffmpeg"
    assert str(video_in) in command
    assert str(video_out) in command
    assert "-c:a" in command
    assert "copy" in command
    assert "subtitles=" in command[5]  # Check the -vf filter

    # Replicate the exact escaping logic from the implementation to create the expected path string.
    expected_path_str = str(subs_in.resolve()).replace("\\", "\\\\")
    if ":" in expected_path_str:
        expected_path_str = expected_path_str.replace(":", "\\:")

    assert expected_path_str in command[5]


@patch(
    "subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "ffmpeg", stderr="Test error"),
)
def test_burn_subtitles_ffmpeg_fails_raises_ffmpeg_error(mock_run: MagicMock, tmp_path: Path) -> None:
    """Test that a CalledProcessError from subprocess is caught and re-raised as FFmpegError."""
    with pytest.raises(FFmpegError) as exc_info:
        burn_subtitles(tmp_path / "in.mp4", tmp_path / "in.ass", tmp_path / "out.mp4")

    assert "FFmpeg failed" in str(exc_info.value)
    assert "Test error" in str(exc_info.value)


@patch("subprocess.run", side_effect=FileNotFoundError)
def test_burn_subtitles_ffmpeg_not_found_raises_ffmpeg_error(mock_run: MagicMock, tmp_path: Path) -> None:
    """Test that a FileNotFoundError is caught and re-raised as FFmpegError."""
    with pytest.raises(FFmpegError, match="ffmpeg command not found"):
        burn_subtitles(tmp_path / "in.mp4", tmp_path / "in.ass", tmp_path / "out.mp4")


@patch("subprocess.run")
@patch("pathlib.Path.resolve")
@patch("sys.platform", "win32")
def test_burn_subtitles_escapes_windows_path_colon(
    mock_resolve: MagicMock, mock_run: MagicMock, tmp_path: Path
) -> None:
    """Test that the colon in a Windows drive letter is correctly escaped for the ffmpeg filter."""
    video_in = tmp_path / "in.mp4"
    subs_in = tmp_path / "in.ass"
    video_out = tmp_path / "out.mp4"

    # Simulate a resolved Windows path
    mock_resolve.return_value = Path("C:\\Users\\test\\sub.ass")

    burn_subtitles(video_in, subs_in, video_out)

    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    command = args[0]
    filter_string = command[5]

    # The key assertion: C\: and \\
    assert "subtitles=filename='C\\:\\\\Users\\\\test\\\\sub.ass'" in filter_string
