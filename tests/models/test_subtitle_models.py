import logging

import pytest
from _pytest.logging import LogCaptureFixture

from autosubs.core.builder import create_dict_from_subtitles
from autosubs.models import AssSubtitles
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


def test_subtitle_word_validation() -> None:
    """Test SubtitleWord timestamp validation."""
    word = SubtitleWord(text="test", start=1.0, end=2.0)
    assert word.text == "test"
    with pytest.raises(ValueError, match="has invalid timestamp"):
        SubtitleWord(text="invalid", start=2.0, end=1.0)


def test_subtitle_segment_properties_and_validation() -> None:
    """Test SubtitleSegment properties and validations."""
    word1 = SubtitleWord(text="Hello", start=0.5, end=1.0)
    word2 = SubtitleWord(text="world.", start=1.1, end=1.5)

    segment = SubtitleSegment(words=[word1, word2])
    assert segment.start == pytest.approx(0.5)
    assert segment.end == pytest.approx(1.5)
    assert segment.text == "Hello world."

    empty_segment = SubtitleSegment(words=[])
    assert empty_segment.start == pytest.approx(0.0)
    assert empty_segment.end == pytest.approx(0.0)

    with pytest.raises(ValueError, match="has invalid timestamp"):
        word3 = SubtitleWord(text="invalid", start=2.0, end=1.9)
        SubtitleSegment(words=[word3])


def test_subtitles_sorting_and_overlap_warning(caplog: LogCaptureFixture) -> None:
    """Test that Subtitles automatically sorts segments and warns on overlap."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="B", start=2.0, end=3.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="A", start=0.0, end=1.0)])
    seg3 = SubtitleSegment(words=[SubtitleWord(text="Overlap", start=2.5, end=3.5)])

    with caplog.at_level(logging.WARNING):
        subtitles = Subtitles(segments=[seg1, seg2, seg3])

    assert subtitles.segments[0] is seg2
    assert subtitles.segments[1] is seg1
    assert subtitles.segments[2] is seg3

    assert len(caplog.records) == 1
    assert "Overlap detected" in caplog.text
    assert "ending at 3.000s overlaps with segment starting at 2.500s" in caplog.text


def test_subtitles_to_transcription_dict() -> None:
    """Test conversion of a Subtitles object back to a transcription dictionary."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="First.", start=0.0, end=1.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Second.", start=2.0, end=3.0)])
    subtitles = Subtitles(segments=[seg1, seg2])

    result = create_dict_from_subtitles(subtitles)

    assert result["language"] == "unknown"
    assert result["text"] == "First.\nSecond."
    assert len(result["segments"]) == 2
    assert result["segments"][0]["id"] == 1
    assert result["segments"][0]["text"] == "First."
    assert result["segments"][0]["words"][0]["word"] == "First."


def test_subtitles_string_representation() -> None:
    """Test the __str__ method of the Subtitles object."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="First line.", start=0.0, end=1.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Second line.", start=2.0, end=3.0)])
    subtitles = Subtitles(segments=[seg1, seg2])
    assert str(subtitles.text) == "First line.\nSecond line."


def test_subtitle_segment_boundary_calculation() -> None:
    """Test that segments correctly calculate start and end from words."""
    words = [
        SubtitleWord(text="First", start=1.0, end=2.0),
        SubtitleWord(text="Last", start=3.0, end=4.0),
    ]
    segment = SubtitleSegment(words=words)

    assert segment.start == pytest.approx(1.0)
    assert segment.end == pytest.approx(4.0)


def test_subtitle_segment_add_word() -> None:
    """Test adding a word to an existing segment."""
    segment = SubtitleSegment(words=[SubtitleWord(text="Existing", start=2.0, end=3.0)])
    segment.add_word(SubtitleWord(text="New", start=1.0, end=1.5))

    assert segment.start == pytest.approx(1.0)
    assert segment.end == pytest.approx(3.0)
    assert segment.words[0].text == "New"


def test_subtitles_sorting() -> None:
    """Test that Subtitles object sorts segments by start time."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="Later", start=5.0, end=6.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Earlier", start=1.0, end=2.0)])
    subs = Subtitles(segments=[seg1, seg2])

    assert subs.segments[0].start == pytest.approx(1.0)
    assert subs.segments[1].start == pytest.approx(5.0)


def test_subtitles_text_property() -> None:
    """Test that Subtitles.text correctly joins segment text with newlines."""
    seg1 = SubtitleSegment(words=[SubtitleWord(text="Line 1", start=1.0, end=2.0)])
    seg2 = SubtitleSegment(words=[SubtitleWord(text="Line 2", start=3.0, end=4.0)])
    subs = Subtitles(segments=[seg1, seg2])

    assert subs.text == "Line 1\nLine 2"


def test_subtitles_concatenation_logic() -> None:
    """Test that concatenation merges segments and applies offsets correctly."""
    s1 = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("Part1", 0.0, 5.0)])])
    s2 = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("Part2", 0.0, 5.0)])])

    # Joining CD1 and CD2 where CD1 is 10s long
    result = s1.concatenate(s2, offset=10.0)

    assert len(result.segments) == 2
    assert result.segments[0].start == 0.0
    assert result.segments[1].start == 10.0
    assert result.segments[1].end == 15.0


def test_mixed_type_concatenation() -> None:
    """Verify behavior when mixing Subtitles and AssSubtitles."""
    base = Subtitles(segments=[])
    ass = AssSubtitles(segments=[], script_info={"Title": "Test"})

    # Subtitles + AssSubtitles = Subtitles (Metadata lost)
    res1 = base + ass
    assert type(res1) is Subtitles

    # AssSubtitles + Subtitles = AssSubtitles (Metadata preserved)
    res2 = ass + base
    assert isinstance(res2, AssSubtitles)
    assert res2.script_info["Title"] == "Test"


def test_concatenation_immutability() -> None:
    """Ensure the original subtitle objects are not modified."""
    s1 = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("A", 0, 1)])])
    s2 = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord("B", 0, 1)])])

    _ = s1.concatenate(s2, offset=100.0)

    # s2 should still start at 0
    assert s2.segments[0].start == 0.0


def test_ass_subtitles_concatenation_metadata_winner() -> None:
    """Ensure that metadata from the first AssSubtitles operand is preserved."""
    s1 = AssSubtitles(
        segments=[], script_info={"PlayResX": "1920", "Title": "Original"}, custom_sections={"[Fonts]": ["Arial.ttf"]}
    )
    s2 = AssSubtitles(
        segments=[], script_info={"PlayResX": "1280", "Title": "Other"}, custom_sections={"[Fonts]": ["Impact.ttf"]}
    )

    result = s1 + s2

    assert isinstance(result, AssSubtitles)
    # Metadata from s1 must win
    assert result.script_info["PlayResX"] == "1920"
    assert result.script_info["Title"] == "Original"
    assert result.custom_sections["[Fonts]"] == ["Arial.ttf"]


def test_ass_subtitles_style_merging() -> None:
    """Verify that concatenation merges unique styles from both operands."""
    s1 = AssSubtitles(
        segments=[], styles=[{"Name": "Default", "Fontsize": "48"}], style_format_keys=["Name", "Fontsize"]
    )
    s2 = AssSubtitles(
        segments=[],
        styles=[
            {"Name": "Default", "Fontsize": "60"},  # Collision
            {"Name": "Fancy", "Fontsize": "72"},  # New
        ],
    )

    result = s1 + s2

    assert isinstance(result, AssSubtitles)
    assert len(result.styles) == 2
    # s1's version of "Default" must win
    assert any(s["Name"] == "Default" and s["Fontsize"] == "48" for s in result.styles)
    # "Fancy" must be added
    assert any(s["Name"] == "Fancy" for s in result.styles)
