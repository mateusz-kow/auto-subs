from autosubs.core.generator import to_ass
from autosubs.core.parser import parse_ass


def test_generate_sample_ass_fixture(sample_ass_content: str) -> None:
    """Test round-trip generation of the primary sample.ass fixture."""
    subs = parse_ass(sample_ass_content)
    generated_content = to_ass(subs)

    assert "Dialogue: 0,0:00:00.50,0:00:01.50,Default,,0,0,0,,Hello world." in generated_content
    assert (
        "Dialogue: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,This is a test with {\\b1}bold{\\b0} tags."
        in generated_content
    )
    assert "Dialogue: 0,0:00:04.10,0:00:05.90,Default,,0,0,0,,And a\\Nnew line." in generated_content


def test_generate_sample2_ass_fixture(sample2_ass_content: str) -> None:
    """Test round-trip generation of sample2.ass, focusing on pos tags."""
    subs = parse_ass(sample2_ass_content)
    generated_content = to_ass(subs)

    assert "{\\pos(20,20)}To split audio stream" in generated_content
    # The original file has many \N, which are parsed and then reconstructed.
    # We check for a key part of the reconstructed content.
    assert "{\\pos(40,160)}#! /bin/sh\\Nifn=" in generated_content
    assert "{\\pos(20,550)}(Note: Uploaded video is of `div2'.)" in generated_content


def test_generate_complex_ass_fixture(complex_ass_content: str) -> None:
    """Test round-trip generation of complex.ass, focusing on mixed inline tags."""
    subs = parse_ass(complex_ass_content)
    generated_content = to_ass(subs)

    assert "Dialogue: 0,0:00:05.10,0:00:08.50,Default,,0,0,0,,This line has {\\b1}bold{\\b0} text." in generated_content
    assert (
        "Dialogue: 1,0:00:10.00,0:00:12.00,Highlight,ActorName,10,10,10,Banner;Text banner,Mid-word st{\\i1}y{\\i0}le."
        in generated_content
    )
    assert "Dialogue: 0,0:00:15.00,0:00:18.00,Default,,0,0,0,,{\\k20}Kara{\\k40}oke{\\k50} test." in generated_content
