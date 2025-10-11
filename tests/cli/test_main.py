import logging
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from auto_subs import __version__
from auto_subs.cli import app
from tests.utils import strip_ansi

runner = CliRunner()


def test_cli_version() -> None:
    """Test the --version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"auto-subs version: {__version__}" in result.stdout


def test_cli_file_not_found() -> None:
    """Test error handling for a non-existent input file."""
    env = {"TERM": "dumb", "NO_COLOR": "1"}
    result = runner.invoke(app, ["generate", "non_existent_file.json"], env=env)
    assert result.exit_code == 2

    assert "Invalid value" in result.stderr
    assert "non_existent_file.json" in result.stderr


def test_cli_quiet_and_verbose_error() -> None:
    """Test that using --quiet and --verbose together raises a BadParameter error."""
    result = runner.invoke(app, ["--quiet", "--verbose", "generate", "dummy.json"])
    assert result.exit_code == 2  # Typer's exit code for bad parameters

    stderr = strip_ansi(result.stderr)
    assert "Error" in stderr
    assert "--quiet and --verbose options cannot be used together" in stderr


@patch("logging.basicConfig")
def test_cli_logging_level_quiet(mock_basic_config: MagicMock) -> None:
    """Test that --quiet sets the logging level to WARNING."""
    runner.invoke(app, ["--quiet", "generate", "dummy.json"])
    # The first positional argument to basicConfig is 'level'
    args, kwargs = mock_basic_config.call_args
    assert kwargs["level"] == logging.WARNING


@patch("logging.basicConfig")
@pytest.mark.parametrize("verbose_flag", ["-v", "-vv", "--verbose"])
def test_cli_logging_level_verbose(mock_basic_config: MagicMock, verbose_flag: str) -> None:
    """Test that -v or --verbose sets the logging level to DEBUG."""
    runner.invoke(app, [verbose_flag, "generate", "dummy.json"])
    args, kwargs = mock_basic_config.call_args
    assert kwargs["level"] == logging.DEBUG
