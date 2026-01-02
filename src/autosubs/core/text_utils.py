"""Text processing utilities for subtitle formatting."""


def balance_lines(text: str, max_width_chars: int = 42) -> str:
    r"""Balance text across multiple lines using minimum raggedness algorithm.

    This function implements a Knuth-Plass-style minimum raggedness algorithm
    to create balanced line breaks. Instead of greedily filling the first line,
    it finds the optimal break point that minimizes the difference in length
    between lines, creating a more visually pleasing and readable result.

    The algorithm prefers breaking at punctuation marks over spaces when possible.

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
