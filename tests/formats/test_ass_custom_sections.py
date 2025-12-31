"""Tests for parsing and preserving custom ASS sections."""

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_parse_ass_preserves_fonts_section() -> None:
    """Test that [Fonts] section is preserved during parsing."""
    content = """[Script Info]
Title: Test with Fonts
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour
Style: Default,Arial,20,&H00FFFFFF

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Test line

[Fonts]
fontname: Arial.ttf
0000000000000000000000000001M4[5H000000000000
00000000000000000000004U@`4U@`000000000000000
"""
    subs = parse_ass(content)

    assert "[Fonts]" in subs.custom_sections
    assert len(subs.custom_sections["[Fonts]"]) == 3
    assert subs.custom_sections["[Fonts]"][0] == "fontname: Arial.ttf"
    assert "0000000000000000000000000001M4[5H000000000000" in subs.custom_sections["[Fonts]"][1]


def test_parse_ass_preserves_graphics_section() -> None:
    """Test that [Graphics] section is preserved during parsing."""
    content = """[Script Info]
Title: Test with Graphics

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test

[Graphics]
graphic1.png
0000000000000000000000000001M4[5H000000000000
00000000000000000000004U@`4U@`000000000000000
"""
    subs = parse_ass(content)

    assert "[Graphics]" in subs.custom_sections
    assert len(subs.custom_sections["[Graphics]"]) == 3
    assert subs.custom_sections["[Graphics]"][0] == "graphic1.png"


def test_parse_ass_preserves_arbitrary_custom_section() -> None:
    """Test that arbitrary custom sections are preserved."""
    content = """[Script Info]
Title: Test with Custom Section

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test

[Custom Section]
key1: value1
key2: value2
some arbitrary data
"""
    subs = parse_ass(content)

    assert "[Custom Section]" in subs.custom_sections
    assert len(subs.custom_sections["[Custom Section]"]) == 3
    assert subs.custom_sections["[Custom Section]"][0] == "key1: value1"
    assert subs.custom_sections["[Custom Section]"][1] == "key2: value2"
    assert subs.custom_sections["[Custom Section]"][2] == "some arbitrary data"


def test_parse_ass_preserves_multiple_custom_sections() -> None:
    """Test that multiple custom sections are all preserved."""
    content = """[Script Info]
Title: Test

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test

[Fonts]
font.ttf

[Graphics]
image.png

[Aegisub Project Garbage]
Audio File: audio.mp3
Video File: video.mp4
"""
    subs = parse_ass(content)

    assert "[Fonts]" in subs.custom_sections
    assert "[Graphics]" in subs.custom_sections
    assert "[Aegisub Project Garbage]" in subs.custom_sections
    assert len(subs.custom_sections) == 3


def test_round_trip_preserves_custom_sections() -> None:
    """Test that custom sections survive a parse->generate round trip."""
    original_content = """[Script Info]
Title: Round Trip Test
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour
Style: Default,Arial,20,&H00FFFFFF

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Test line

[Fonts]
fontname: Arial.ttf
0000000000000000000000000001M4[5H000000000000

[Graphics]
image.png
ABCDEF0123456789
"""

    # Parse the original content
    subs = parse_ass(original_content)

    # Modify a dialogue line (simulate editing)
    subs.segments[0].words[0].text = "Modified line"

    # Generate ASS output (no styler needed for AssSubtitles)
    output = to_ass(subs)

    # Verify custom sections are in the output
    assert "[Fonts]" in output
    assert "fontname: Arial.ttf" in output
    assert "0000000000000000000000000001M4[5H000000000000" in output
    assert "[Graphics]" in output
    assert "image.png" in output
    assert "ABCDEF0123456789" in output

    # Verify the edit was applied
    assert "Modified line" in output


def test_round_trip_with_sample3() -> None:
    """Test round trip with the actual sample3.ass file that has [Fonts] section."""
    with open("tests/fixtures/ass/sample3.ass") as f:
        original_content = f.read()

    # Parse the file
    subs = parse_ass(original_content)

    # Verify the [Fonts] section was captured
    assert "[Fonts]" in subs.custom_sections
    assert len(subs.custom_sections["[Fonts]"]) == 9  # 9 font mappings

    # Verify specific font mappings
    assert any("impact: impact.ttf" in line for line in subs.custom_sections["[Fonts]"])
    assert any("comic sans ms: comic.ttf" in line for line in subs.custom_sections["[Fonts]"])

    # The text property converts \N to actual newlines
    assert "The quick brown fox jumps over a lazy dog." in subs.segments[0].text
    assert "Sphinx of black quartz, judge my vow." in subs.segments[0].text


def test_empty_custom_sections() -> None:
    """Test that files without custom sections work correctly."""
    content = """[Script Info]
Title: No Custom Sections

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test
"""
    subs = parse_ass(content)

    assert len(subs.custom_sections) == 0

    # Should generate output without errors
    output = to_ass(subs)
    assert "[Script Info]" in output
    assert "[Events]" in output


def test_custom_section_skips_empty_lines() -> None:
    """Test that custom sections can contain empty lines."""
    content = """[Script Info]
Title: Test

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test

[Custom]
line1

line3
"""
    subs = parse_ass(content)

    # Empty lines and comment lines should be skipped during parsing
    assert "[Custom]" in subs.custom_sections
    # Only non-empty, non-comment lines should be stored
    assert "line1" in subs.custom_sections["[Custom]"]
    assert "line3" in subs.custom_sections["[Custom]"]


def test_custom_section_preserves_whitespace() -> None:
    """Test that leading whitespace is preserved in custom sections."""
    content = """[Script Info]
Title: Test

[Events]
Format: Start, End, Text
Dialogue: 0:00:00.00,0:00:05.00,Test

[Fonts]
  fontname: Arial.ttf
"""
    subs = parse_ass(content)

    assert "[Fonts]" in subs.custom_sections
    # Leading whitespace should be preserved, trailing whitespace is stripped (rstrip)
    assert subs.custom_sections["[Fonts]"][0] == "  fontname: Arial.ttf"
