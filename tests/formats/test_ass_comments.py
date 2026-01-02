"""Tests for ASS comment handling functionality."""

import pytest

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_parse_ass_with_script_info_comments() -> None:
    """Test that comments in [Script Info] section are preserved."""
    content = (
        "[Script Info]\n"
        "; This is a header comment\n"
        "Title: Test\n"
        "; Another comment\n"
        "ScriptType: v4.00+\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.script_info_comments) == 2
    assert subs.script_info_comments[0] == (0, "; This is a header comment")
    assert subs.script_info_comments[1] == (2, "; Another comment")
    assert subs.script_info["Title"] == "Test"
    assert subs.script_info["ScriptType"] == "v4.00+"


def test_parse_ass_with_styles_comments() -> None:
    """Test that comments in [V4+ Styles] section are preserved."""
    content = (
        "[V4+ Styles]\n"
        "; Style definitions below\n"
        "Format: Name, Fontname, Fontsize\n"
        "; Default style\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.styles_comments) == 2
    assert subs.styles_comments[0] == (0, "; Style definitions below")
    assert subs.styles_comments[1] == (2, "; Default style")


def test_parse_ass_with_events_comments() -> None:
    """Test that `;` comments in [Events] section are preserved."""
    content = (
        "[Events]\n"
        "; Event definitions\n"
        "Format: Start, End, Text\n"
        "; First dialogue\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Hello\n"
        "; Second dialogue\n"
        "Dialogue: 0:00:03.00,0:00:04.00,World\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.events_comments) == 3
    assert subs.events_comments[0] == (0, "; Event definitions")
    assert subs.events_comments[1] == (2, "; First dialogue")
    assert subs.events_comments[2] == (4, "; Second dialogue")
    assert len(subs.segments) == 2


def test_parse_ass_comment_dialogue_lines() -> None:
    """Test that Comment: dialogue lines are parsed with is_comment flag."""
    content = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Default,Hello\n"
        "Comment: 0:00:02.50,0:00:03.00,Default,This is a comment line\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Default,World\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.segments) == 3
    assert not subs.segments[0].is_comment
    assert subs.segments[1].is_comment
    assert subs.segments[1].text == "This is a comment line"
    assert not subs.segments[2].is_comment


def test_parse_ass_without_comments() -> None:
    """Test that include_comments=False skips all `;` comments."""
    content = (
        "[Script Info]\n"
        "; This comment should be skipped\n"
        "Title: Test\n"
        "\n"
        "[Events]\n"
        "; This comment too\n"
        "Format: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Hello\n"
    )

    subs = parse_ass(content, include_comments=False)

    assert len(subs.script_info_comments) == 0
    assert len(subs.events_comments) == 0
    assert subs.script_info["Title"] == "Test"
    assert len(subs.segments) == 1


def test_parse_ass_custom_section_with_comments() -> None:
    """Test that custom sections treat `;` lines as content when include_comments=True."""
    content = (
        "[Script Info]\n"
        "Title: Test\n"
        "\n"
        "[Custom Section]\n"
        "; This looks like a comment but is content\n"
        "Some data\n"
        "; More content\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert "[Custom Section]" in subs.custom_sections
    assert len(subs.custom_sections["[Custom Section]"]) == 3
    assert subs.custom_sections["[Custom Section]"][0] == "; This looks like a comment but is content"
    assert subs.custom_sections["[Custom Section]"][1] == "Some data"
    assert subs.custom_sections["[Custom Section]"][2] == "; More content"


def test_parse_ass_custom_section_without_comments() -> None:
    """Test that custom sections skip `;` lines when include_comments=False."""
    content = (
        "[Script Info]\n"
        "Title: Test\n"
        "\n"
        "[Custom Section]\n"
        "; This should be skipped\n"
        "Some data\n"
    )

    subs = parse_ass(content, include_comments=False)

    assert "[Custom Section]" in subs.custom_sections
    assert len(subs.custom_sections["[Custom Section]"]) == 1
    assert subs.custom_sections["[Custom Section]"][0] == "Some data"


def test_generate_ass_with_script_info_comments() -> None:
    """Test that script info comments are written back to the generated file."""
    content = (
        "[Script Info]\n"
        "; Comment at start\n"
        "Title: Test\n"
        "; Comment in middle\n"
        "ScriptType: v4.00+\n"
        "\n"
        "[V4+ Styles]\n"
        "\n"
        "[Events]\n"
        "Format: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Hello\n"
    )

    subs = parse_ass(content, include_comments=True)
    generated = to_ass(subs)

    assert "; Comment at start" in generated
    assert "; Comment in middle" in generated
    # Check order is preserved
    lines = generated.split("\n")
    script_section_start = lines.index("[Script Info]")
    comment1_idx = next(i for i, line in enumerate(lines[script_section_start:]) if "; Comment at start" in line)
    title_idx = next(i for i, line in enumerate(lines[script_section_start:]) if "Title:" in line)
    comment2_idx = next(i for i, line in enumerate(lines[script_section_start:]) if "; Comment in middle" in line)

    assert comment1_idx < title_idx < comment2_idx


def test_generate_ass_with_events_comments() -> None:
    """Test that event comments are written back to the generated file."""
    content = (
        "[Script Info]\n"
        "Title: Test\n"
        "\n"
        "[V4+ Styles]\n"
        "\n"
        "[Events]\n"
        "; Comment before format\n"
        "Format: Start, End, Text\n"
        "; Comment before dialogue\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Hello\n"
    )

    subs = parse_ass(content, include_comments=True)
    generated = to_ass(subs)

    assert "; Comment before format" in generated
    assert "; Comment before dialogue" in generated


def test_generate_ass_with_comment_dialogue_lines() -> None:
    """Test that Comment: dialogue lines are generated correctly."""
    content = (
        "[Script Info]\n"
        "Title: Test\n"
        "\n"
        "[V4+ Styles]\n"
        "\n"
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Default,Hello\n"
        "Comment: 0:00:02.50,0:00:03.00,Default,This is a comment\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Default,World\n"
    )

    subs = parse_ass(content, include_comments=True)
    generated = to_ass(subs)

    assert "Comment: " in generated
    assert "This is a comment" in generated
    # Verify it's generated as Comment: not Dialogue:
    lines = generated.split("\n")
    comment_line = next(line for line in lines if "This is a comment" in line)
    assert comment_line.startswith("Comment:")


def test_roundtrip_ass_with_all_comment_types() -> None:
    """Test that all comment types survive a parse-generate roundtrip."""
    content = (
        "[Script Info]\n"
        "; Script info comment\n"
        "Title: Test\n"
        "ScriptType: v4.00+\n"
        "\n"
        "[V4+ Styles]\n"
        "; Styles comment\n"
        "Format: Name, Fontname, Fontsize\n"
        "\n"
        "[Events]\n"
        "; Events comment\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Default,Hello\n"
        "Comment: 0:00:02.50,0:00:03.00,Default,Commented line\n"
        "; Another event comment\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Default,World\n"
        "\n"
        "[Custom]\n"
        "; Custom section data\n"
        "SomeData\n"
    )

    subs = parse_ass(content, include_comments=True)
    generated = to_ass(subs)

    # Parse again to verify roundtrip
    subs2 = parse_ass(generated, include_comments=True)

    assert len(subs2.script_info_comments) == len(subs.script_info_comments)
    assert len(subs2.styles_comments) == len(subs.styles_comments)
    assert len(subs2.events_comments) == len(subs.events_comments)
    assert len(subs2.segments) == len(subs.segments)
    assert subs2.segments[1].is_comment == subs.segments[1].is_comment
    assert "[Custom]" in subs2.custom_sections
    assert "; Custom section data" in subs2.custom_sections["[Custom]"]


def test_parse_ass_empty_comments() -> None:
    """Test that ASS files without comments work correctly."""
    content = (
        "[Script Info]\n"
        "Title: Test\n"
        "\n"
        "[Events]\n"
        "Format: Start, End, Text\n"
        "Dialogue: 0:00:01.00,0:00:02.00,Hello\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.script_info_comments) == 0
    assert len(subs.styles_comments) == 0
    assert len(subs.events_comments) == 0
    assert len(subs.segments) == 1


def test_parse_ass_multiple_consecutive_comments() -> None:
    """Test that multiple consecutive comments are preserved."""
    content = (
        "[Script Info]\n"
        "; Comment 1\n"
        "; Comment 2\n"
        "; Comment 3\n"
        "Title: Test\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.script_info_comments) == 3
    assert subs.script_info_comments[0][1] == "; Comment 1"
    assert subs.script_info_comments[1][1] == "; Comment 2"
    assert subs.script_info_comments[2][1] == "; Comment 3"


def test_comment_dialogue_with_complex_metadata() -> None:
    """Test that Comment: lines with full metadata are parsed correctly."""
    content = (
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Comment: 1,0:00:01.00,0:00:02.00,TestStyle,Actor,10,20,30,Effect,Comment text\n"
    )

    subs = parse_ass(content, include_comments=True)

    assert len(subs.segments) == 1
    segment = subs.segments[0]
    assert segment.is_comment
    assert segment.layer == 1
    assert segment.start == pytest.approx(1.0)
    assert segment.end == pytest.approx(2.0)
    assert segment.style_name == "TestStyle"
    assert segment.actor_name == "Actor"
    assert segment.margin_l == 10
    assert segment.margin_r == 20
    assert segment.margin_v == 30
    assert segment.effect == "Effect"
    assert segment.text == "Comment text"
