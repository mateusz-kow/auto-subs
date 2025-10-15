import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core.parser import parse_ass
from autosubs.models.ass import AssSubtitles, AssSubtitleSegment
from autosubs.models.ass_styles import AssStyle, WordStyleRange


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS parser not implemented")
def test_parse_ass_structure(simple_ass_content: str) -> None:
    """Test that the basic structure of an ASS file is parsed correctly."""
    subs = parse_ass(simple_ass_content)

    assert isinstance(subs, AssSubtitles)
    assert subs.script_info["Title"] == "Test Script"
    assert len(subs.styles) == 1
    assert isinstance(subs.styles[0], AssStyle)
    assert subs.styles[0].name == "Default"
    assert subs.styles[0].font_name == "Arial"
    assert subs.styles[0].font_size == 48.0


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS parser not implemented")
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


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS parser not implemented")
def test_parse_ass_word_and_style_parsing(complex_ass_content: str) -> None:
    """Test the detailed parsing of inline style tags into WordStyleRange objects."""
    subs = parse_ass(complex_ass_content)

    # Test case 1: Mid-word styling: "st{\i1}y{\i0}le."
    segment = subs.segments[1]
    assert segment.actor_name == "ActorName"
    assert segment.effect == "Banner;Text banner"

    # Expecting "st", "y", "le." to be three separate words
    word1, word2, word3 = segment.words[2], segment.words[3], segment.words[4]
    assert word1.text == "st"
    assert word2.text == "y"
    assert word3.text == "le."
    assert not word1.styles
    assert word2.styles == [WordStyleRange(start_char_index=0, end_char_index=1, ass_tag="{\\i1}")]
    assert word3.styles == [WordStyleRange(start_char_index=0, end_char_index=3, ass_tag="{\\i0}")]

    # Test case 2: Karaoke tags: "{\k20}Kara{\k40}oke{\k50} test."
    segment_karaoke = subs.segments[2]
    kara_word1, kara_word2, kara_word3 = segment_karaoke.words[0], segment_karaoke.words[1], segment_karaoke.words[2]
    assert kara_word1.text == "Kara"
    assert kara_word1.styles == [WordStyleRange(start_char_index=0, end_char_index=4, ass_tag="{\\k20}")]
    assert kara_word2.text == "oke"
    assert kara_word2.styles == [WordStyleRange(start_char_index=0, end_char_index=3, ass_tag="{\\k40}")]
    assert kara_word3.text == "test."
    assert kara_word3.styles == [WordStyleRange(start_char_index=0, end_char_index=5, ass_tag="{\\k50}")]


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS parser not implemented")
def test_parse_malformed_ass_gracefully(malformed_ass_content: str, caplog: LogCaptureFixture) -> None:
    """Test that the parser handles malformed lines by logging warnings and continuing."""
    subs = parse_ass(malformed_ass_content)

    # Should skip the line before "Format" and the line with a bad timestamp
    assert len(subs.segments) == 1
    assert subs.segments[0].text == "This line is good."
    assert "Skipping Dialogue line found before Format line" in caplog.text
    assert "Skipping malformed ASS Dialogue line" in caplog.text
