"""Example demonstrating the Template Engine feature.

This example shows how to use the TemplateEngine to apply complex
effects to subtitle segments based on criteria like actor name.
"""

import copy

from autosubs.core.selector import LineSelector
from autosubs.core.template_engine import EffectContext, EffectDefinition, TemplateEngine
from autosubs.models.subtitles.ass import AssSubtitleSegment, AssSubtitleWord, AssSubtitles


def create_sample_subtitles() -> AssSubtitles:
    """Creates sample subtitles for demonstration."""
    segments = []
    
    # Create segments for different actors
    for i, (text, actor) in enumerate([
        ("Hello, I'm a regular person.", "Human"),
        ("BEEP BOOP. I AM A ROBOT.", "Robot"),
        ("This is just normal dialogue.", "Human"),
        ("ERROR 404: EMOTIONS NOT FOUND.", "Robot"),
    ]):
        word = AssSubtitleWord(text=text, start=float(i * 2), end=float(i * 2 + 1.5))
        segment = AssSubtitleSegment(words=[word])
        segment.actor_name = actor
        segment.style_name = "Default"
        segments.append(segment)
    
    return AssSubtitles(
        segments=segments,
        script_info={"Title": "Robot Demo", "PlayResX": "1920", "PlayResY": "1080"},
        styles=[{"Name": "Default", "Fontname": "Arial", "Fontsize": "48"}],
    )


def glitch_text_effect(ctx: EffectContext) -> list[AssSubtitleSegment]:
    """Effect that creates a 'glitch' appearance for robot text.
    
    This demonstrates generating multiple layers for a single line:
    - Base layer with the text
    - Glitch layer 1 with slight offset and color shift
    - Glitch layer 2 with different offset and color shift
    """
    results = []
    
    # Base layer (layer 0)
    base = copy.deepcopy(ctx.segment)
    base.layer = 0
    results.append(base)
    
    # Glitch layer 1 (slightly offset, red tint)
    glitch1 = copy.deepcopy(ctx.segment)
    glitch1.layer = 1
    # In real usage, you'd add ASS tags here for positioning/coloring
    # For demo purposes, we'll just add text indicators
    glitch1.words[0].text = f"[GLITCH-R] {ctx.text}"
    results.append(glitch1)
    
    # Glitch layer 2 (offset differently, blue tint)
    glitch2 = copy.deepcopy(ctx.segment)
    glitch2.layer = 2
    glitch2.words[0].text = f"[GLITCH-B] {ctx.text}"
    results.append(glitch2)
    
    return results


def add_style_prefix_effect(ctx: EffectContext) -> list[AssSubtitleSegment]:
    """Effect that adds a visual prefix to indicate special formatting."""
    result = copy.deepcopy(ctx.segment)
    result.words[0].text = f"🤖 {ctx.text}"
    return [result]


def example_basic_transformation() -> None:
    """Example 1: Basic transformation applied to all segments."""
    print("\n=== Example 1: Basic Transformation ===")
    subtitles = create_sample_subtitles()
    
    # Effect that adds timestamps to all lines
    def add_timestamp(ctx: EffectContext) -> list[AssSubtitleSegment]:
        result = copy.deepcopy(ctx.segment)
        timestamp = f"[{ctx.line_start:.1f}s]"
        result.words[0].text = f"{timestamp} {ctx.text}"
        return [result]
    
    engine = TemplateEngine()
    effect = EffectDefinition(effect_function=add_timestamp)
    result = engine.apply_effects(subtitles, [effect])
    
    print("Original segments:")
    for seg in subtitles.segments:
        print(f"  {seg.text}")
    
    print("\nTransformed segments:")
    for seg in result.segments:
        print(f"  {seg.text}")


def example_selective_transformation() -> None:
    """Example 2: Transform only segments matching criteria."""
    print("\n=== Example 2: Selective Transformation (Robot Lines Only) ===")
    subtitles = create_sample_subtitles()
    
    # Apply glitch effect only to Robot's lines
    engine = TemplateEngine()
    effect = EffectDefinition(
        effect_function=glitch_text_effect,
        selector=lambda seg: seg.actor_name == "Robot",
        name="Robot Glitch Effect",
    )
    result = engine.apply_effects(subtitles, [effect])
    
    print(f"Original segments: {len(subtitles.segments)}")
    print(f"Transformed segments: {len(result.segments)} (Robot lines multiplied to 3 layers each)")
    
    for seg in result.segments:
        print(f"  Layer {seg.layer}: {seg.actor_name:6} - {seg.text}")


def example_using_line_selector() -> None:
    """Example 3: Use LineSelector for complex filtering."""
    print("\n=== Example 3: Using LineSelector ===")
    subtitles = create_sample_subtitles()
    
    # Use LineSelector to pre-filter segments
    robot_segments = LineSelector.by_actor(subtitles.segments, "Robot")
    
    # Apply effect to the pre-selected segments
    engine = TemplateEngine()
    result = engine.apply_effect_to_selection(
        subtitles,
        add_style_prefix_effect,
        robot_segments,
    )
    
    print("Lines with robot emoji prefix:")
    for seg in result.segments:
        print(f"  {seg.actor_name:6} - {seg.text}")


def example_multiple_effects() -> None:
    """Example 4: Apply multiple effects in sequence."""
    print("\n=== Example 4: Multiple Effects (Priorities) ===")
    subtitles = create_sample_subtitles()
    
    # Effect 1: Uppercase robot lines (priority 0)
    def uppercase_robots(ctx: EffectContext) -> list[AssSubtitleSegment]:
        if ctx.actor != "Robot":
            return [ctx.segment]
        result = copy.deepcopy(ctx.segment)
        result.words[0].text = ctx.text.upper()
        return [result]
    
    # Effect 2: Add brackets to all lines (priority 1, applied after uppercase)
    def add_brackets(ctx: EffectContext) -> list[AssSubtitleSegment]:
        result = copy.deepcopy(ctx.segment)
        result.words[0].text = f"[ {ctx.text} ]"
        return [result]
    
    engine = TemplateEngine()
    effects = [
        EffectDefinition(effect_function=uppercase_robots, priority=0, name="Uppercase"),
        EffectDefinition(effect_function=add_brackets, priority=1, name="Add Brackets"),
    ]
    result = engine.apply_effects(subtitles, effects)
    
    print("After applying both effects (uppercase → brackets):")
    for seg in result.segments:
        print(f"  {seg.actor_name:6} - {seg.text}")


def example_syllable_based_effect() -> None:
    """Example 5: Effect that uses syllable-level timing data."""
    print("\n=== Example 5: Syllable-Based Effect ===")
    
    # Create a segment with karaoke timing tags
    # Note: In real usage, these would be parsed from an ASS file
    from autosubs.models.subtitles.ass import AssTagBlock, WordStyleRange
    
    word = AssSubtitleWord(text="Hello", start=0.0, end=1.0)
    # Add karaoke tag (this is simplified; real usage would parse from ASS)
    tag_block = AssTagBlock(unknown_tags=("k50",))
    word.styles = [WordStyleRange(0, 5, tag_block)]
    
    segment = AssSubtitleSegment(words=[word])
    subtitles = AssSubtitles(segments=[segment])
    
    # Effect that processes each syllable
    def syllable_processor(ctx: EffectContext) -> list[AssSubtitleSegment]:
        if not ctx.syllables:
            return [ctx.segment]
        
        result = copy.deepcopy(ctx.segment)
        syllable_info = ", ".join([f"{syl.text}({syl.duration}cs)" for syl in ctx.syllables])
        result.words[0].text = f"{ctx.text} [Syllables: {syllable_info}]"
        return [result]
    
    engine = TemplateEngine()
    effect = EffectDefinition(effect_function=syllable_processor)
    result = engine.apply_effects(subtitles, [effect])
    
    print("Syllable information extracted:")
    for seg in result.segments:
        print(f"  {seg.text}")


def main() -> None:
    """Run all examples."""
    print("=" * 70)
    print("Template Engine Examples")
    print("=" * 70)
    
    example_basic_transformation()
    example_selective_transformation()
    example_using_line_selector()
    example_multiple_effects()
    example_syllable_based_effect()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
