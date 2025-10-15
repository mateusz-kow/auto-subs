import pytest

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: Full implementation not complete")
def test_ass_round_trip_preserves_data(complex_ass_content: str) -> None:
    """Test that loading and saving a complex ASS file results in a semantically identical file."""
    subs = parse_ass(complex_ass_content)
    output_text = to_ass(subs)

    # For a perfect round-trip, the output should be very close to the input.
    # Normalization (e.g., stripping comments, standardizing spacing) might be needed in the final implementation.
    # For now, we test for the presence of key structural and content elements.
    assert "[Script Info]" in output_text
    assert "Title: Complex Test" in output_text
    assert "Style: Highlight,Impact" in output_text
    assert "Mid-word st{\\i1}y{\\i0}le." in output_text
    assert "{\\k20}Kara{\\k40}oke{\\k50} test." in output_text


@pytest.mark.xfail(raises=NotImplementedError, reason="Phase 3: Full implementation not complete")
def test_ass_editing_integrity(complex_ass_content: str) -> None:
    """Test that programmatic edits correctly modify the object and the final output."""
    subs = parse_ass(complex_ass_content)

    # Find the karaoke segment and shift it forward by 10 seconds
    karaoke_segment = subs.segments[2]
    karaoke_segment.shift_by(10.0)

    # Regenerate the file content
    output_text = to_ass(subs)

    # The original line should NOT be in the output
    assert "0:00:15.00" not in output_text

    # The new, shifted line SHOULD be in the output
    new_start_str = "0:00:25.00"  # 15.0 + 10.0
    new_end_str = "0:00:28.00"  # 18.0 + 10.0
    expected_line = (
        f"Dialogue: 0,{new_start_str},{new_end_str},Default,,0,0,0,,{{\\k20}}Kara{{\\k40}}oke{{\\k50}} test."
    )
    assert expected_line in output_text
