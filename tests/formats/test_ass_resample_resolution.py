"""Tests for ASS resolution resampling functionality."""

import pytest

from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_resample_resolution_basic() -> None:
    """Test basic resolution resampling from 720p to 1080p."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Name, MarginL, MarginR, MarginV, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,NTP,10,20,5,{\pos(640,360)}{\fs48}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check script info updated
    assert subs.script_info["PlayResX"] == "1920"
    assert subs.script_info["PlayResY"] == "1080"

    # Check margins scaled (1.5x horizontal, 1.5x vertical)
    seg = subs.segments[0]
    assert seg.margin_l == 15  # 10 * 1.5
    assert seg.margin_r == 30  # 20 * 1.5
    assert seg.margin_v == 7  # 5 * 1.5 = 7.5 -> 7

    # Check position scaled
    style = seg.words[0].styles[0].tag_block
    assert style.position_x == pytest.approx(960.0)  # 640 * 1.5
    assert style.position_y == pytest.approx(540.0)  # 360 * 1.5

    # Check font size scaled
    assert style.font_size == pytest.approx(72.0)  # 48 * 1.5


def test_resample_resolution_with_move() -> None:
    r"""Test resampling with \move tags."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\move(60,100,150,250,0,5000)}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check move coordinates scaled
    style = subs.segments[0].words[0].styles[0].tag_block
    assert style.move_x1 == pytest.approx(90.0)  # 60 * 1.5
    assert style.move_y1 == pytest.approx(150.0)  # 100 * 1.5
    assert style.move_x2 == pytest.approx(225.0)  # 150 * 1.5
    assert style.move_y2 == pytest.approx(375.0)  # 250 * 1.5
    # Time values should not change
    assert style.move_t1 == 0
    assert style.move_t2 == 5000


def test_resample_resolution_with_org() -> None:
    r"""Test resampling with \org (origin) tags."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\org(320,180)}{\frz45}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check origin coordinates scaled
    style = subs.segments[0].words[0].styles[0].tag_block
    assert style.origin_x == pytest.approx(480.0)  # 320 * 1.5
    assert style.origin_y == pytest.approx(270.0)  # 180 * 1.5
    # Rotation should not change
    assert style.rotation_z == pytest.approx(45.0)


def test_resample_resolution_with_border_shadow_blur() -> None:
    """Test resampling with border, shadow, and blur effects."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\bord2}{\shad1}{\blur0.5}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check effects scaled by Y factor
    style = subs.segments[0].words[0].styles[0].tag_block
    assert style.border == pytest.approx(3.0)  # 2 * 1.5
    assert style.shadow == pytest.approx(1.5)  # 1 * 1.5
    assert style.blur == pytest.approx(0.75)  # 0.5 * 1.5


def test_resample_resolution_downscale() -> None:
    """Test resampling with downscaling (1080p to 720p)."""
    content = r"""[Script Info]
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,72

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\pos(960,540)}{\fs72}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1280, 720)

    # Check script info updated
    assert subs.script_info["PlayResX"] == "1280"
    assert subs.script_info["PlayResY"] == "720"

    # Check values scaled down (2/3)
    style = subs.segments[0].words[0].styles[0].tag_block
    assert style.position_x == pytest.approx(640.0)  # 960 * (2/3)
    assert style.position_y == pytest.approx(360.0)  # 540 * (2/3)
    assert style.font_size == pytest.approx(48.0)  # 72 * (2/3)


def test_resample_resolution_to_4k() -> None:
    """Test resampling from 1080p to 4K (3840x2160)."""
    content = r"""[Script Info]
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\pos(960,540)}{\fs48}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(3840, 2160)

    # Check values scaled by 2x
    assert subs.script_info["PlayResX"] == "3840"
    assert subs.script_info["PlayResY"] == "2160"

    style = subs.segments[0].words[0].styles[0].tag_block
    assert style.position_x == pytest.approx(1920.0)  # 960 * 2
    assert style.position_y == pytest.approx(1080.0)  # 540 * 2
    assert style.font_size == pytest.approx(96.0)  # 48 * 2


def test_resample_resolution_missing_playres_raises_error() -> None:
    """Test that resampling fails if PlayResX/PlayResY are missing."""
    content = r"""[Script Info]
Title: Test

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,Test
"""

    subs = parse_ass(content)

    with pytest.raises(ValueError, match="PlayResX and PlayResY must be set"):
        subs.resample_resolution(1920, 1080)


def test_resample_resolution_round_trip() -> None:
    """Test that resampled content can be serialized and parsed again."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Name, MarginL, MarginR, MarginV, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,NTP,10,20,5,{\pos(640,360)}{\fs48}{\bord2}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Serialize to string
    output = to_ass(subs)

    # Verify output contains scaled values
    assert "PlayResX: 1920" in output
    assert "PlayResY: 1080" in output
    assert r"{\pos(960,540)\fs72\bord3}" in output

    # Parse again and verify
    subs2 = parse_ass(output)
    assert subs2.script_info["PlayResX"] == "1920"
    assert subs2.script_info["PlayResY"] == "1080"

    style = subs2.segments[0].words[0].styles[0].tag_block
    assert style.position_x == pytest.approx(960.0)
    assert style.position_y == pytest.approx(540.0)
    assert style.font_size == pytest.approx(72.0)
    assert style.border == pytest.approx(3.0)


def test_resample_resolution_preserves_non_coordinate_tags() -> None:
    """Test that non-coordinate tags (colors, rotation, etc.) are preserved."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\pos(640,360)}{\c&HFF0000&}{\frz45}{\b1}Test
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    style = subs.segments[0].words[0].styles[0].tag_block
    # Position should be scaled
    assert style.position_x == pytest.approx(960.0)
    assert style.position_y == pytest.approx(540.0)
    # But color, rotation, and bold should be unchanged
    assert style.primary_color == "&HFF0000&"
    assert style.rotation_z == pytest.approx(45.0)
    assert style.bold is True


def test_resample_resolution_with_multiple_segments() -> None:
    """Test resampling with multiple dialogue lines."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Name, MarginL, MarginR, MarginV, Text
Dialogue: 00:00:00.00,00:00:05.00,Default,NTP,10,20,5,{\pos(100,100)}Line 1
Dialogue: 00:00:05.00,00:00:10.00,Default,NTP,20,30,10,{\pos(200,200)}Line 2
Dialogue: 00:00:10.00,00:00:15.00,Default,NTP,30,40,15,{\pos(300,300)}Line 3
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check all segments are scaled correctly
    for i, (expected_l, expected_r, expected_v, expected_x, expected_y) in enumerate(
        [
            (15, 30, 7, 150.0, 150.0),
            (30, 45, 15, 300.0, 300.0),
            (45, 60, 22, 450.0, 450.0),
        ]
    ):
        seg = subs.segments[i]
        assert seg.margin_l == expected_l
        assert seg.margin_r == expected_r
        assert seg.margin_v == expected_v

        style = seg.words[0].styles[0].tag_block
        assert style.position_x == pytest.approx(expected_x)
        assert style.position_y == pytest.approx(expected_y)


def test_resample_resolution_real_world_sample9(sample9_ass_content: str) -> None:
    """Test resampling with real-world sample9.ass which has move tags."""
    subs = parse_ass(sample9_ass_content)

    # Original resolution is 1280x720
    assert subs.script_info["PlayResX"] == "1280"
    assert subs.script_info["PlayResY"] == "720"

    # Check original move tag values (from line 16: Dialogue 00:00:40.00-00:00:50.00)
    seg_with_move = subs.segments[4]  # 5th dialogue line
    move_tag = seg_with_move.words[0].styles[0].tag_block
    assert move_tag.move_x1 == pytest.approx(60.0)
    assert move_tag.move_y1 == pytest.approx(100.0)
    assert move_tag.move_x2 == pytest.approx(150.0)
    assert move_tag.move_y2 == pytest.approx(250.0)
    assert move_tag.move_t1 == 0
    assert move_tag.move_t2 == 5000

    # Resample to 1080p
    subs.resample_resolution(1920, 1080)

    assert subs.script_info["PlayResX"] == "1920"
    assert subs.script_info["PlayResY"] == "1080"

    # Check scaled move tag (1.5x horizontal, 1.5x vertical)
    move_tag = subs.segments[4].words[0].styles[0].tag_block
    assert move_tag.move_x1 == pytest.approx(90.0)  # 60 * 1.5
    assert move_tag.move_y1 == pytest.approx(150.0)  # 100 * 1.5
    assert move_tag.move_x2 == pytest.approx(225.0)  # 150 * 1.5
    assert move_tag.move_y2 == pytest.approx(375.0)  # 250 * 1.5
    # Time values should remain unchanged
    assert move_tag.move_t1 == 0
    assert move_tag.move_t2 == 5000

    # Check pos tag is also scaled (from line 12: first dialogue)
    pos_tag = subs.segments[0].words[0].styles[0].tag_block
    assert pos_tag.position_x == pytest.approx(90.0)  # 60 * 1.5
    assert pos_tag.position_y == pytest.approx(150.0)  # 100 * 1.5


def test_resample_resolution_real_world_sample2(sample2_ass_content: str) -> None:
    """Test resampling with real-world sample2.ass which has pos tags and margins."""
    subs = parse_ass(sample2_ass_content)

    # Original resolution (only PlayResY is set, PlayResX is missing)
    # This should fail because PlayResX is not set
    with pytest.raises(ValueError, match="PlayResX and PlayResY must be set"):
        subs.resample_resolution(1920, 1080)


def test_resample_resolution_move_tag_without_time() -> None:
    """Test resampling move tags without time parameters."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:10.00,Default,{\move(100,200,300,400)}Test without time
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check move tag scaled correctly
    move_tag = subs.segments[0].words[0].styles[0].tag_block
    assert move_tag.move_x1 == pytest.approx(150.0)  # 100 * 1.5
    assert move_tag.move_y1 == pytest.approx(300.0)  # 200 * 1.5
    assert move_tag.move_x2 == pytest.approx(450.0)  # 300 * 1.5
    assert move_tag.move_y2 == pytest.approx(600.0)  # 400 * 1.5
    # Time values should be None
    assert move_tag.move_t1 is None
    assert move_tag.move_t2 is None


def test_resample_resolution_multiple_move_tags() -> None:
    """Test resampling with multiple move tags in the same file."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:05.00,Default,{\move(0,0,1280,720,0,5000)}Diagonal move
Dialogue: 00:00:05.00,00:00:10.00,Default,{\move(640,0,640,720)}Vertical move
Dialogue: 00:00:10.00,00:00:15.00,Default,{\move(0,360,1280,360,1000,4000)}Horizontal move with time
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Check first move (diagonal)
    move1 = subs.segments[0].words[0].styles[0].tag_block
    assert move1.move_x1 == pytest.approx(0.0)
    assert move1.move_y1 == pytest.approx(0.0)
    assert move1.move_x2 == pytest.approx(1920.0)  # 1280 * 1.5
    assert move1.move_y2 == pytest.approx(1080.0)  # 720 * 1.5

    # Check second move (vertical)
    move2 = subs.segments[1].words[0].styles[0].tag_block
    assert move2.move_x1 == pytest.approx(960.0)  # 640 * 1.5
    assert move2.move_y1 == pytest.approx(0.0)
    assert move2.move_x2 == pytest.approx(960.0)  # 640 * 1.5
    assert move2.move_y2 == pytest.approx(1080.0)  # 720 * 1.5

    # Check third move (horizontal with time)
    move3 = subs.segments[2].words[0].styles[0].tag_block
    assert move3.move_x1 == pytest.approx(0.0)
    assert move3.move_y1 == pytest.approx(540.0)  # 360 * 1.5
    assert move3.move_x2 == pytest.approx(1920.0)  # 1280 * 1.5
    assert move3.move_y2 == pytest.approx(540.0)  # 360 * 1.5
    assert move3.move_t1 == 1000
    assert move3.move_t2 == 4000


def test_resample_resolution_combined_pos_and_move() -> None:
    """Test resampling when both pos and move tags are present."""
    content = r"""[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,48

[Events]
Format: Start, End, Style, Text
Dialogue: 00:00:00.00,00:00:05.00,Default,{\pos(640,360)}{\move(100,100,200,200,0,2000)}Combined tags
"""

    subs = parse_ass(content)
    subs.resample_resolution(1920, 1080)

    # Both pos and move should be scaled
    tag = subs.segments[0].words[0].styles[0].tag_block
    assert tag.position_x == pytest.approx(960.0)  # 640 * 1.5
    assert tag.position_y == pytest.approx(540.0)  # 360 * 1.5
    assert tag.move_x1 == pytest.approx(150.0)  # 100 * 1.5
    assert tag.move_y1 == pytest.approx(150.0)  # 100 * 1.5
    assert tag.move_x2 == pytest.approx(300.0)  # 200 * 1.5
    assert tag.move_y2 == pytest.approx(300.0)  # 200 * 1.5
