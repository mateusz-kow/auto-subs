"""Text processing utilities for professional subtitle segmentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autosubs.models.subtitles import SubtitleWord

# Professional Linguistic Hierarchy for splitting preference.
LINGUISTIC_WEIGHTS = {
    ".": -150.0,  # Sentence boundary (Optimal split)
    "!": -150.0,
    "?": -150.0,
    ":": -80.0,  # Clause boundary
    ";": -80.0,
    ",": -60.0,  # Phrase boundary
    "-": -30.0,  # Hyphenated break
}


def _calculate_cost(
    words: list[SubtitleWord],
    i: int,
    j: int,
    char_limit: int,
    target_cps: float = 15.0,
) -> float:
    """Calculate the cost of creating a segment from words[i:j+1].

    Balances character length, reading speed (CPS), punctuation, and temporal silence.
    """
    line_words = words[i : j + 1]
    line_text = " ".join(w.text for w in line_words)
    char_count = len(line_text)

    # 1. HARD MAXIMUM CONSTRAINT
    if char_count > char_limit:
        return float("inf")

    # 2. Base Cost
    # Fragmentation penalty to prevent unnecessary single-word segments.
    cost = 20.0

    # 3. Readability: Characters Per Second (CPS)
    # Penalize heavily if the text is moving too fast for human reading.
    duration = line_words[-1].end - line_words[0].start
    if duration > 0:
        cps = char_count / duration
        if cps > 21.0:  # Industry hard limit for reading comfort
            return float("inf")
        if cps > target_cps:
            cost += (cps - target_cps) ** 2 * 10.0

    # 4. Linguistic Anchoring
    last_word = line_words[-1].text.strip()
    if last_word:
        # Match the last char against weights; penalize "bad" breaks (no punctuation)
        penalty = LINGUISTIC_WEIGHTS.get(last_word[-1], 25.0)
        cost += penalty

    # 5. Temporal Anchoring (Silence)
    if j < len(words) - 1:
        gap = words[j + 1].start - words[j].end
        if gap > 0.4:
            # Major reward for splitting during natural pauses in speech.
            cost -= min(gap, 2.0) * 100.0
        elif gap < 0.1:
            # "Flicker" penalty: avoid splitting if the next word is temporally too close.
            cost += 40.0

    return cost


def partition_words_optimal(
    words: list[SubtitleWord],
    char_limit: int = 80,
    target_cps: float = 15.0,
) -> list[list[SubtitleWord]]:
    """Partition words into segments using Dynamic Programming to find global optima."""
    if not words:
        return []

    n = len(words)
    dp = [0.0] * (n + 1)
    breaks = [0] * (n + 1)

    for i in range(n - 1, -1, -1):
        min_total_cost = float("inf")
        best_j = i + 1

        for j in range(i, n):
            cost = _calculate_cost(words, i, j, char_limit, target_cps)

            if cost == float("inf"):
                break

            total_cost = cost + dp[j + 1]
            if total_cost < min_total_cost:
                min_total_cost = total_cost
                best_j = j + 1

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
