import pytest

from autosubs.core.generator import to_ass
from autosubs.models.styles.ass import AssStyle, WordStyleRange
from autosubs.models.subtitles import SubtitleWord
from autosubs.models.subtitles.ass import AssSubtitles, AssSubtitleSegment


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS generator not implemented")
def test_generate_ass_from_basic_object() -> None:
    """Test that a basic AssSubtitles object is generated into a valid file string."""
    subs = AssSubtitles(
        script_info={"Title": "Generated", "ScriptType": "v4.00+"},
        styles=[AssStyle(name="Default", font_name="Arial", font_size=28)],
        segments=[
            AssSubtitleSegment(
                start=1.0, end=3.5, style_name="Default", words=[SubtitleWord(text="Hello world.", start=1.0, end=3.5)]
            )
        ],
    )

    result = to_ass(subs)

    assert "[Script Info]" in result
    assert "Title: Generated" in result
    assert "[V4+ Styles]" in result
    assert "Style: Default,Arial,28" in result
    assert "[Events]" in result
    assert "Dialogue: 0,0:00:01.00,0:00:03.50,Default,,0,0,0,,Hello world." in result


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: ASS generator not implemented")
def test_generate_ass_reconstructs_inline_tags() -> None:
    """Test that the generator intelligently reconstructs dialogue text from styled words."""
    words = [
        SubtitleWord(text="Hel", start=1.0, end=1.2),
        SubtitleWord(
            text="lo",
            start=1.2,
            end=1.5,
            styles=[WordStyleRange(start_char_index=0, end_char_index=2, ass_tag="{\\i1}")],
        ),
        SubtitleWord(text=" ", start=1.5, end=1.6),
        SubtitleWord(
            text="world",
            start=1.6,
            end=2.0,
            styles=[WordStyleRange(start_char_index=0, end_char_index=5, ass_tag="{\\k40}")],
        ),
    ]
    segment = AssSubtitleSegment(start=1.0, end=2.0, words=words)
    subs = AssSubtitles(segments=[segment])

    result = to_ass(subs)
    expected_text = "Hel{\\i1}lo {\\k40}world"
    assert expected_text in result
