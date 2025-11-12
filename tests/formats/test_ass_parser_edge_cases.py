import pytest

from autosubs.core.parser import parse_ass
from autosubs.models.styles import WordStyleRange


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
    assert word_music.styles == [WordStyleRange(0, 5, "{\\i1}")]

    assert word_trailing_tag.text == ""
    assert word_trailing_tag.styles == [WordStyleRange(0, 0, "{\\i0}")]
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
    assert word_trailing_tags.styles == [
        WordStyleRange(0, 0, "{\\b0}"),
        WordStyleRange(0, 0, "{\\an5}"),
    ]
    assert word_trailing_tags.start == 10.0


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
    assert word_tags_only.styles == [
        WordStyleRange(0, 0, "{\\an5}"),
        WordStyleRange(0, 0, "{\\fs30}"),
    ]
    # It should have a zero-duration at the end of the segment timeline.
    assert word_tags_only.start == 20.0
    assert word_tags_only.end == 20.0


def test_parser_weird_tags(weird_ass_content: str) -> None:
    """Test that unusual but valid formatting is parsed correctly and gracefully."""
    subs = parse_ass(weird_ass_content)

    # The parser should ignore 'Comment:' lines and handle extra commas gracefully.
    assert len(subs.segments) == 2
    assert subs.segments[0].text == "Line 1"
    # The text field is the last one, so it consumes the rest of the line.
    assert subs.segments[1].text == ",Some text with extra fields,"
