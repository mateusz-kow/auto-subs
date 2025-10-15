from autosubs.core.generator import to_ass
from autosubs.models.styles.ass import AssStyle, WordStyleRange
from autosubs.models.subtitles.ass import (
    AssSubtitles,
    AssSubtitleSegment,
    AssSubtitleWord,
)


def test_generate_ass_from_basic_object() -> None:
    """Test that a basic AssSubtitles object is generated into a valid file string."""
    subs = AssSubtitles(
        script_info={"Title": "Generated", "ScriptType": "v4.00+"},
        styles=[AssStyle(Name="Default", Fontname="Arial", Fontsize=28)],
        segments=[
            AssSubtitleSegment(
                words=[AssSubtitleWord(text="Hello world.", start=1.0, end=3.5)],
                style_name="Default",
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


def test_generate_ass_reconstructs_inline_tags() -> None:
    """Test that the generator intelligently reconstructs dialogue text from styled words."""
    words = [
        AssSubtitleWord(text="Hel", start=1.0, end=1.2),
        AssSubtitleWord(
            text="lo",
            start=1.2,
            end=1.5,
            styles=[WordStyleRange(start_char_index=0, end_char_index=2, ass_tag="{\\i1}")],
        ),
        AssSubtitleWord(text=" ", start=1.5, end=1.6),
        AssSubtitleWord(
            text="world",
            start=1.6,
            end=2.0,
            styles=[WordStyleRange(start_char_index=0, end_char_index=5, ass_tag="{\\k40}")],
        ),
    ]
    segment = AssSubtitleSegment(words=words)
    subs = AssSubtitles(segments=[segment])

    result = to_ass(subs)
    expected_text = "Hel{\\i1}lo {\\k40}world"
    assert expected_text in result
