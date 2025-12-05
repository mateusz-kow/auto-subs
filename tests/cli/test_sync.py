from pathlib import Path

import pytest
from typer.testing import CliRunner

from autosubs.cli.main import app
from autosubs.core.parser import parse_srt
from tests.utils import strip_ansi

runner = CliRunner()

# Content for a sample SRT file
SAMPLE_SRT_CONTENT = """1
00:00:10,000 --> 00:00:12,000
Hello world.

2
00:00:15,000 --> 00:00:17,500
This is a test.
"""


@pytest.fixture
def tmp_srt_file(tmp_path: Path) -> Path:
    """Creates a temporary SRT file for testing."""
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(SAMPLE_SRT_CONTENT, encoding="utf-8")
    return srt_file


def test_cli_sync_success(tmp_path: Path, tmp_srt_file: Path) -> None:
    """Test successful synchronization with valid arguments."""
    output_path = tmp_path / "synced.srt"
    result = runner.invoke(
        app,
        [
            "sync",
            str(tmp_srt_file),
            "--output",
            str(output_path),
            "--point",
            "10,20",  # old 10s -> new 20s
            "--point",
            "15,30",  # old 15s -> new 30s
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Successfully saved to:" in result.stdout
    assert output_path.exists()

    segments = parse_srt(output_path.read_text())
    assert len(segments) == 2
    assert segments[0].start == pytest.approx(20.0)
    assert segments[0].end == pytest.approx(24.0)
    assert segments[1].start == pytest.approx(30.0)
    assert segments[1].end == pytest.approx(35.0)


def test_cli_sync_default_output_name(tmp_srt_file: Path) -> None:
    """Test that the default output name is correct."""
    expected_output = tmp_srt_file.with_stem("test_synced")
    result = runner.invoke(
        app,
        [
            "sync",
            str(tmp_srt_file),
            "--point",
            "10,20",
            "--point",
            "15,30",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert expected_output.exists()


@pytest.mark.parametrize(
    "args, error_msg",
    [
        (
            ["--point", "1,2"],
            "Exactly two synchronization points required.",
        ),
        (
            ["--point", "1,2", "--point", "3,4", "--point", "5,6"],
            "Exactly two synchronization points required.",
        ),
        (
            ["--point", "1-2", "--point", "3,4"],
            # This triggers _parse_time first, causing BadParameter "Invalid time"
            "Invalid time: '1-2'",
        ),
        (
            ["--point", "a,b", "--point", "c,d"],
            "Invalid time: 'a'",
        ),
        (
            ["--point", "10,20", "--point", "10,30"],
            "The two 'old_time' values cannot be the same.",
        ),
    ],
)
def test_cli_sync_invalid_points(tmp_srt_file: Path, args: list[str], error_msg: str) -> None:
    """Test various invalid --point argument scenarios."""
    result = runner.invoke(app, ["sync", str(tmp_srt_file), *args])
    assert result.exit_code != 0
    assert error_msg in strip_ansi(result.output)


def test_cli_sync_input_file_not_found() -> None:
    """Test that the command fails if the input file doesn't exist."""
    result = runner.invoke(app, ["sync", "non_existent.srt", "--point", "1,2", "--point", "3,4"])
    assert result.exit_code != 0
    assert "does not exist" in strip_ansi(result.output)
