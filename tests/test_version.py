"""A simple test to ensure the package is importable and has a version."""

import auto_subs


def test_package_is_importable() -> None:
    """Verify that the auto_subs package can be imported."""
    assert auto_subs is not None


def test_version_is_present() -> None:
    """Verify that the __version__ attribute is set."""
    assert hasattr(auto_subs, "__version__")
    assert isinstance(auto_subs.__version__, str)
    # Możesz dodać bardziej rygorystyczne sprawdzenie formatu wersji, np. z wyrażeniem regularnym
    assert len(auto_subs.__version__) > 0
