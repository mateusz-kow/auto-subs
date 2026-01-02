"""Template engine for applying complex effects to subtitle segments."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from autosubs.core.karaoke import Syllable, extract_syllables_from_segment
from autosubs.models.subtitles.ass import AssSubtitles, AssSubtitleSegment


@dataclass
class EffectContext:
    """Context object passed to effect functions with segment/syllable data.

    This provides easy access to segment properties and syllable-level data
    for effect functions to use when generating transformed segments.

    Attributes:
        segment: The original subtitle segment being processed.
        index: The zero-based index of this segment in the subtitle list.
        syllables: List of syllables extracted from the segment (if any).
        line_start: Start time of the line in seconds.
        line_end: End time of the line in seconds.
        actor: Actor name from the segment.
        style: Style name from the segment.
        layer: Layer number from the segment.
        effect: Effect field from the segment.
    """

    segment: AssSubtitleSegment
    index: int
    syllables: list[Syllable] = field(default_factory=list)

    @property
    def line_start(self) -> float:
        """Returns the start time of the line."""
        return self.segment.start

    @property
    def line_end(self) -> float:
        """Returns the end time of the line."""
        return self.segment.end

    @property
    def actor(self) -> str:
        """Returns the actor name."""
        return self.segment.actor_name

    @property
    def style(self) -> str:
        """Returns the style name."""
        return self.segment.style_name

    @property
    def layer(self) -> int:
        """Returns the layer number."""
        return self.segment.layer

    @property
    def effect(self) -> str:
        """Returns the effect field."""
        return self.segment.effect

    @property
    def text(self) -> str:
        """Returns the segment text."""
        return self.segment.text


class EffectFunction(Protocol):
    """Protocol for effect functions that transform segments.

    An effect function takes an EffectContext and returns a list of
    AssSubtitleSegment objects. It may return:
    - An empty list to remove the line
    - A single segment to replace the line
    - Multiple segments to generate layered effects

    Example:
        def duplicate_layer(ctx: EffectContext) -> list[AssSubtitleSegment]:
            # Create two copies with different layers
            seg1 = copy.deepcopy(ctx.segment)
            seg1.layer = 0
            seg2 = copy.deepcopy(ctx.segment)
            seg2.layer = 1
            return [seg1, seg2]
    """

    def __call__(self, context: EffectContext) -> list[AssSubtitleSegment]:
        """Apply the effect transformation.

        Args:
            context: Effect context with segment and syllable data.

        Returns:
            List of transformed segments (may be empty, single, or multiple).
        """
        ...


@dataclass
class EffectDefinition:
    """Defines an effect transformation with selection criteria.

    Attributes:
        effect_function: The function that transforms segments.
        selector: Optional function to filter which segments to apply to.
                 If None, applies to all segments.
        name: Optional name for the effect (for debugging/logging).
        priority: Priority for ordering effects (higher = applied later).
    """

    effect_function: EffectFunction
    selector: Callable[[AssSubtitleSegment], bool] | None = None
    name: str | None = None
    priority: int = 0


class TemplateEngine:
    """Engine for applying templated effects to subtitle segments.

    This class orchestrates the process of:
    1. Selecting segments based on criteria
    2. Applying effect transformations
    3. Replacing original segments with generated output

    Example:
        >>> engine = TemplateEngine()
        >>> def glitch_effect(ctx: EffectContext) -> list[AssSubtitleSegment]:
        ...     # Generate glitched versions
        ...     return [create_glitch_segment(ctx.segment)]
        >>> definition = EffectDefinition(
        ...     effect_function=glitch_effect,
        ...     selector=lambda seg: seg.actor_name == "Robot"
        ... )
        >>> result = engine.apply_effects(subtitles, [definition])
    """

    def apply_effects(
        self,
        subtitles: AssSubtitles,
        effect_definitions: list[EffectDefinition],
    ) -> AssSubtitles:
        """Applies effect definitions to subtitle segments.

        Args:
            subtitles: The subtitle object to transform.
            effect_definitions: List of effect definitions to apply.

        Returns:
            New AssSubtitles object with transformed segments.

        Note:
            - Effects are applied in priority order (lower priority first)
            - Original subtitles object is not modified
            - Metadata (styles, script_info, etc.) is preserved
        """
        # Sort effects by priority
        sorted_effects = sorted(effect_definitions, key=lambda e: e.priority)

        # Start with the original segments
        current_segments = list(subtitles.segments)

        # Apply each effect in order
        for effect_def in sorted_effects:
            new_segments = []

            for index, segment in enumerate(current_segments):
                # Check if this segment should be transformed
                if effect_def.selector is None or effect_def.selector(segment):
                    # Extract syllables for this segment
                    syllables = extract_syllables_from_segment(segment)

                    # Create context
                    context = EffectContext(
                        segment=segment,
                        index=index,
                        syllables=syllables,
                    )

                    # Apply effect function
                    transformed = effect_def.effect_function(context)
                    new_segments.extend(transformed)
                else:
                    # Keep original segment
                    new_segments.append(segment)

            current_segments = new_segments

        # Create new AssSubtitles with transformed segments
        # Preserve all metadata from original
        result = AssSubtitles(
            segments=current_segments,
            script_info=subtitles.script_info.copy(),
            styles=list(subtitles.styles),
            style_format_keys=list(subtitles.style_format_keys),
            events_format_keys=list(subtitles.events_format_keys),
            custom_sections={k: list(v) for k, v in subtitles.custom_sections.items()},
        )

        return result

    def apply_effect_to_selection(
        self,
        subtitles: AssSubtitles,
        effect_function: EffectFunction,
        selected_segments: list[AssSubtitleSegment],
    ) -> AssSubtitles:
        """Applies an effect function to a pre-selected list of segments.

        This is a convenience method for when you've already filtered segments
        using LineSelector and want to apply an effect to just those segments.

        Args:
            subtitles: The subtitle object to transform.
            effect_function: The effect function to apply.
            selected_segments: Pre-filtered list of segments to transform.

        Returns:
            New AssSubtitles object with transformed segments.
        """
        # Create a set of selected segment IDs for fast lookup
        selected_ids = {id(seg) for seg in selected_segments}

        # Create an effect definition with a selector based on segment identity
        effect_def = EffectDefinition(
            effect_function=effect_function,
            selector=lambda seg: id(seg) in selected_ids,
        )

        return self.apply_effects(subtitles, [effect_def])
