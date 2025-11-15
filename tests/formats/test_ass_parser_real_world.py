from pathlib import Path

import pytest

from autosubs.core.parser import parse_ass

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "ass"
ASS_FILES = sorted(FIXTURES_DIR.glob("sample*.ass"))
ASS_FILE_IDS = [p.name for p in ASS_FILES]


def test_parser_handles_multi_digit_hour_timestamps() -> None:
    """Test that the parser correctly handles hh:mm:ss.cs timestamps."""
    content = (
        "[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,00:00:01.50,00:00:02.50,Default,Hello world\n"
    )
    subs = parse_ass(content)

    assert len(subs.segments) == 1
    segment = subs.segments[0]
    assert segment.start == 1.5
    assert segment.end == 2.5
    assert segment.text == "Hello world"


@pytest.mark.parametrize("ass_file_path", ASS_FILES, ids=ASS_FILE_IDS)
def test_real_world_ass_files_parse_without_errors(ass_file_path: Path) -> None:
    """Tests that various real-world .ass files can be parsed without raising an exception."""
    content = ass_file_path.read_text(encoding="utf-8")
    subs = parse_ass(content)

    assert subs.script_info or subs.segments, f"File {ass_file_path.name} was parsed as completely empty."

    if subs.segments:
        assert subs.segments[0].text is not None
        assert subs.segments[0].start >= 0
        assert subs.segments[0].end >= subs.segments[0].start
