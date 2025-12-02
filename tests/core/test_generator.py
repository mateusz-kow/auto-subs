import pytest

from autosubs.core import generator
from autosubs.core.generator import to_ass
from autosubs.core.styler import AssStyler
from autosubs.models import SubtitleWord
from autosubs.models.styles.domain import StyleEngineConfig
from autosubs.models.subtitles import AssSubtitles, AssSubtitleSegment, AssSubtitleWord, Subtitles, SubtitleSegment


@pytest.fixture
def sample_subtitles() -> Subtitles:
    """Provides a sample Subtitles object for testing."""
    words1 = [
        SubtitleWord("Hello", 0.5, 1.0),
        SubtitleWord("world.", 1.1, 1.5),
    ]
    words2 = [
        SubtitleWord("This", 2.0, 2.2),
        SubtitleWord("is", 2.3, 2.4),
        SubtitleWord("a", 2.5, 2.6),
        SubtitleWord("test.", 2.7, 3.0),
    ]
    segment1 = SubtitleSegment(words1)
    segment2 = SubtitleSegment(words2)
    return Subtitles([segment1, segment2])


@pytest.fixture
def empty_subtitles() -> Subtitles:
    """Provides an empty Subtitles object for testing."""
    return Subtitles([])


@pytest.fixture
def default_styler_engine() -> AssStyler:
    """Provides a StylerEngine with a minimal default configuration."""
    config = StyleEngineConfig(
        script_info={"Title": "Default"},
        styles=[{"Name": "Default", "Fontname": "Arial", "Fontsize": 48}],
        rules=[],
        effects={},
    )
    return AssStyler(config)


def test_to_srt(sample_subtitles: Subtitles) -> None:
    """Test SRT generation."""
    expected_srt = (
        "1\n00:00:00,500 --> 00:00:01,500\nHello world.\n\n2\n00:00:02,000 --> 00:00:03,000\nThis is a test.\n\n"
    )
    assert generator.to_srt(sample_subtitles) == expected_srt


def test_to_ass(sample_subtitles: Subtitles, default_styler_engine: AssStyler) -> None:
    """Test ASS generation."""
    result = generator.to_ass(sample_subtitles, styler_engine=default_styler_engine)
    assert "[Script Info]" in result
    assert "Title: Default" in result
    assert "Dialogue: 0,0:00:00.50,0:00:01.50,Default,,0,0,0,,Hello world." in result
    assert "Dialogue: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,This is a test." in result


def test_to_ass_requires_styler_engine() -> None:
    """Test that generating ASS from scratch without a styler engine raises an error."""
    with pytest.raises(ValueError, match="AssStyler is required"):
        generator.to_ass(Subtitles(segments=[]))  # type: ignore[call-overload]


def test_format_srt_timestamp() -> None:
    """Test SRT timestamp formatting."""
    assert generator.format_srt_timestamp(0) == "00:00:00,000"
    assert generator.format_srt_timestamp(61.525) == "00:01:01,525"
    assert generator.format_srt_timestamp(3661.0) == "01:01:01,000"


def test_format_ass_timestamp() -> None:
    """Test ASS timestamp formatting."""
    assert generator.format_ass_timestamp(0) == "0:00:00.00"
    assert generator.format_ass_timestamp(61.525) == "0:01:01.52"
    assert generator.format_ass_timestamp(3661.0) == "1:01:01.00"


def test_to_vtt_empty(empty_subtitles: Subtitles) -> None:
    """Test that generating a VTT from empty subtitles returns only the header."""
    assert generator.to_vtt(empty_subtitles) == "WEBVTT\n"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5.0, "5"),
        (True, "-1"),
        (False, "0"),
        (5.3, "5.3"),
        ("text", "text"),
        (100, "100"),
    ],
)
def test_format_ass_number(value: object, expected: str) -> None:
    """Test the _format_ass_number helper for various types."""
    assert generator._format_ass_number(value) == expected


def test_to_ass_generates_v4_styles_from_styler_engine(sample_subtitles: Subtitles) -> None:
    """Test that [V4+ Styles] are correctly generated from a styler engine config."""
    config = StyleEngineConfig(
        script_info={},
        styles=[
            {"Name": "Default", "Fontname": "Arial", "Bold": True},
            {"Name": "Highlight", "Fontname": "Impact", "Bold": False},
        ],
    )
    styler_engine = AssStyler(config)
    result = generator.to_ass(sample_subtitles, styler_engine=styler_engine)
    assert "Format: Name, Fontname, Bold" in result
    assert "Style: Default,Arial,-1" in result
    assert "Style: Highlight,Impact,0" in result


def test_to_ass_regenerate_uses_default_events_format_keys() -> None:
    """Test that regenerating an ASS file falls back to default event keys if they are missing."""
    segment = AssSubtitleSegment(words=[AssSubtitleWord("test", 1.0, 2.0)])
    subs = AssSubtitles(segments=[segment])
    subs.events_format_keys = []  # Explicitly clear the keys

    result = to_ass(subs)

    expected_format = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    assert expected_format in result
