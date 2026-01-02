"""Tests for karaoke timing parsing utilities."""

import pytest

from autosubs.core.karaoke import KaraokeParser, Syllable, extract_syllables_from_segment
from autosubs.models.subtitles.ass import AssSubtitleSegment, AssSubtitleWord, AssTagBlock, WordStyleRange


def test_syllable_properties() -> None:
    """Test Syllable dataclass properties."""
    syllable = Syllable(text="hello", start=1.0, duration=50, tag_type="k")
    
    assert syllable.text == "hello"
    assert syllable.start == pytest.approx(1.0)
    assert syllable.duration == 50
    assert syllable.duration_seconds == pytest.approx(0.5)
    assert syllable.end == pytest.approx(1.5)
    assert syllable.tag_type == "k"


def test_karaoke_parser_basic() -> None:
    """Test parsing basic karaoke tags."""
    text = "{\\k50}Hel{\\k30}lo"
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 2
    assert syllables[0].text == "Hel"
    assert syllables[0].duration == 50
    assert syllables[0].start == pytest.approx(0.0)
    assert syllables[0].tag_type == "k"
    
    assert syllables[1].text == "lo"
    assert syllables[1].duration == 30
    assert syllables[1].start == pytest.approx(0.5)
    assert syllables[1].tag_type == "k"


def test_karaoke_parser_multiple_types() -> None:
    """Test parsing different karaoke tag types."""
    text = "{\\k50}test{\\kf30}ing{\\ko20}now{\\K40}here"
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 4
    assert syllables[0].tag_type == "k"
    assert syllables[1].tag_type == "kf"
    assert syllables[2].tag_type == "ko"
    assert syllables[3].tag_type == "K"


def test_karaoke_parser_zero_duration() -> None:
    """Test parsing karaoke tags with zero or omitted duration."""
    text = "{\\k0}test{\\k}ing"
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 2
    assert syllables[0].duration == 0
    assert syllables[1].duration == 0


def test_karaoke_parser_with_spaces() -> None:
    """Test parsing karaoke with spaces in text."""
    text = "{\\k50}Hel{\\k30}lo {\\k40}world"
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 3
    assert syllables[0].text == "Hel"
    assert syllables[1].text == "lo "
    assert syllables[2].text == "world"


def test_karaoke_parser_mixed_tags() -> None:
    """Test parsing text with karaoke and other ASS tags."""
    text = "{\\k50\\c&H00FF00&}Hel{\\k30}lo"
    syllables = KaraokeParser.parse_syllables(text)
    
    # Should extract syllables while ignoring non-karaoke tags
    assert len(syllables) == 2
    assert syllables[0].text == "Hel"
    assert syllables[1].text == "lo"


def test_karaoke_parser_no_tags() -> None:
    """Test parsing text without karaoke tags."""
    text = "Hello world"
    syllables = KaraokeParser.parse_syllables(text)
    
    # Text without karaoke tags should create a syllable with 0 duration
    assert len(syllables) == 1
    assert syllables[0].text == "Hello world"
    assert syllables[0].duration == 0


def test_karaoke_parser_empty_text() -> None:
    """Test parsing empty text."""
    text = ""
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 0


def test_has_karaoke_tags() -> None:
    """Test detection of karaoke tags in text."""
    assert KaraokeParser.has_karaoke_tags("{\\k50}test")
    assert KaraokeParser.has_karaoke_tags("{\\kf30}test")
    assert KaraokeParser.has_karaoke_tags("{\\ko20}test")
    assert KaraokeParser.has_karaoke_tags("{\\K40}test")
    assert not KaraokeParser.has_karaoke_tags("plain text")
    assert not KaraokeParser.has_karaoke_tags("{\\c&H00FF00&}colored")


def test_extract_syllables_from_segment_with_karaoke() -> None:
    """Test extracting syllables from segment with karaoke tags."""
    # Create a segment with karaoke tags in the word styles
    tag_block = AssTagBlock(unknown_tags=("k50",))
    word1 = AssSubtitleWord(text="Hel", start=1.0, end=1.5)
    word1.styles = [WordStyleRange(0, 3, tag_block)]
    
    tag_block2 = AssTagBlock(unknown_tags=("k30",))
    word2 = AssSubtitleWord(text="lo", start=1.5, end=1.8)
    word2.styles = [WordStyleRange(0, 2, tag_block2)]
    
    segment = AssSubtitleSegment(words=[word1, word2])
    
    syllables = extract_syllables_from_segment(segment)
    
    # Should extract syllables with absolute timing
    assert len(syllables) == 2
    assert syllables[0].text == "Hel"
    assert syllables[0].start == pytest.approx(1.0)  # segment.start + 0.0
    assert syllables[1].text == "lo"
    assert syllables[1].start == pytest.approx(1.5)  # segment.start + 0.5


def test_extract_syllables_from_segment_no_karaoke() -> None:
    """Test extracting syllables from segment without karaoke tags."""
    word = AssSubtitleWord(text="Hello", start=1.0, end=2.0)
    segment = AssSubtitleSegment(words=[word])
    
    syllables = extract_syllables_from_segment(segment)
    
    # Should return empty list when no karaoke tags present
    assert len(syllables) == 0


def test_karaoke_timing_accumulation() -> None:
    """Test that syllable timing accumulates correctly."""
    text = "{\\k10}a{\\k20}b{\\k30}c"
    syllables = KaraokeParser.parse_syllables(text)
    
    assert len(syllables) == 3
    assert syllables[0].start == pytest.approx(0.0)
    assert syllables[0].end == pytest.approx(0.1)
    
    assert syllables[1].start == pytest.approx(0.1)
    assert syllables[1].end == pytest.approx(0.3)
    
    assert syllables[2].start == pytest.approx(0.3)
    assert syllables[2].end == pytest.approx(0.6)
