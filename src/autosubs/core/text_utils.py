"""Text processing utilities for deterministic subtitle segmentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autosubs.models.subtitles import SubtitleWord

# Punctuation hierarchy for splitting preference.
PUNCTUATION_BONUSES = {
    ".": -60.0,
    "!": -60.0,
    "?": -60.0,
    ":": -30.0,
    ";": -30.0,
    ",": -25.0,
    "-": -15.0,
}


def _calculate_cost(
    words: list[SubtitleWord],
    i: int,
    j: int,
    max_chars: int,
) -> float:
    """Calculate the cost of creating a segment from words[i:j+1].

    The cost function balances character length, speaking rate (CPS),
    punctuation, and temporal silence gaps.
    """
    line_words = words[i : j + 1]
    line_text = " ".join(w.text for w in line_words)
    char_count = len(line_text)

    # Handle oversized segments
    if char_count > max_chars:
        # If it's a single word that exceeds the limit, allow it with a high penalty
        # to prevent DP failure, otherwise return infinity.
        if i == j:
            return 10000.0 + (char_count - max_chars) * 10.0
        return float("inf")

    # 1. Base cost for creating a segment to prevent unnecessary fragmentation.
    cost = 15.0

    # 2. Length Penalty: Prefer longer lines up to the limit to avoid flickering.
    cost += (max_chars - char_count) * 0.5

    # 3. Temporal Penalty: Characters Per Second (CPS).
    # Typical limit is ~20 CPS. Penalize if reading speed is too high.
    duration = line_words[-1].end - line_words[0].start
    if duration > 0:
        cps = char_count / duration
        if cps > 20:
            cost += (cps - 20) * 50.0

    # 4. Punctuation Bonus (Negative Cost).
    last_word = line_words[-1].text.strip()
    if last_word:
        last_char = last_word[-1]
        cost += PUNCTUATION_BONUSES.get(last_char, 0.0)

    # 5. Silence Bonus (Negative Cost) and Flicker Penalty.
    if j < len(words) - 1:
        silence_gap = words[j + 1].start - words[j].end
        if silence_gap > 0.1:
            # Reward splitting at clear pauses.
            cost -= min(silence_gap, 1.0) * 100.0
        elif 0.0 < silence_gap <= 0.1:
            # Penalize splitting at tiny gaps to prevent visual flickering.
            cost += (0.1 - silence_gap) * 100.0

    return cost


def partition_words_optimal(
    words: list[SubtitleWord],
    max_chars: int = 42,
) -> list[list[SubtitleWord]]:
    """Partition words into segments using Dynamic Programming.

    Minimizes the cumulative cost across all generated segments to find the
    globally optimal subtitle timing and layout.
    """
    if not words:
        return []

    n = len(words)
    dp = [0.0] * (n + 1)
    breaks = [0] * (n + 1)

    for i in range(n - 1, -1, -1):
        min_total_cost = float("inf")
        best_j = i + 1

        for j in range(i, n):
            cost = _calculate_cost(words, i, j, max_chars)

            if cost == float("inf"):
                break

            total_cost = cost + dp[j + 1]
            if total_cost < min_total_cost:
                min_total_cost = total_cost
                best_j = j + 1

        # If it's impossible to fit even the single next word (handled by _calculate_cost),
        # force a single-word break to ensure algorithm termination.
        if min_total_cost == float("inf"):
            dp[i] = 1e6
            best_j = i + 1
        else:
            dp[i] = min_total_cost

        breaks[i] = best_j

    result = []
    curr = 0
    while curr < n:
        next_break = breaks[curr]
        result.append(words[curr:next_break])
        curr = next_break

    return result


def balance_lines_with_timing(
    words: list[SubtitleWord],
    max_chars: int = 42,
) -> list[list[SubtitleWord]]:
    """Partition words into segments using temporal and visual heuristics."""
    return partition_words_optimal(words, max_chars=max_chars)
