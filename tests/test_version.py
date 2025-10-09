import auto_subs


def test_package_is_importable() -> None:
    """Verify that the auto_subs package can be imported."""
    assert auto_subs is not None


def test_version_is_present() -> None:
    """Verify that the __version__ attribute is set and matches the expected version."""
    assert hasattr(auto_subs, "__version__")
    assert auto_subs.__version__ == "0.1.0"
