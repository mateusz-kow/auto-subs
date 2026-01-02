"""Utilities for parsing and working with ASS karaoke timing tags."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import regex

if TYPE_CHECKING:
    from autosubs.models.subtitles.ass import AssSubtitleSegment


@dataclass(frozen=True)
class Syllable:
    r"""Represents a single syllable with karaoke timing information.

    Attributes:
        text: The text content of the syllable.
        start: Start time in seconds relative to line start.
        duration: Duration of the syllable in centiseconds (as specified in ASS).
        duration_seconds: Duration of the syllable in seconds.
        tag_type: The karaoke tag type used (\\k, \\kf, \\ko, or \\K).
    """

    text: str
    start: float
    duration: int  # in centiseconds
    tag_type: str = "k"

    @property
    def duration_seconds(self) -> float:
        """Returns the duration in seconds."""
        return self.duration / 100.0

    @property
    def end(self) -> float:
        """Returns the end time in seconds relative to line start."""
        return self.start + self.duration_seconds


class KaraokeParser:
    r"""Parser for ASS karaoke timing tags.

    Supports the following karaoke tags:
    - \k<duration>: Basic karaoke timing
    - \kf<duration> or \K<duration>: Fill karaoke (sweeping highlight)
    - \ko<duration>: Outline karaoke (outline changes before fill)
    """

    # Match karaoke tags: \k, \kf, \ko, \K followed by optional duration
    KARAOKE_TAG_PATTERN = re.compile(r"\\(k[fo]?|K)(\d*)")

    @classmethod
    def parse_syllables(cls, text: str) -> list[Syllable]:
        r"""Extracts syllables from text containing karaoke tags.

        Args:
            text: Text with embedded ASS karaoke tags (e.g., "{\k50}hel{\k30}lo").

        Returns:
            List of Syllable objects with timing information.

        Example:
            >>> parser = KaraokeParser()
            >>> syllables = parser.parse_syllables("{\k50}Hel{\k30}lo {\k40}world")
            >>> len(syllables)
            3
            >>> syllables[0].text
            'Hel'
            >>> syllables[0].duration
            50
        """
        syllables: list[Syllable] = []
        current_time = 0.0

        # Remove newline tags
        cleaned_text = text.replace("\\N", " ").replace("\\n", " ")

        # Pattern to match override blocks and text
        # This captures {override blocks} and text between them
        pattern = r"(\{[^}]*\})|([^{}]+)"
        tokens = regex.findall(pattern, cleaned_text)

        pending_tag: tuple[str, int] | None = None

        for override_block, text_content in tokens:
            if override_block:
                # Extract karaoke tag if present
                match = cls.KARAOKE_TAG_PATTERN.search(override_block)
                if match:
                    tag_type = match.group(1)
                    duration_str = match.group(2)
                    duration = int(duration_str) if duration_str else 0
                    pending_tag = (tag_type, duration)
            elif text_content:
                # This is text content
                if pending_tag:
                    tag_type, duration = pending_tag
                    syllables.append(
                        Syllable(
                            text=text_content,
                            start=current_time,
                            duration=duration,
                            tag_type=tag_type,
                        )
                    )
                    current_time += duration / 100.0
                    pending_tag = None
                elif text_content.strip():
                    # Text without a preceding karaoke tag
                    syllables.append(
                        Syllable(
                            text=text_content,
                            start=current_time,
                            duration=0,
                            tag_type="k",
                        )
                    )

        return syllables

    @classmethod
    def has_karaoke_tags(cls, text: str) -> bool:
        """Checks if text contains any karaoke timing tags.

        Args:
            text: Text to check for karaoke tags.

        Returns:
            True if text contains karaoke tags, False otherwise.
        """
        return bool(cls.KARAOKE_TAG_PATTERN.search(text))


def extract_syllables_from_segment(segment: AssSubtitleSegment) -> list[Syllable]:  # noqa: F821
    """Extracts syllables with absolute timing from an AssSubtitleSegment.

    This function parses karaoke tags from the segment text and converts
    relative timings to absolute timestamps.

    Args:
        segment: The subtitle segment to extract syllables from.

    Returns:
        List of Syllable objects. If no karaoke tags are found, returns
        an empty list.
    """
    # Reconstruct text with karaoke tags from words
    full_text_parts = []
    for word in segment.words:
        # Add any style tags that might contain karaoke tags
        for style_range in word.styles:
            tag_str = style_range.tag_block.to_ass_string()
            if tag_str and KaraokeParser.has_karaoke_tags(tag_str):
                full_text_parts.append(tag_str)
        full_text_parts.append(word.text)

    full_text = "".join(full_text_parts)

    if not KaraokeParser.has_karaoke_tags(full_text):
        return []

    # Parse syllables and adjust timing to be absolute
    syllables = KaraokeParser.parse_syllables(full_text)

    # Convert relative timing to absolute timing based on segment start
    result = []
    for syllable in syllables:
        result.append(
            Syllable(
                text=syllable.text,
                start=segment.start + syllable.start,
                duration=syllable.duration,
                tag_type=syllable.tag_type,
            )
        )

    return result
