"""Text processing utilities for subtitle formatting."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autosubs.models.subtitles import SubtitleWord


def _normalize_text(text: str) -> str:
    """Normalize text by removing existing line breaks.

    Args:
        text: The text to normalize.

    Returns:
        The normalized text with line breaks replaced by spaces.
    """
    return text.replace("\\N", " ").replace("\n", " ")


def _calculate_line_duration(words: list[SubtitleWord]) -> float:
    """Calculate the total duration of a line of words.

    Args:
        words: The words in the line.

    Returns:
        The duration in seconds, or 0 if no words.
    """
    if not words:
        return 0.0
    return words[-1].end - words[0].start


def _detect_silence_gap(word1: SubtitleWord, word2: SubtitleWord) -> float:
    """Detect the silence gap between two consecutive words.

    Args:
        word1: The first word.
        word2: The second word.

    Returns:
        The gap duration in seconds.
    """
    return word2.start - word1.end


def balance_lines_with_timing(
    words: list[SubtitleWord],
    max_width_chars: int = 42,
    char_weight: float = 1.0,
    duration_weight: float = 2.0,
    silence_bonus: float = -10.0,
    silence_threshold_ms: float = 200.0,
    punctuation_bonus: float = -5.0,
) -> list[list[SubtitleWord]]:
    """Balance words across multiple lines using temporal and visual cost function.

    This function implements a cost-minimization algorithm that considers:
    - Character balance: Minimizes difference in line lengths
    - Duration balance: Minimizes difference in speaking time
    - Silence gaps: Prefers breaking at natural pauses
    - Punctuation: Prefers breaking after punctuation marks

    Cost Formula: Cost = (char_diff * char_weight) + (duration_diff * duration_weight)
                        + (silence_bonus if gap > threshold) + (punctuation_bonus)

    Args:
        words: The list of SubtitleWord objects to balance.
        max_width_chars: Maximum characters per line (default: 42).
        char_weight: Weight for character balance in cost function (default: 1.0).
        duration_weight: Weight for duration balance in cost function (default: 2.0).
        silence_bonus: Bonus (negative cost) for breaking at silence gaps (default: -10.0).
        silence_threshold_ms: Minimum gap in milliseconds to apply silence bonus (default: 200).
        punctuation_bonus: Bonus for breaking after punctuation (default: -5.0).

    Returns:
        A list of lists, where each inner list represents a line of words.
        Returns [words] (single line) if text fits or cannot be split properly.
    """
    if not words:
        return [[]]

    # Check if all text fits on one line
    total_text = " ".join(word.text for word in words)
    if len(total_text) <= max_width_chars:
        return [words]

    if len(words) == 1:
        return [words]

    # Find the optimal break point
    best_break_idx = 0
    min_cost = float("inf")

    for i in range(1, len(words)):
        line1_words = words[:i]
        line2_words = words[i:]

        line1_text = " ".join(word.text for word in line1_words)
        line2_text = " ".join(word.text for word in line2_words)

        # Skip if either line exceeds max width
        if len(line1_text) > max_width_chars or len(line2_text) > max_width_chars:
            continue

        # Calculate character difference
        char_diff = abs(len(line1_text) - len(line2_text))

        # Calculate duration difference
        line1_duration = _calculate_line_duration(line1_words)
        line2_duration = _calculate_line_duration(line2_words)
        duration_diff = abs(line1_duration - line2_duration)

        # Base cost
        cost = (char_diff * char_weight) + (duration_diff * duration_weight)

        # Apply silence gap bonus
        silence_gap = _detect_silence_gap(line1_words[-1], line2_words[0])
        if silence_gap >= (silence_threshold_ms / 1000.0):
            cost += silence_bonus

        # Apply punctuation bonus
        last_word_text = line1_words[-1].text
        if last_word_text and last_word_text[-1] in ".,!?;:":
            cost += punctuation_bonus

        if cost < min_cost:
            min_cost = cost
            best_break_idx = i

    # If no valid break found, try middle fallback
    if best_break_idx == 0:
        mid_point = len(words) // 2
        for offset in range(len(words)):
            for idx in [mid_point + offset, mid_point - offset]:
                if 0 < idx < len(words):
                    line1_text = " ".join(word.text for word in words[:idx])
                    line2_text = " ".join(word.text for word in words[idx:])
                    if len(line1_text) <= max_width_chars and len(line2_text) <= max_width_chars:
                        best_break_idx = idx
                        break
            if best_break_idx != 0:
                break

    # If still no valid break, return as single line
    if best_break_idx == 0:
        return [words]

    return [words[:best_break_idx], words[best_break_idx:]]


def balance_lines(text: str, max_width_chars: int = 42) -> str:
    r"""Balance text across multiple lines using minimum raggedness algorithm.

    This is a text-only convenience function for backward compatibility.
    For timing-aware balancing, use balance_lines_with_timing() instead.

    Args:
        text: The text to balance across lines.
        max_width_chars: Maximum width in characters per line (default: 42).

    Returns:
        The text with balanced line breaks inserted using \N (ASS format newline).

    Examples:
        >>> balance_lines("The quick brown fox jumps over the lazy dog.")
        'The quick brown fox jumps\\Nover the lazy dog.'
        >>> balance_lines("Hello, world!")
        'Hello, world!'
    """
    # Normalize input to handle pre-existing line breaks
    text = _normalize_text(text)

    if not text or not text.strip():
        return text

    # If the text fits on a single line, no wrapping needed
    if len(text) <= max_width_chars:
        return text

    # Find all potential break points (spaces and punctuation)
    words = text.split()
    if len(words) <= 1:
        # Cannot break a single word
        return text

    # Find the optimal break point that minimizes raggedness
    # Raggedness is the difference in length between the two lines
    best_break_idx = 0
    min_raggedness = float("inf")

    # Try breaking at each word boundary
    for i in range(1, len(words)):
        # Line 1: words[0:i], Line 2: words[i:]
        line1_words = words[:i]
        line2_words = words[i:]

        line1 = " ".join(line1_words)
        line2 = " ".join(line2_words)

        # Skip if either line exceeds max width
        if len(line1) > max_width_chars or len(line2) > max_width_chars:
            continue

        # Calculate raggedness: difference in lengths
        raggedness = abs(len(line1) - len(line2))

        # Prefer breaks after punctuation marks
        # Check if the last word of line1 ends with punctuation
        punctuation_bonus = 0
        if line1_words and line1_words[-1] and line1_words[-1][-1] in ".,!?;:":
            punctuation_bonus = -5  # Lower raggedness score for punctuation breaks

        adjusted_raggedness = raggedness + punctuation_bonus

        if adjusted_raggedness < min_raggedness:
            min_raggedness = adjusted_raggedness
            best_break_idx = i

    # If no valid break point was found (all lines exceed max_width),
    # fall back to breaking near the middle
    if best_break_idx == 0:
        # Try to break as close to the middle as possible
        mid_point = len(words) // 2
        for offset in range(len(words)):
            # Try positions around the middle
            for idx in [mid_point + offset, mid_point - offset]:
                if 0 < idx < len(words):
                    line1 = " ".join(words[:idx])
                    line2 = " ".join(words[idx:])
                    if len(line1) <= max_width_chars and len(line2) <= max_width_chars:
                        best_break_idx = idx
                        break
            if best_break_idx != 0:
                break

    # If still no valid break (text cannot be balanced within max_width),
    # return original text
    if best_break_idx == 0:
        return text

    # Create the balanced result with \\N line break
    line1 = " ".join(words[:best_break_idx])
    line2 = " ".join(words[best_break_idx:])

    return f"{line1}\\N{line2}"
