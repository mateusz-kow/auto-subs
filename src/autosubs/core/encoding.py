"""Core module for file encoding detection and reading."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

try:
    from charset_normalizer import from_bytes

    _HAS_CHARSET_NORMALIZER = True
except ImportError:
    _HAS_CHARSET_NORMALIZER = False

    if TYPE_CHECKING:

        def from_bytes(byte_str: bytes, **kwargs: object) -> object:  # type: ignore[misc]
            """Dummy typing function for when the library is not installed."""
            pass


def detect_file_encoding(file_path: Path, file_bytes: bytes) -> tuple[str, float | None]:
    """Detect the encoding of a file using charset-normalizer.

    Args:
        file_path: The path to the file (used for logging context).
        file_bytes: The raw bytes of the file.

    Returns:
        A tuple containing the detected encoding name and the confidence score (0.0-1.0).
        If charset-normalizer is not installed, returns ("latin-1", None).
    """
    if not _HAS_CHARSET_NORMALIZER:
        logger.debug(f"charset-normalizer not found. Falling back to latin-1 for: {file_path}")
        return "latin-1", None

    logger.debug(f"Attempting to detect encoding for: {file_path}")
    matches = from_bytes(file_bytes)
    best_match = matches.best()

    if best_match is None:
        logger.warning(f"Encoding detection yielded no matches for: {file_path}")
        return "utf-8", 0.0

    # charset-normalizer uses 'chaos' to indicate messiness. Confidence is roughly 1 - chaos.
    # While it provides 'coherence', 1 - chaos is the standard 'confidence' metric used in its detect() wrapper.
    confidence = 1.0 - getattr(best_match, "chaos", 1.0)
    logger.debug(f"Detected encoding '{best_match.encoding}' with confidence {confidence:.2f} for: {file_path}")
    return best_match.encoding, confidence


def read_with_encoding_detection(file_path: Path, explicit_encoding: str | None) -> str:
    """Read file content with automatic encoding detection fallback.

    1. Uses `explicit_encoding` if provided.
    2. Tries 'utf-8' strict.
    3. Falls back to `detect_file_encoding` using charset-normalizer.

    Args:
        file_path: Path to the file to read.
        explicit_encoding: Specific encoding to use, or None to auto-detect.

    Returns:
        The decoded string content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If UTF-8 fails and charset-normalizer is not installed.
        ValueError: If detected encoding confidence is below threshold (0.6).
        UnicodeDecodeError: If decoding fails with the final selected encoding.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if explicit_encoding:
        logger.debug(f"Reading {file_path} with explicit encoding: {explicit_encoding}")
        return file_path.read_text(encoding=explicit_encoding)

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.info(f"UTF-8 decode failed for {file_path}. Falling back to encoding detection.")

    if not _HAS_CHARSET_NORMALIZER:
        raise ImportError(
            f"UTF-8 decoding failed for {file_path} and 'charset-normalizer' is not installed. "
            "To enable automatic encoding detection, install the encoding extra: "
            "pip install 'auto-subs[encoding]'"
        )

    file_bytes = file_path.read_bytes()
    detected_encoding, confidence = detect_file_encoding(file_path, file_bytes)

    if confidence is not None and confidence < 0.6:
        raise ValueError(
            f"Encoding detection failed for {file_path}. "
            f"Detected '{detected_encoding}' with low confidence ({confidence:.2f} < 0.6)."
        )

    logger.info(f"Reading {file_path} using detected encoding: {detected_encoding}")
    return file_bytes.decode(detected_encoding)
