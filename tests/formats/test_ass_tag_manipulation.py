import dataclasses

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
        transforms=["1,1000,0.5,\\fscx200"],
        unknown_tags=["k50"],
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
