from pathlib import Path

import pytest
from typer.testing import CliRunner

from autosubs.cli.main import app

runner = CliRunner()


@pytest.fixture
def problematic_srt_file(tmp_path: Path) -> Path:
    """Creates an SRT file with a character that fails in some encodings."""
    content = "1\n00:00:00,000 --> 00:00:02,000\nHello world 🤔.\n\n"
    srt_file = tmp_path / "problem.srt"
    srt_file.write_text(content, encoding="utf-8")
    return srt_file


@pytest.mark.parametrize(
    ("error_handler", "expected_output"),
    [
        ("replace", "1\n00:00:00,000 --> 00:00:02,000\nHello world ?.\n\n"),
        ("ignore", "1\n00:00:00,000 --> 00:00:02,000\nHello world .\n\n"),
    ],
)
def test_cli_convert_encoding_errors(
    problematic_srt_file: Path,
    tmp_path: Path,
    error_handler: str,
    expected_output: str,
) -> None:
    """Tests that encoding errors are handled correctly during conversion."""
    output_file = tmp_path / "output.srt"
    result = runner.invoke(
        app,
        [
            "convert",
            str(problematic_srt_file),
            "--output",
            str(output_file),
            "--output-encoding",
            "latin-1",
            "--output-encoding-errors",
            error_handler,
        ],
    )
    assert result.exit_code == 0, result.stderr or result.stdout
    assert "Successfully saved" in result.stdout
    content = output_file.read_text(encoding="latin-1")
    assert content == expected_output


def test_cli_convert_invalid_encoding(problematic_srt_file: Path, tmp_path: Path) -> None:
    """Tests that converting with an invalid encoding name fails gracefully."""
    output_file = tmp_path / "output.srt"
    result = runner.invoke(
        app,
        [
            "convert",
            str(problematic_srt_file),
            "--output",
            str(output_file),
            "--output-encoding",
            "invalid-encoding",
        ],
    )
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout
    assert "unknown encoding: invalid-encoding" in result.stdout


def test_cli_convert_invalid_error_handler(problematic_srt_file: Path) -> None:
    """Tests that an invalid error handler value is rejected."""
    result = runner.invoke(
        app,
        [
            "convert",
            str(problematic_srt_file),
            "--output-encoding-errors",
            "invalid-handler",
        ],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.stdout
    assert "invalid-handler" in result.stdout
    assert "is not one of" in result.stdout


def test_cli_convert_encoding_strict_fails(
    problematic_srt_file: Path,
    tmp_path: Path,
) -> None:
    """Tests that the 'strict' error handler fails when an invalid character is present."""
    output_file = tmp_path / "output.srt"
    result = runner.invoke(
        app,
        [
            "convert",
            str(problematic_srt_file),
            "--output",
            str(output_file),
            "--output-encoding",
            "latin-1",
            "--output-encoding-errors",
            "strict",
        ],
    )
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout
    assert "codec can't encode character" in result.stdout
