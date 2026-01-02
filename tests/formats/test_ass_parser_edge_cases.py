import pytest

from autosubs.core.parser import parse_ass
from autosubs.models.subtitles.ass import AssTagBlock


@pytest.fixture
def weird_ass_content() -> str:
    """Provide ASS content with unusual but potentially valid formatting."""
    return (
        "[Script Info]\n"
        ";-;\n"
        "Title: Weirdness\n\n"
        "[v4+ STYLES]\n"  # Mixed case
        "Format: Name, Fontname, Fontsize\n"
        "Style: Default,Arial,20,,\n"  # Extra trailing commas
        "\n"
        "[Events]\n"
        "Format: Layer,Start,End,Style,Text\n"
        "Comment: 0,0:00:01.00,0:00:02.00,Default,This is a comment line, it should be ignored\n"
        "Dialogue: 0,0:00:03.00,0:00:04.00,Default,Line 1\n"
        "Dialogue: 0,0:00:05.00,0:00:06.00,Default,,Some text with extra fields,\n"  # Extra commas
        "\n"
        "[Fonts]\n"  # Empty section
        "\n"
        "[Graphics]\n"  # Empty section
    )


def test_parser_handles_trailing_tag() -> None:
    """Test that a single style tag at the end of the line is preserved."""
    content = (
        "[Events]\n"
        "Format: Layer, Start, End, Style, Text\n"
        "Dialogue: 0,0:00:01.00,0:00:02.00,Default,{\\i1}Music{\\i0}\n"
    )
    subs = parse_ass(content)
    segment = subs.segments[0]

    # Should be parsed into two "words": "Music" and an empty word for the final tag.
    assert len(segment.words) == 2
    word_music, word_trailing_tag = segment.words

    assert word_music.text == "Music"
    assert len(word_music.styles) == 1
    assert word_music.styles[0].tag_block == AssTagBlock(italic=True)

    assert word_trailing_tag.text == ""
    assert len(word_trailing_tag.styles) == 1
    assert word_trailing_tag.styles[0].tag_block == AssTagBlock(italic=False)
    # The zero-duration word should be at the very end of the segment timeline.
    assert word_trailing_tag.start == 2.0
    assert word_trailing_tag.end == 2.0


def test_parser_handles_multiple_trailing_tags() -> None:
    """Test that multiple style tags at the end of a line are grouped and preserved."""
    content = (
        "[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,0:00:05.00,0:00:10.00,Styled,Text{\\b0}{\\an5}\n"
    )
    subs = parse_ass(content)
    segment = subs.segments[0]

    # Should be parsed into two "words": "Text" and an empty word for the final tags.
    assert len(segment.words) == 2
    word_text, word_trailing_tags = segment.words

    assert word_text.text == "Text"
    assert not word_text.styles

    assert word_trailing_tags.text == ""
    # Both tags should be present on the final empty word, in order.
    assert len(word_trailing_tags.styles) == 2
    assert word_trailing_tags.styles[0].tag_block == AssTagBlock(bold=False)
    assert word_trailing_tags.styles[1].tag_block == AssTagBlock(alignment=5)
    assert word_trailing_tags.start == pytest.approx(10.0)


def test_parser_handles_tag_only_line() -> None:
    """Test that a dialogue line containing only tags is parsed correctly."""
    content = (
        "[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,0:00:15.00,0:00:20.00,Default,{\\an5}{\\fs30}\n"
    )
    subs = parse_ass(content)

    assert len(subs.segments) == 1
    segment = subs.segments[0]

    # The entire line should be represented by a single, empty-text word.
    assert len(segment.words) == 1
    word_tags_only = segment.words[0]

    assert word_tags_only.text == ""
    assert len(word_tags_only.styles) == 2
    assert word_tags_only.styles[0].tag_block == AssTagBlock(alignment=5)
    assert word_tags_only.styles[1].tag_block == AssTagBlock(font_size=30.0)
    # It should have a zero-duration at the end of the segment timeline.
    assert word_tags_only.start == pytest.approx(20.0)
    assert word_tags_only.end == pytest.approx(20.0)


def test_parser_weird_tags(weird_ass_content: str) -> None:
    """Test that unusual but valid formatting is parsed correctly and gracefully."""
    subs = parse_ass(weird_ass_content)

    # The parser should now parse 'Comment:' lines with is_comment flag set.
    assert len(subs.segments) == 3
    assert subs.segments[0].is_comment
    assert subs.segments[0].text == "This is a comment line, it should be ignored"
    assert subs.segments[1].text == "Line 1"
    # The text field is the last one, so it consumes the rest of the line.
    assert subs.segments[2].text == ",Some text with extra fields,"


def test_parser_handles_invalid_move_tag_parameter_count() -> None:
    """Test that move tags with invalid parameter counts are handled gracefully."""
    # Test with 3 parameters (invalid)
    content_3_params = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:00.00,0:00:05.00,Default,{\\move(100,200,300)}Invalid move\n"
    )
    subs = parse_ass(content_3_params)
    # Should parse but move tag fields should be None (warning is logged)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 is None
    assert tag_block.move_y1 is None
    assert tag_block.move_x2 is None
    assert tag_block.move_y2 is None
    # The tag is silently ignored (with warning) - it's not in unknown_tags
    assert "move" not in "".join(tag_block.unknown_tags)

    # Test with 5 parameters (invalid)
    content_5_params = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:00.00,0:00:05.00,Default,{\\move(100,200,300,400,500)}Invalid move\n"
    )
    subs = parse_ass(content_5_params)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 is None
    assert tag_block.move_x2 is None
    assert "move" not in "".join(tag_block.unknown_tags)

    # Test with 7 parameters (invalid)
    content_7_params = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:00.00,0:00:05.00,Default,{\\move(1,2,3,4,5,6,7)}Invalid move\n"
    )
    subs = parse_ass(content_7_params)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 is None
    assert "move" not in "".join(tag_block.unknown_tags)

    # Test with 1 parameter (invalid)
    content_1_param = (
        "[Events]\nFormat: Start, End, Style, Text\nDialogue: 0:00:00.00,0:00:05.00,Default,{\\move(100)}Invalid move\n"
    )
    subs = parse_ass(content_1_param)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 is None


def test_parser_handles_valid_move_tag_4_params() -> None:
    """Test that move tags with 4 parameters are parsed correctly."""
    content = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:00.00,0:00:05.00,Default,{\\move(100,200,300,400)}Valid move\n"
    )
    subs = parse_ass(content)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 == pytest.approx(100.0)
    assert tag_block.move_y1 == pytest.approx(200.0)
    assert tag_block.move_x2 == pytest.approx(300.0)
    assert tag_block.move_y2 == pytest.approx(400.0)
    assert tag_block.move_t1 is None
    assert tag_block.move_t2 is None
    assert "move" not in "".join(tag_block.unknown_tags)


def test_parser_handles_valid_move_tag_6_params() -> None:
    """Test that move tags with 6 parameters are parsed correctly."""
    content = (
        "[Events]\n"
        "Format: Start, End, Style, Text\n"
        "Dialogue: 0:00:00.00,0:00:05.00,Default,{\\move(100,200,300,400,0,5000)}Valid move with time\n"
    )
    subs = parse_ass(content)
    assert len(subs.segments) == 1
    tag_block = subs.segments[0].words[0].styles[0].tag_block
    assert tag_block.move_x1 == pytest.approx(100.0)
    assert tag_block.move_y1 == pytest.approx(200.0)
    assert tag_block.move_x2 == pytest.approx(300.0)
    assert tag_block.move_y2 == pytest.approx(400.0)
    assert tag_block.move_t1 == 0
    assert tag_block.move_t2 == 5000
    assert "move" not in "".join(tag_block.unknown_tags)
