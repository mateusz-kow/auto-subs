import sys
from importlib import reload
from unittest.mock import patch

import pytest

import autosubs.cli.main


def test_main_shim_without_typer(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the CLI entry point handles missing 'typer' dependency gracefully.

    This test mocks the absence of the 'typer' module, reloads the main CLI module,
    and verifies that the 'app' object becomes a shim function that prints an error
    message and exits, rather than crashing on import.
    """
    with patch.dict(sys.modules, {"typer": None}):
        reload(autosubs.cli.main)

        assert callable(autosubs.cli.main.app)
        assert not hasattr(autosubs.cli.main.app, "command")

        with pytest.raises(SystemExit) as exc_info:
            autosubs.cli.main.app()

        # Verify exit code and error message.
        assert exc_info.value.code == 1
        _, err = capsys.readouterr()
        assert "requires the optional 'cli' dependencies" in err
        assert "pip install 'auto-subs[cli]'" in err

    # Cleanup: Reload the module again without the mock to restore the normal
    # Typer application state. This is crucial to prevent side effects in other tests.
    reload(autosubs.cli.main)
    assert hasattr(autosubs.cli.main.app, "command")
