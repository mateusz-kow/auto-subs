import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core.parser import parse_ass
from autosubs.models import AssSubtitles, AssSubtitleSegment, WordStyleRange
from autosubs.models.subtitles.ass import AssTagBlock


def test_parse_ass_structure(simple_ass_content: str) -> None:
    """Test that the basic structure of an ASS file is parsed correctly."""
    subs = parse_ass(simple_ass_content)

    assert isinstance(subs, AssSubtitles)
    assert subs.script_info["Title"] == "Test Script"


def test_parse_ass_dialogue_metadata(simple_ass_content: str) -> None:
    """Test that Dialogue line metadata is parsed into an AssSubtitleSegment."""
    subs = parse_ass(simple_ass_content)

    assert len(subs.segments) == 1
    segment = subs.segments[0]
    assert isinstance(segment, AssSubtitleSegment)
    assert segment.start == 1.0
    assert segment.end == 2.0
    assert segment.style_name == "Default"
    assert segment.layer == 0


def test_parse_ass_word_and_style_parsing(complex_ass_content: str) -> None:
    """Test the detailed parsing of inline style tags into WordStyleRange objects."""
    subs = parse_ass(complex_ass_content)

    segment = subs.segments[1]
    assert segment.actor_name == "ActorName"
    assert segment.effect == "Banner;Text banner"

    assert len(segment.words) == 3
    word1, word2, word3 = segment.words
    assert word1.text == "Mid-word st"
    assert word2.text == "y"
    assert word3.text == "le."
    assert not word1.styles
    assert len(word2.styles) == 1
    assert word2.styles[0].tag_block == AssTagBlock(italic=True)
    assert len(word3.styles) == 1
    assert word3.styles[0].tag_block == AssTagBlock(italic=False)

    segment_karaoke = subs.segments[2]
    assert len(segment_karaoke.words) == 3
    kara_word1, kara_word2, kara_word3 = segment_karaoke.words
    assert kara_word1.text == "Kara"
    assert len(kara_word1.styles) == 1
    assert kara_word1.styles[0].tag_block == AssTagBlock(unknown_tags=["k20"])
    assert kara_word2.text == "oke"
    assert len(kara_word2.styles) == 1
    assert kara_word2.styles[0].tag_block == AssTagBlock(unknown_tags=["k40"])
    assert kara_word3.text == " test."
    assert len(kara_word3.styles) == 1
    assert kara_word3.styles[0].tag_block == AssTagBlock(unknown_tags=["k50"])


def test_parse_malformed_ass_gracefully(malformed_ass_content: str, caplog: LogCaptureFixture) -> None:
    """Test that the parser handles malformed lines by logging warnings and continuing."""
    subs = parse_ass(malformed_ass_content)

    assert len(subs.segments) == 1
    assert subs.segments[0].text == "This line is good."
    assert "Skipping Dialogue line found before Format line" in caplog.text
    assert "Skipping malformed ASS Dialogue line" in caplog.text


def test_parse_ass_skips_style_lines(caplog: LogCaptureFixture) -> None:
    """Test that an ASS Style line is now skipped with a warning."""
    content = "[V4+ Styles]\nStyle: Bad,Arial,20\nFormat: Name,Fontname,Fontsize\n"
    subs = parse_ass(content)
    assert not hasattr(subs, "styles")
    assert "Parsing of [V4+ Styles] is deprecated" in caplog.text


def test_parse_ass_handles_inverted_timestamps(caplog: LogCaptureFixture) -> None:
    """Test that an ASS Dialogue line with start > end is skipped with a warning."""
    content = (
        "[Events]\nFormat: Start, End, Text\n"
        "Dialogue: 0:00:02.00,0:00:01.00,Inverted timestamps\n"
        "Dialogue: 0:00:03.00,0:00:04.00,Valid timestamps"
    )
    subs = parse_ass(content)
    assert len(subs.segments) == 1
    assert subs.segments[0].text == "Valid timestamps"
    assert "Skipping ASS Dialogue with invalid timestamp (start > end)" in caplog.text


def test_parse_ass_missing_required_format_fields() -> None:
    """Test that a ValueError is raised if the Format line is missing key fields."""
    content = "[Events]\nFormat: Style, Name\nDialogue: Default,ActorName,Some Text"
    with pytest.raises(ValueError) as exc_info:
        parse_ass(content)

    error_message = str(exc_info.value)
    assert "is missing required fields" in error_message
    assert "'Start'" in error_message
    assert "'End'" in error_message
    assert "'Text'" in error_message
