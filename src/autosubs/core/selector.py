"""Selection system for filtering subtitle segments based on metadata criteria."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autosubs.models.subtitles.ass import AssSubtitleSegment


class LineSelector:
    """Filters subtitle segments based on metadata criteria.

    This class provides methods to filter AssSubtitleSegment objects based on
    various criteria like actor name, style name, and text patterns.

    Example:
        >>> selector = LineSelector()
        >>> filtered = selector.by_actor(segments, "Singer")
        >>> filtered = selector.by_style(segments, "Karaoke")
        >>> filtered = selector.by_text_regex(segments, r"^Hello")
    """

    @staticmethod
    def by_actor(
        segments: list[AssSubtitleSegment],
        actor: str,
        case_sensitive: bool = False,
    ) -> list[AssSubtitleSegment]:
        """Filters segments by actor name.

        Args:
            segments: List of subtitle segments to filter.
            actor: Actor name to match.
            case_sensitive: Whether to perform case-sensitive matching.

        Returns:
            List of segments where actor_name matches the specified actor.
        """
        if case_sensitive:
            return [seg for seg in segments if seg.actor_name == actor]
        else:
            actor_lower = actor.lower()
            return [seg for seg in segments if seg.actor_name.lower() == actor_lower]

    @staticmethod
    def by_style(
        segments: list[AssSubtitleSegment],
        style: str,
        case_sensitive: bool = False,
    ) -> list[AssSubtitleSegment]:
        """Filters segments by style name.

        Args:
            segments: List of subtitle segments to filter.
            style: Style name to match.
            case_sensitive: Whether to perform case-sensitive matching.

        Returns:
            List of segments where style_name matches the specified style.
        """
        if case_sensitive:
            return [seg for seg in segments if seg.style_name == style]
        else:
            style_lower = style.lower()
            return [seg for seg in segments if seg.style_name.lower() == style_lower]

    @staticmethod
    def by_text_regex(
        segments: list[AssSubtitleSegment],
        pattern: str | re.Pattern[str],
    ) -> list[AssSubtitleSegment]:
        """Filters segments by text content matching a regex pattern.

        Args:
            segments: List of subtitle segments to filter.
            pattern: Regex pattern to match against segment text.

        Returns:
            List of segments where text matches the pattern.
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        return [seg for seg in segments if pattern.search(seg.text)]

    @staticmethod
    def by_layer(
        segments: list[AssSubtitleSegment],
        layer: int,
    ) -> list[AssSubtitleSegment]:
        """Filters segments by layer number.

        Args:
            segments: List of subtitle segments to filter.
            layer: Layer number to match.

        Returns:
            List of segments with the specified layer.
        """
        return [seg for seg in segments if seg.layer == layer]

    @staticmethod
    def by_effect(
        segments: list[AssSubtitleSegment],
        effect: str,
        case_sensitive: bool = False,
    ) -> list[AssSubtitleSegment]:
        """Filters segments by effect field.

        Args:
            segments: List of subtitle segments to filter.
            effect: Effect name to match.
            case_sensitive: Whether to perform case-sensitive matching.

        Returns:
            List of segments where effect field matches.
        """
        if case_sensitive:
            return [seg for seg in segments if seg.effect == effect]
        else:
            effect_lower = effect.lower()
            return [seg for seg in segments if seg.effect.lower() == effect_lower]

    @staticmethod
    def by_time_range(
        segments: list[AssSubtitleSegment],
        start: float | None = None,
        end: float | None = None,
    ) -> list[AssSubtitleSegment]:
        """Filters segments by time range.

        Args:
            segments: List of subtitle segments to filter.
            start: Minimum start time (inclusive). None means no lower bound.
            end: Maximum end time (inclusive). None means no upper bound.

        Returns:
            List of segments within the specified time range.
        """
        result = segments
        if start is not None:
            result = [seg for seg in result if seg.start >= start]
        if end is not None:
            result = [seg for seg in result if seg.end <= end]
        return result

    @staticmethod
    def by_custom(
        segments: list[AssSubtitleSegment],
        predicate: Callable[[AssSubtitleSegment], bool],
    ) -> list[AssSubtitleSegment]:
        """Filters segments using a custom predicate function.

        Args:
            segments: List of subtitle segments to filter.
            predicate: Function that takes a segment and returns True to include it.

        Returns:
            List of segments for which predicate returns True.
        """
        return [seg for seg in segments if predicate(seg)]

    @staticmethod
    def combine_and(
        *filters: list[AssSubtitleSegment],
    ) -> list[AssSubtitleSegment]:
        """Combines multiple filter results using AND logic (intersection).

        Args:
            *filters: Multiple filter result lists to combine.

        Returns:
            List of segments present in all filter results.
        """
        if not filters:
            return []

        # Use id() for comparison since segments are not hashable
        result_ids = {id(seg) for seg in filters[0]}
        for filter_result in filters[1:]:
            result_ids &= {id(seg) for seg in filter_result}

        # Maintain original order from first filter
        return [seg for seg in filters[0] if id(seg) in result_ids]

    @staticmethod
    def combine_or(
        *filters: list[AssSubtitleSegment],
    ) -> list[AssSubtitleSegment]:
        """Combines multiple filter results using OR logic (union).

        Args:
            *filters: Multiple filter result lists to combine.

        Returns:
            List of unique segments present in any filter result.
        """
        seen_ids = set()
        result = []
        for filter_result in filters:
            for seg in filter_result:
                seg_id = id(seg)
                if seg_id not in seen_ids:
                    seen_ids.add(seg_id)
                    result.append(seg)
        return result
