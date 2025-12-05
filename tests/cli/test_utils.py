from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from _pytest.capture import CaptureFixture
from typer import Exit

from autosubs.cli.utils import (
    PathProcessor,
    SupportedExtension,
    check_ffmpeg_installed,
    determine_output_format,
    handle_burn_operation,
)
from autosubs.core.burner import FFmpegError
from autosubs.models.formats import SubtitleFormat


def test_path_processor_single_file(tmp_path: Path) -> None:
    """Test processing a single valid file."""
    in_file = tmp_path / "test.mp4"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, in_file.with_suffix(""))


def test_path_processor_single_file_with_output(tmp_path: Path) -> None:
    """Test processing a single file with a specified output path."""
    in_file = tmp_path / "test.mp4"
    out_file = tmp_path / "output.srt"
    in_file.touch()
    processor = PathProcessor(in_file, out_file, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, out_file.with_suffix(""))


def test_path_processor_unsupported_file_type(tmp_path: Path) -> None:
    """Test that an unsupported file type raises an Exit exception."""
    in_file = tmp_path / "test.txt"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_directory(tmp_path: Path) -> None:
    """Test processing a directory of files."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    (in_dir / "test1.json").touch()
    (in_dir / "test2.json").touch()
    (in_dir / "ignored.txt").touch()

    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 2
    assert results[0] == (in_dir / "test1.json", in_dir / "test1")
    assert results[1] == (in_dir / "test2.json", in_dir / "test2")


def test_path_processor_directory_with_output_dir(tmp_path: Path) -> None:
    """Test processing a directory with a specified output directory."""
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "test1.json").touch()

    processor = PathProcessor(in_dir, out_dir, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_dir / "test1.json", out_dir / "test1")


def test_path_processor_empty_directory(tmp_path: Path) -> None:
    """Test that an empty directory raises an Exit exception."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_input_dir_output_file_error(tmp_path: Path) -> None:
    """Test that input dir with output file raises an Exit exception."""
    in_dir = tmp_path / "input"
    out_file = tmp_path / "output.txt"
    in_dir.mkdir()
    out_file.touch()

    with pytest.raises(Exit):
        PathProcessor(in_dir, out_file, SupportedExtension.JSON)


def test_determine_output_format_explicit_option_wins() -> None:
    """Test that the explicit --format option has the highest priority."""
    result = determine_output_format(SubtitleFormat.SRT, Path("output.vtt"))
    assert result == SubtitleFormat.SRT


def test_determine_output_format_inferred_from_path() -> None:
    """Test that the format is correctly inferred from the output path extension."""
    result = determine_output_format(None, Path("video.ass"))
    assert result == SubtitleFormat.ASS


def test_determine_output_format_fallback_to_default(
    capsys: CaptureFixture[str],
) -> None:
    """Test that the function falls back to the default when no format can be determined."""
    result1 = determine_output_format(None, None, default=SubtitleFormat.SRT)
    assert result1 == SubtitleFormat.SRT
    assert "Defaulting to SRT" in capsys.readouterr().out

    # .txt is now recognized as MPL2, so it won't default to SRT
    result2 = determine_output_format(None, Path("output.txt"), default=SubtitleFormat.SRT)
    assert result2 == SubtitleFormat.MPL2


@patch("shutil.which", return_value="/path/to/ffmpeg")
def test_check_ffmpeg_installed_success(mock_which: MagicMock) -> None:
    """Test that no error is raised when ffmpeg is found."""
    try:
        check_ffmpeg_installed()
    except Exit:
        pytest.fail("check_ffmpeg_installed raised Exit unexpectedly.")


@patch("shutil.which", return_value=None)
def test_check_ffmpeg_installed_failure(mock_which: MagicMock) -> None:
    """Test that Exit is raised when ffmpeg is not found."""
    with pytest.raises(Exit):
        check_ffmpeg_installed()


@patch("pathlib.Path.resolve")
@patch("tempfile.NamedTemporaryFile")
@patch(
    "autosubs.cli.utils.burn_subtitles",
    side_effect=Exception("A generic filesystem error"),
)
def test_handle_burn_operation_generic_exception(
    mock_burn_subtitles: MagicMock, mock_tempfile: MagicMock, mock_resolve: MagicMock
) -> None:
    """Test that a generic Exception in the burn process is caught and handled."""
    mock_tempfile.return_value.__enter__.return_value.name = "dummy_temp_file.srt"
    mock_resolve.return_value = Path("dummy_temp_file.srt")

    with pytest.raises(Exit) as exc_info:
        handle_burn_operation(
            video_input=Path("video.mp4"),
            video_output=Path("out.mp4"),
            subtitle_content="dummy",
            subtitle_format=SubtitleFormat.SRT,
            styling_options_used=False,
        )

    assert exc_info.value.exit_code == 1
    mock_burn_subtitles.assert_called_once()


@pytest.mark.parametrize("subtitle_format", [SubtitleFormat.SRT, SubtitleFormat.VTT])
@patch("autosubs.core.burner.burn_subtitles", side_effect=FFmpegError("ffmpeg failed"))
def test_handle_burn_operation_srt_vtt_styling_warning(
    mock_burn: MagicMock,
    subtitle_format: SubtitleFormat,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """Test that a warning is shown for styled SRT/VTT burns."""
    video_input = tmp_path / "video.mp4"
    video_output = tmp_path / "output.mp4"
    video_input.touch()
    video_output.parent.mkdir(parents=True, exist_ok=True)

    with pytest.raises(Exit):
        handle_burn_operation(
            video_input=video_input,
            video_output=video_output,
            subtitle_content="dummy",
            subtitle_format=subtitle_format,
            styling_options_used=True,
        )

    captured = capsys.readouterr()
    assert "Warning: Burning SRT/VTT ignores style config." in captured.out
