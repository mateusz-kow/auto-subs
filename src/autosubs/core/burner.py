"""Core module for burning subtitles into video files."""

import subprocess
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)


class FFmpegError(Exception):
    """Custom exception for FFmpeg command failures."""


def burn_subtitles(video_input: Path, subtitle_file: Path, video_output: Path) -> None:
    """Burns subtitles into a video file using FFmpeg.

    Args:
        video_input: Path to the source video file.
        subtitle_file: Path to the subtitle file to burn.
        video_output: Path to save the output video file.

    Raises:
        FFmpegError: If the ffmpeg command fails.
    """
    # FFmpeg's filter syntax for subtitles is notoriously tricky, especially on Windows.
    # The most robust method is to use the `filename` option explicitly.
    # 1. Get the absolute path to ensure no relative path issues.
    # 2. Escape backslashes for the filter string.
    # 3. Escape the colon in the drive letter for Windows.
    subtitle_path_str = str(subtitle_file.resolve()).replace("\\", "\\\\")
    if ":" in subtitle_path_str:
        subtitle_path_str = subtitle_path_str.replace(":", "\\:")

    filter_string = f"subtitles=filename='{subtitle_path_str}'"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_input),
        "-vf",
        filter_string,
        "-c:a",
        "copy",
        str(video_output),
    ]

    logger.debug(f"Executing FFmpeg command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        logger.debug(f"FFmpeg stdout: {result.stdout}")
        logger.info(f"Successfully burned subtitles into {video_output}")
    except subprocess.CalledProcessError as e:
        error_message = (
            f"FFmpeg failed with exit code {e.returncode}.\nCommand: {' '.join(command)}\nStderr: {e.stderr}"
        )
        logger.error(error_message)
        raise FFmpegError(error_message) from e
    except FileNotFoundError as e:
        # This is a fallback, but check_ffmpeg_installed should prevent this.
        raise FFmpegError("ffmpeg command not found. Please ensure it is installed and in your PATH.") from e
