import dataclasses

import pytest

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass
from autosubs.models.subtitles.ass import AssTagBlock, WordStyleRange


def test_ass_tag_block_serialization() -> None:
    """Test basic serialization of an AssTagBlock."""
    tag_block = AssTagBlock(bold=True, font_size=50, position_x=100, position_y=200)
    assert tag_block.to_ass_string() == "{\\pos(100,200)\\fs50\\b1}"


def test_ass_tag_block_property_removal() -> None:
    """Test that setting a property to None removes it from the output."""
    tag_block = AssTagBlock(bold=True, italic=True)
    assert "\\b1" in tag_block.to_ass_string()
    assert "\\i1" in tag_block.to_ass_string()

    # AssTagBlock is frozen, so we use dataclasses.replace
    modified_block = dataclasses.replace(tag_block, bold=None)
    assert "\\b1" not in modified_block.to_ass_string()
    assert "\\i1" in modified_block.to_ass_string()


def test_ass_tag_block_complex_serialization() -> None:
    """Test serialization of complex properties like transforms and unknown tags."""
    tag_block = AssTagBlock(
        primary_color="&H00FFFFFF&",
        transforms=("1,1000,0.5,\\fscx200",),
        unknown_tags=("k50",),
        alpha="&H80&",
        fade=(200, 300),
    )
    result = tag_block.to_ass_string()
    assert "\\c&H00FFFFFF&" in result
    assert "\\alpha&H80&" in result
    assert "\\t(1,1000,0.5,\\fscx200)" in result
    assert "\\k50" in result
    assert "\\fad(200,300)" in result
    assert "fad(200,300)" not in tag_block.unknown_tags


def test_computed_ass_tag_property() -> None:
    """Test the backward-compatible `ass_tag` property on WordStyleRange."""
    tag_block = AssTagBlock(underline=True, strikeout=False)
    style_range = WordStyleRange(start_char_index=0, end_char_index=1, tag_block=tag_block)
    assert style_range.ass_tag == "{\\u1\\s0}"


def test_round_trip_with_modification() -> None:
    """Test a full parse -> modify -> serialize -> re-parse cycle."""
    content = "[Events]\nFormat: Start, End, Text\nDialogue: 0:00:01.00,0:00:02.00,Test {\\b1}text\n"
    subs = parse_ass(content)

    # In this simple case, the text "text" is part of the first word "Test text"
    # The split is "Test ", then "text". Let's check the words.
    word_with_style = subs.segments[0].words[1]
    original_style_range = word_with_style.styles[0]

    # Modify: add italic and change boldness
    modified_block = dataclasses.replace(original_style_range.tag_block, bold=False, italic=True)
    word_with_style.styles[0] = dataclasses.replace(original_style_range, tag_block=modified_block)

    new_content = to_ass(subs)

    # Note: the parser splits "Test {\\b1}text" into "Test " and "text", so we reconstruct it as such.
    # The output should respect the minimal format from the input content.
    expected_line = "Dialogue: 0:00:01.00,0:00:02.00,Test {\\b0\\i1}text"
    assert expected_line in new_content

    # Re-parse and verify
    new_subs = parse_ass(new_content)
    new_block = new_subs.segments[0].words[1].styles[0].tag_block
    assert new_block.bold is False
    assert new_block.italic is True


def test_move_tag_serialization_with_time() -> None:
    """Test serialization of move tag with time parameters."""
    tag_block = AssTagBlock(
        move_x1=100,
        move_y1=200,
        move_x2=300,
        move_y2=400,
        move_t1=0,
        move_t2=5000,
    )
    result = tag_block.to_ass_string()
    assert result == "{\\move(100,200,300,400,0,5000)}"


def test_move_tag_serialization_without_time() -> None:
    """Test serialization of move tag without time parameters."""
    tag_block = AssTagBlock(
        move_x1=100,
        move_y1=200,
        move_x2=300,
        move_y2=400,
    )
    result = tag_block.to_ass_string()
    assert result == "{\\move(100,200,300,400)}"


def test_move_tag_serialization_with_floats() -> None:
    """Test serialization of move tag with float coordinates."""
    tag_block = AssTagBlock(
        move_x1=100.5,
        move_y1=200.75,
        move_x2=300.25,
        move_y2=400.0,
        move_t1=1000,
        move_t2=5000,
    )
    result = tag_block.to_ass_string()
    # Whole numbers should drop .0
    assert result == "{\\move(100.5,200.75,300.25,400,1000,5000)}"


def test_move_tag_serialization_combined_with_other_tags() -> None:
    """Test serialization of move tag combined with other tags."""
    tag_block = AssTagBlock(
        position_x=640,
        position_y=360,
        move_x1=100,
        move_y1=200,
        move_x2=300,
        move_y2=400,
        font_size=48,
        bold=True,
    )
    result = tag_block.to_ass_string()
    # Order matters: pos and org first, then move, then other tags
    assert "\\pos(640,360)" in result
    assert "\\move(100,200,300,400)" in result
    assert "\\fs48" in result
    assert "\\b1" in result


def test_move_tag_partial_coordinates_not_serialized() -> None:
    """Test that move tag is not serialized if not all coordinates are present."""
    # Only x1 and y1 set
    tag_block = AssTagBlock(
        move_x1=100,
        move_y1=200,
    )
    result = tag_block.to_ass_string()
    assert "\\move" not in result

    # Only x1, y1, x2 set (missing y2)
    tag_block2 = AssTagBlock(
        move_x1=100,
        move_y1=200,
        move_x2=300,
    )
    result2 = tag_block2.to_ass_string()
    assert "\\move" not in result2


def test_move_tag_round_trip() -> None:
    """Test parsing and serializing move tags maintains data."""
    content = r"""[Script Info]
Title: Test

[Events]
Format: Start, End, Style, Text
Dialogue: 0:00:00.00,0:00:05.00,Default,{\move(60,100,150,250,0,5000)}Moving text
Dialogue: 0:00:05.00,0:00:10.00,Default,{\move(100,200,300,400)}No time params
"""

    subs = parse_ass(content)

    # Check first move tag (with time)
    move_tag1 = subs.segments[0].words[0].styles[0].tag_block
    assert move_tag1.move_x1 == pytest.approx(60.0)
    assert move_tag1.move_y1 == pytest.approx(100.0)
    assert move_tag1.move_x2 == pytest.approx(150.0)
    assert move_tag1.move_y2 == pytest.approx(250.0)
    assert move_tag1.move_t1 == 0
    assert move_tag1.move_t2 == 5000
    assert "\\move(60,100,150,250,0,5000)" in move_tag1.to_ass_string()

    # Check second move tag (without time)
    move_tag2 = subs.segments[1].words[0].styles[0].tag_block
    assert move_tag2.move_x1 == pytest.approx(100.0)
    assert move_tag2.move_y1 == pytest.approx(200.0)
    assert move_tag2.move_x2 == pytest.approx(300.0)
    assert move_tag2.move_y2 == pytest.approx(400.0)
    assert move_tag2.move_t1 is None
    assert move_tag2.move_t2 is None
    assert "\\move(100,200,300,400)" in move_tag2.to_ass_string()

    # Re-serialize and verify
    output = to_ass(subs)
    assert "\\move(60,100,150,250,0,5000)" in output
    assert "\\move(100,200,300,400)" in output
