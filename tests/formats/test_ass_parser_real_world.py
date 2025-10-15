from autosubs.core.parser import parse_ass
from autosubs.models.styles.ass import WordStyleRange


def test_parser_handles_multi_digit_hour_timestamps() -> None:
    """Test that the parser correctly handles hh:mm:ss.cs timestamps."""
    content = (
        "[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,00:00:01.50,00:00:02.50,Default,Hello world\n"
    )
    subs = parse_ass(content)

    assert len(subs.segments) == 1
    segment = subs.segments[0]
    assert segment.start == 1.5
    assert segment.end == 2.5
    assert segment.text == "Hello world"


def test_parser_handles_trailing_tag_from_bug_report() -> None:
    """Test the specific 'dangling tag' case reported in the bug."""
    content = (
        "[Events]\n"
        "Format: Layer, Start, End, Style, Text\n"
        "Dialogue: 0,0:00:02.65,0:00:09.60,Default,{\\i1}Music{\\i0}\n"
    )
    subs = parse_ass(content)
    segment = subs.segments[0]

    assert len(segment.words) == 2
    word_music, word_trailing_tag = segment.words

    assert word_music.text == "Music"
    assert word_music.styles == [WordStyleRange(0, 5, "{\\i1}")]

    assert word_trailing_tag.text == ""
    assert word_trailing_tag.styles == [WordStyleRange(0, 0, "{\\i0}")]
    assert word_trailing_tag.start == 9.60
    assert word_trailing_tag.end == 9.60
