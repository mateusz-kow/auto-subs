"""Tests for ASS collision resolution functionality."""

import pytest

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_resolve_collisions_basic() -> None:
    """Test basic collision resolution with two overlapping bottom-aligned subtitles."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,First line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,Second line
"""

    subs = parse_ass(content)

    # Check initial margins are 0
    assert subs.segments[0].margin_v == 0
    assert subs.segments[1].margin_v == 0

    # Resolve collisions
    subs.resolve_collisions(1280, 720)

    # First segment should remain at margin 0
    assert subs.segments[0].margin_v == 0
    # Second segment should have increased margin due to overlap
    assert subs.segments[1].margin_v > 0


def test_resolve_collisions_no_overlap() -> None:
    """Test that non-overlapping subtitles are not affected."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:01.50,Default,,0,0,0,,First line
Dialogue: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,Second line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # No overlap, so both should have margin 0
    assert subs.segments[0].margin_v == 0
    assert subs.segments[1].margin_v == 0


def test_resolve_collisions_three_way_overlap() -> None:
    """Test collision resolution with three overlapping subtitles."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:03.00,Default,,0,0,0,,First line
Dialogue: 0,0:00:01.00,0:00:03.50,Default,,0,0,0,,Second line
Dialogue: 0,0:00:01.50,0:00:04.00,Default,,0,0,0,,Third line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # First should be at bottom
    assert subs.segments[0].margin_v == 0
    # Second and third should be stacked above
    assert subs.segments[1].margin_v > 0
    assert subs.segments[2].margin_v > subs.segments[1].margin_v


def test_resolve_collisions_top_aligned() -> None:
    """Test collision resolution with top-aligned subtitles."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,{\an8}First top line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,{\an8}Second top line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # Both should have adjusted margins
    assert subs.segments[0].margin_v == 0
    assert subs.segments[1].margin_v > 0


def test_resolve_collisions_mixed_alignment() -> None:
    """Test that top and bottom aligned subtitles are processed separately."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,{\an2}Bottom line
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,{\an8}Top line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,{\an2}Second bottom
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # Bottom lines should stack
    assert subs.segments[0].margin_v == 0
    assert subs.segments[2].margin_v > 0
    # Top line should remain at 0 (separate group)
    assert subs.segments[1].margin_v == 0


def test_resolve_collisions_with_layer_priority() -> None:
    """Test that layer values affect stacking order."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.50,0:00:02.50,Default,,0,0,0,,Higher layer
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,Lower layer
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # Lower layer (0) should stay at bottom with margin 0
    assert subs.segments[1].margin_v == 0
    # Higher layer (1) should be stacked above
    assert subs.segments[0].margin_v > 0


def test_resolve_collisions_multiline_text() -> None:
    """Test collision resolution accounts for multiline text."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,First line\NSecond line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,Third line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # First segment is multiline, so second should be offset more
    assert subs.segments[0].margin_v == 0
    # The offset should account for 2 lines in first segment
    assert subs.segments[1].margin_v > 48  # More than single line height


def test_resolve_collisions_with_custom_font_size() -> None:
    """Test collision resolution with custom font size tags."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,{\fs72}Large text
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,Normal text
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # First segment has larger font, so offset should account for that
    assert subs.segments[0].margin_v == 0
    # Second segment should be offset by at least 72 (larger font size)
    assert subs.segments[1].margin_v >= 72


def test_resolve_collisions_empty_segments() -> None:
    """Test that empty subtitle list doesn't cause errors."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Text
"""

    subs = parse_ass(content)
    # Should not raise an error
    subs.resolve_collisions(1280, 720)


def test_resolve_collisions_invalid_resolution() -> None:
    """Test that invalid resolution values raise errors."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Text
Dialogue: 0,0:00:00.50,0:00:01.50,Default,Test
"""

    subs = parse_ass(content)

    with pytest.raises(ValueError, match="Resolution must be positive"):
        subs.resolve_collisions(0, 720)

    with pytest.raises(ValueError, match="Resolution must be positive"):
        subs.resolve_collisions(1280, -720)


def test_resolve_collisions_preserves_existing_margin() -> None:
    """Test that existing margin values are preserved and added to."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,20,,First line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,Second line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # First segment should keep its margin of 20
    assert subs.segments[0].margin_v == 20
    # Second segment should have offset added
    assert subs.segments[1].margin_v > 0


def test_resolve_collisions_round_trip() -> None:
    """Test that collision resolution works with serialization."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,First line
Dialogue: 0,0:00:01.50,0:00:03.50,Default,,0,0,0,,Second line
"""

    subs = parse_ass(content)
    subs.resolve_collisions(1280, 720)

    # Serialize and parse again
    output = to_ass(subs)
    subs2 = parse_ass(output)

    # Margins should be preserved
    assert subs2.segments[0].margin_v == subs.segments[0].margin_v
    assert subs2.segments[1].margin_v == subs.segments[1].margin_v
