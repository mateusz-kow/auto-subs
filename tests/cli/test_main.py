from typer.testing import CliRunner

from auto_subs import __version__
from auto_subs.cli import app

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
