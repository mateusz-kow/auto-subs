from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_ass_round_trip_preserves_data(complex_ass_content: str) -> None:
    """Test that loading and saving a complex ASS file results in a semantically identical file."""
    subs = parse_ass(complex_ass_content)
    output_text = to_ass(subs)

    assert "[Script Info]" in output_text
    assert "Title: Complex Test" in output_text
    assert "Mid-word st{\\i1}y{\\i0}le." in output_text
    assert "{\\k20}Kara{\\k40}oke{\\k50} test." in output_text


def test_ass_editing_integrity(complex_ass_content: str) -> None:
    """Test that programmatic edits correctly modify the object and the final output."""
    subs = parse_ass(complex_ass_content)

    karaoke_segment = subs.segments[2]
    karaoke_segment.shift_by(10.0)

    output_text = to_ass(subs)

    assert "0:00:15.00" not in output_text

    new_start_str = "0:00:25.00"
    new_end_str = "0:00:28.00"
    expected_line = (
        f"Dialogue: 0,{new_start_str},{new_end_str},Default,,0,0,0,,{{\\k20}}Kara{{\\k40}}oke{{\\k50}} test."
    )
    assert expected_line in output_text
