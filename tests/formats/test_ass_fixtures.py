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

    assert "Style: Code,monospace,20," in generated_content
    assert "{\\pos(20,20)}To split audio stream" in generated_content
    assert "{\\pos(40,160)}#! /bin/sh\\Nifn=" in generated_content
    assert "{\\pos(20,550)}(Note: Uploaded video is of `div2'.)" in generated_content


def test_generate_sample3_ass_fixture(sample3_ass_content: str) -> None:
    """Test round-trip generation of sample3.ass, focusing on font styles."""
    subs = parse_ass(sample3_ass_content)
    generated_content = to_ass(subs)

    assert "Style: F1,impact,70," in generated_content
    assert "Style: F9,segoe print bold,80," in generated_content
    assert "Dialogue: 0:01:20.00,0:01:30.00,F9,{\\pos(260,320)}The quick brown fox" in generated_content


def test_generate_sample4_ass_fixture(sample4_ass_content: str) -> None:
    """Test round-trip generation of sample4.ass, focusing on alignment styles."""
    subs = parse_ass(sample4_ass_content)
    generated_content = to_ass(subs)

    assert "Style: A1,Arial,34,&H3030FF,1,0" in generated_content
    assert "Style: A9,Arial,34,&H3030FF,9,0" in generated_content
    assert "Dialogue: 0:01:20.00,0:01:30.00,A9,{\\pos(600,400)}The quick brown fox" in generated_content


def test_generate_sample5_ass_fixture(sample5_ass_content: str) -> None:
    """Test round-trip generation of sample5.ass, focusing on border and shadow styles."""
    subs = parse_ass(sample5_ass_content)
    generated_content = to_ass(subs)

    assert "Style: S10,Arial,70,&HFFFFFF,&HFF0000,&H555555,1,4,2,7,0" in generated_content
    assert "Dialogue: 0:02:10.00,0:02:20.00,S14,{\\pos(20,40)}The quick brown fox" in generated_content


def test_generate_sample6_ass_fixture(sample6_ass_content: str) -> None:
    """Test round-trip generation of sample6.ass, focusing on bold/italic styles."""
    subs = parse_ass(sample6_ass_content)
    generated_content = to_ass(subs)

    assert "Style: S1,Arial,60,&HFFB0B0,-1,0,0,0,7,0" in generated_content
    assert "Style: S2,Arial,60,&HFFB0B0,0,-1,0,0,7,0" in generated_content
    assert "Style: S3,Arial,60,&HFFB0B0,0,0,-1,0,7,0" in generated_content
    assert "Style: S4,Arial,60,&HFFB0B0,0,0,0,-1,7,0" in generated_content


def test_generate_sample7_ass_fixture(sample7_ass_content: str) -> None:
    """Test round-trip generation of sample7.ass, focusing on transform styles."""
    subs = parse_ass(sample7_ass_content)
    generated_content = to_ass(subs)

    assert "Style: S1,Arial,60,&HFFB0B0,150,100,0,0,7,0" in generated_content
    assert "Style: S4,Arial,60,&HFFB0B0,100,100,0,-5,7,0" in generated_content


def test_generate_sample8_ass_fixture(sample8_ass_content: str) -> None:
    """Test round-trip generation of sample8.ass, focusing on complex inline override tags."""
    subs = parse_ass(sample8_ass_content)
    generated_content = to_ass(subs)

    assert "{\\pos(60,100)}The quick {\\b1}brown{\\b0} fox jumps over a lazy dog." in generated_content
    assert (
        "{\\pos(60,100)}\\shad uses {\\shad5}BackColour{\\r} in [V4+ Styles] section as a shade." in generated_content
    )
    assert (
        "{\\pos(60,100)}The quick brown {\\c&HFF0000&}fox{\\r} {\\c&HFF}jumps{\\r} over a lazy {\\c&FF00&}dog{\\r}."
        in generated_content
    )
    assert (
        "{\\pos(60,100)}{\\k150}\\k {\\k150}uses {\\k300}PrimaryColour {\\k100}and {\\k300}SecondaryColour."
        in generated_content
    )


def test_generate_sample9_ass_fixture(sample9_ass_content: str) -> None:
    """Test round-trip generation of sample9.ass, focusing on animation tags."""
    subs = parse_ass(sample9_ass_content)
    generated_content = to_ass(subs)

    assert "{\\pos(60,100)}{\\t(0,10000,0.5,\\fscy200)}The quick brown fox jumps over a lazy dog." in generated_content
    assert (
        "{\\pos(60,100)}{\\t(0,5000,0.5,\\fscy200)}{\\t(5000,10000,2,\\c&HFF&)}The quick brown fox" in generated_content
    )
    assert "{\\move(60,100,150,250,0,5000)}The quick brown fox" in generated_content
    assert "{\\pos(60,100)}{\\fad(4000,4000)}The quick brown fox" in generated_content


def test_generate_sample10_ass_fixture(sample10_ass_content: str) -> None:
    """Test round-trip generation of sample10.ass, focusing on Dialogue effects."""
    subs = parse_ass(sample10_ass_content)
    generated_content = to_ass(subs)

    assert "Dialogue: 0:00:00.00,0:00:10.00,S1,Scroll up;300;100;0,The quick brown fox" in generated_content
    assert "Dialogue: 0:00:40.00,0:00:50.00,S1,Scroll down;100;300;0,The quick brown fox" in generated_content
    assert "Dialogue: 0:01:20.00,0:01:30.00,S1,Banner;0,The quick brown fox" in generated_content


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
