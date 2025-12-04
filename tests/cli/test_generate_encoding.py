import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autosubs.cli.main import app

runner = CliRunner()


@pytest.fixture
def problematic_transcription(tmp_path: Path) -> Path:
    """Creates a transcription file with a character that fails in some encodings."""
    content = {
        "text": "Hello world 🤔.",
        "segments": [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "Hello world 🤔.",
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0},
                    {"word": "🤔.", "start": 1.0, "end": 2.0},
                ],
            }
        ],
    }
    json_file = tmp_path / "problem.json"
    json_file.write_text(json.dumps(content), encoding="utf-8")
    return json_file


@pytest.mark.parametrize(
    ("error_handler", "expected_output"),
    [
        ("replace", "1\n00:00:00,000 --> 00:00:02,000\nHello world ?.\n\n"),
        ("ignore", "1\n00:00:00,000 --> 00:00:02,000\nHello world .\n\n"),
    ],
)
def test_cli_generate_encoding_errors(
    problematic_transcription: Path,
    tmp_path: Path,
    error_handler: str,
    expected_output: str,
) -> None:
    """Tests that encoding errors are handled correctly based on the chosen strategy."""
    output_file = tmp_path / "output.srt"
    result = runner.invoke(
        app,
        [
            "generate",
            str(problematic_transcription),
            "--output",
            str(output_file),
            "--output-encoding",
            "latin-1",
            "--output-encoding-errors",
            error_handler,
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert "Successfully saved" in result.stdout
    content = output_file.read_text(encoding="latin-1")
    assert content == expected_output


def test_cli_generate_invalid_encoding(problematic_transcription: Path, tmp_path: Path) -> None:
    """Tests that using an invalid encoding name fails gracefully."""
    output_file = tmp_path / "output.srt"
    result = runner.invoke(
        app,
        [
            "generate",
            str(problematic_transcription),
            "--output",
            str(output_file),
            "--output-encoding",
            "invalid-encoding",
        ],
    )
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout
    assert "unknown encoding: invalid-encoding" in result.stdout


def test_cli_generate_invalid_error_handler(problematic_transcription: Path) -> None:
    """Tests that an invalid error handler value is rejected."""
    result = runner.invoke(
        app,
        [
            "generate",
            str(problematic_transcription),
            "--output-encoding-errors",
            "strict",
        ],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.stderr
    assert "'strict' is not one of 'replace', 'ignore'" in result.stderr
