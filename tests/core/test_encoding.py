import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autosubs.core import encoding
from autosubs.core.encoding import detect_file_encoding, read_with_encoding_detection


@pytest.fixture
def non_utf8_file(tmp_path: Path) -> Path:
    """Create a temporary file encoded in Windows-1252 (contains characters invalid in UTF-8)."""
    file_path = tmp_path / "test_win1252.txt"
    # 'é' encoded in latin-1/cp1252 is b'\xe9', which is invalid as a start byte in UTF-8
    content_bytes = b"H\xe9llo World"
    file_path.write_bytes(content_bytes)
    return file_path


@pytest.fixture
def mock_match() -> MagicMock:
    """Create a mock match object behaving like charset_normalizer's CharsetMatch."""
    match = MagicMock()
    match.encoding = "cp1252"
    # Confidence is calculated as 1.0 - chaos.
    # To get high confidence (e.g. 1.0), chaos must be 0.0.
    match.chaos = 0.0
    return match


@pytest.fixture
def mock_from_bytes(mock_match: MagicMock) -> MagicMock:
    """Create a mock Matches object behaving like charset_normalizer.from_bytes result."""
    matches = MagicMock()
    matches.best.return_value = mock_match
    return matches


# --- detect_file_encoding tests ---


def test_detect_file_encoding_success(mock_from_bytes: MagicMock) -> None:
    """Test successful detection when charset-normalizer finds a match."""
    # Ensure the flag is True for this test
    with (
        patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", True),
        patch("autosubs.core.encoding.from_bytes", return_value=mock_from_bytes),
    ):
        enc, conf = detect_file_encoding(Path("dummy"), b"dummy")

    assert enc == "cp1252"
    assert conf == 1.0  # 1.0 - 0.0 chaos


def test_detect_file_encoding_no_matches() -> None:
    """Test behavior when charset-normalizer returns no matches."""
    empty_matches = MagicMock()
    empty_matches.best.return_value = None

    with (
        patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", True),
        patch("autosubs.core.encoding.from_bytes", return_value=empty_matches),
    ):
        enc, conf = detect_file_encoding(Path("dummy"), b"dummy")

    assert enc == "utf-8"
    assert conf == 0.0


def test_detect_file_encoding_library_missing(caplog: pytest.LogCaptureFixture) -> None:
    """Test fallback behavior when charset-normalizer is not installed."""
    with patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", False), caplog.at_level(logging.DEBUG):
        enc, conf = detect_file_encoding(Path("dummy.txt"), b"dummy")

    assert enc == "latin-1"
    assert conf is None
    assert "charset-normalizer not found" in caplog.text


# --- read_with_encoding_detection tests ---


def test_read_file_not_found() -> None:
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        read_with_encoding_detection(Path("non_existent.txt"), None)


def test_read_explicit_encoding(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test reading with a specifically provided encoding."""
    file_path = tmp_path / "explicit.txt"
    file_path.write_text("Hello", encoding="utf-8")

    with caplog.at_level(logging.DEBUG):
        content = read_with_encoding_detection(file_path, explicit_encoding="utf-8")

    assert content == "Hello"
    assert "explicit encoding: utf-8" in caplog.text


def test_read_utf8_default(tmp_path: Path) -> None:
    """Test standard UTF-8 reading (happy path, no detection needed)."""
    file_path = tmp_path / "utf8.txt"
    file_path.write_text("Hello 🌍", encoding="utf-8")

    content = read_with_encoding_detection(file_path, None)
    assert content == "Hello 🌍"


def test_read_fallback_success(
    non_utf8_file: Path,
    mock_from_bytes: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test successful fallback to detection when UTF-8 fails."""
    # The file contains b"H\xe9llo World" (Windows-1252)

    with (
        patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", True),
        patch("autosubs.core.encoding.from_bytes", return_value=mock_from_bytes),
        caplog.at_level(logging.INFO),
    ):
        content = read_with_encoding_detection(non_utf8_file, None)

    assert content == "Héllo World"
    assert "UTF-8 decode failed" in caplog.text
    assert "Reading" in caplog.text
    assert "detected encoding: cp1252" in caplog.text


def test_read_fallback_low_confidence(
    non_utf8_file: Path,
    mock_match: MagicMock,
) -> None:
    """Test that ValueError is raised if detection confidence is too low."""
    # Set chaos high -> confidence low (e.g. 1.0 - 0.5 = 0.5)
    mock_match.chaos = 0.5
    matches = MagicMock()
    matches.best.return_value = mock_match

    with (
        patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", True),
        patch("autosubs.core.encoding.from_bytes", return_value=matches),
        pytest.raises(ValueError, match="low confidence"),
    ):
        read_with_encoding_detection(non_utf8_file, None)


def test_read_fallback_library_missing(non_utf8_file: Path) -> None:
    """Test that ImportError is raised when decoding fails and lib is missing."""
    # Simulate library missing
    with patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", False), pytest.raises(ImportError) as exc_info:
        read_with_encoding_detection(non_utf8_file, None)

    msg = str(exc_info.value)
    assert "charset-normalizer" in msg
    assert "pip install 'auto-subs[encoding]'" in msg


def test_read_fallback_unicode_decode_error_after_detection(
    non_utf8_file: Path,
    mock_from_bytes: MagicMock,
) -> None:
    """Test that if the detected encoding is wrong and fails to decode, the error propagates."""
    # Scenario: Detection says it's "ascii", but the file has bytes > 127
    mock_from_bytes.best.return_value.encoding = "ascii"
    mock_from_bytes.best.return_value.chaos = 0.0

    with (
        patch("autosubs.core.encoding._HAS_CHARSET_NORMALIZER", True),
        patch("autosubs.core.encoding.from_bytes", return_value=mock_from_bytes),
        pytest.raises(UnicodeDecodeError),
    ):
        read_with_encoding_detection(non_utf8_file, None)


def test_import_guard_logic() -> None:
    """
    Test the top-level import logic by reloading the module with imports mocked.
    This ensures we cover the `except ImportError` block at the module level.
    """
    import sys
    from importlib import reload

    # Simulate import error for charset_normalizer
    with patch.dict(sys.modules, {"charset_normalizer": None}):
        reload(encoding)
        assert encoding._HAS_CHARSET_NORMALIZER is False

    # Restore module state
    reload(encoding)
    # Depending on environment, it might be True or False, but we just want to ensure
    # the reload works and restores sanity for other tests if needed.
