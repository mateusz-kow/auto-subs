from autosubs.models import AssSubtitleSegment, AssSubtitleWord, SubtitleSegment, SubtitleWord


def test_ass_subtitle_segment_from_generic() -> None:
    """Test converting a generic SubtitleSegment to an AssSubtitleSegment."""
    generic_words = [
        SubtitleWord(text="Hello", start=1.0, end=1.5),
        SubtitleWord(text="world", start=1.6, end=2.0),
    ]
    generic_segment = SubtitleSegment(words=generic_words)

    ass_segment = AssSubtitleSegment.from_generic(generic_segment)

    assert isinstance(ass_segment, AssSubtitleSegment)
    assert len(ass_segment.words) == 2
    assert all(isinstance(w, AssSubtitleWord) for w in ass_segment.words)
    assert ass_segment.text == "Hello world"
    assert ass_segment.start == 1.0
    assert ass_segment.end == 2.0


def test_ass_subtitle_segment_text_override() -> None:
    """Test that the text_override property correctly overrides the generated text."""
    words = [AssSubtitleWord(text="Original", start=0.0, end=1.0)]
    segment = AssSubtitleSegment(words=words)

    assert segment.text == "Original"

    segment.text_override = "This has been overridden."
    assert segment.text == "This has been overridden."
