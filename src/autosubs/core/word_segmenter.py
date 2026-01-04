"""Module responsible for orchestrating word streams into semantic subtitle events."""

from logging import getLogger

from autosubs.core.text_utils import partition_words_optimal
from autosubs.models.subtitles import SubtitleSegment, SubtitleWord

logger = getLogger(__name__)


def segment_words(
    words: list[SubtitleWord],
    char_limit: int = 80,
    target_cps: float = 15.0,
) -> list[SubtitleSegment]:
    """Orchestrates the word stream into semantic subtitle events.

    This uses a 'Renderer-First' approach, defining temporal boundaries
    while leaving visual line-wrapping to the player.
    """
    if not words:
        return []

    # Filter out empty noise or invalid timestamps
    valid_words = [w for w in words if w.text.strip() and w.end >= w.start]

    if not valid_words:
        return []

    logger.info("Starting global heuristic word segmentation...")

    # Dynamic Programming Optimization
    partitions = partition_words_optimal(
        valid_words,
        char_limit=char_limit,
        target_cps=target_cps,
    )

    return [SubtitleSegment(words=group) for group in partitions]
