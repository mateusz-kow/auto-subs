import pytest

from autosubs.core.generator import to_microdvd
from autosubs.core.parser import parse_microdvd
from autosubs.models.subtitles import Subtitles, SubtitleSegment, SubtitleWord


def test_parse_basic_with_explicit_fps() -> None:
    """Test basic parsing with an explicit FPS parameter."""
    content = "{24}{48}Hello world.\n{50}{72}This is a test."
    segments = parse_microdvd(content, fps=24)
    assert len(segments) == 2
    assert segments[0].start == pytest.approx(1.0)
    assert segments[0].end == pytest.approx(2.0)
    assert segments[0].text == "Hello world."
    assert segments[1].start == pytest.approx(50 / 24)
    assert segments[1].end == pytest.approx(3.0)
    assert segments[1].text == "This is a test."


def test_parse_with_fps_from_header() -> None:
    """Test FPS extraction from the {1}{1}fps_value header."""
    content = "{1}{1}25\n{25}{50}First line.\n{51}{75}Second line."
    segments = parse_microdvd(content)
    assert len(segments) == 2
    assert segments[0].start == pytest.approx(1.0)
    assert segments[0].end == pytest.approx(2.0)
    assert segments[1].start == pytest.approx(51 / 25)
    assert segments[1].end == pytest.approx(3.0)


def test_parse_fps_parameter_overrides_header() -> None:
    """Test that the FPS parameter correctly overrides the header value."""
    content = "{1}{1}25\n{24}{48}Hello."
    segments = parse_microdvd(content, fps=24)
    assert len(segments) == 1
    assert segments[0].start == pytest.approx(1.0)
    assert segments[0].end == pytest.approx(2.0)


def test_parse_no_fps_raises_error() -> None:
    """Test that a ValueError is raised if no FPS is available."""
    content = "{24}{48}Hello."
    with pytest.raises(ValueError, match="FPS must be provided to parse MicroDVD files."):
        parse_microdvd(content)


@pytest.mark.parametrize("fps_val", [0, -25])
def test_parse_invalid_fps_raises_error(fps_val: float) -> None:
    """Test that a ValueError is raised for zero or negative FPS."""
    content = "{24}{48}Hello."
    with pytest.raises(ValueError, match="FPS must be a positive number."):
        parse_microdvd(content, fps=fps_val)


@pytest.mark.parametrize(
    ("fps", "start_frame", "end_frame", "expected_start", "expected_end"),
    [
        (23.976, 24, 48, 1.001, 2.002),
        (25, 25, 50, 1.0, 2.0),
        (29.97, 30, 60, 1.001, 2.002),
    ],
)
def test_parse_timestamp_accuracy(
    fps: float, start_frame: float, end_frame: float, expected_start: float, expected_end: float
) -> None:
    """Test timestamp conversion accuracy at different framerates."""
    content = f"{{{start_frame}}}{{{end_frame}}}Test text"
    segments = parse_microdvd(content, fps=fps)
    assert len(segments) == 1
    assert segments[0].start == pytest.approx(expected_start, abs=1e-3)
    assert segments[0].end == pytest.approx(expected_end, abs=1e-3)


def test_parse_handles_malformed_lines() -> None:
    """Test that malformed lines are skipped during parsing."""
    content = "{24}{48}Good line.\n{a}{b}Bad line.\n{50}Only one bracket.\nAnother bad line.\n{50}{75}Another good one."
    segments = parse_microdvd(content, fps=25)
    assert len(segments) == 2
    assert segments[0].text == "Good line."
    assert segments[1].text == "Another good one."


def test_parse_empty_and_whitespace_lines() -> None:
    """Test that empty or whitespace lines are correctly handled."""
    content = "{24}{48}Line 1.\n\n{50}{75}Line 2."
    segments = parse_microdvd(content, fps=25)
    assert len(segments) == 2


def test_parse_large_frame_numbers() -> None:
    """Test parsing with large frame numbers."""
    content = "{100000}{125000}Large frame number test."
    segments = parse_microdvd(content, fps=25)
    assert len(segments) == 1
    assert segments[0].start == pytest.approx(4000.0)
    assert segments[0].end == pytest.approx(5000.0)


def test_parse_frame_zero() -> None:
    """Test parsing with frame number 0."""
    content = "{0}{25}Frame zero test."
    segments = parse_microdvd(content, fps=25)
    assert len(segments) == 1
    assert segments[0].start == pytest.approx(0.0)
    assert segments[0].end == pytest.approx(1.0)


def test_parse_multiline_text() -> None:
    """Test that pipe characters in text are converted to newlines."""
    content = "{25}{50}First line|Second line"
    segments = parse_microdvd(content, fps=25)
    assert segments[0].text == "First line\nSecond line"


def test_parse_skips_invalid_timestamps() -> None:
    """Test that lines with end frame < start frame are skipped."""
    content = "{50}{25}This should be skipped."
    segments = parse_microdvd(content, fps=25)
    assert len(segments) == 0


def test_parse_empty_content() -> None:
    """Test that parsing empty content returns an empty list."""
    assert parse_microdvd("", fps=25) == []


# Generator Tests


@pytest.fixture
def sample_subtitles() -> Subtitles:
    """Provides a sample Subtitles object for testing."""
    return Subtitles(
        segments=[
            SubtitleSegment(words=[SubtitleWord(text="Hello world.", start=1.0, end=2.0)]),
            SubtitleSegment(words=[SubtitleWord(text="Test line.", start=2.5, end=4.0)]),
        ]
    )


def test_generate_basic(sample_subtitles: Subtitles) -> None:
    """Test basic generation of a MicroDVD file."""
    result = to_microdvd(sample_subtitles, fps=25)
    expected = "{25}{50}Hello world.\n{62}{100}Test line.\n"
    assert result == expected


@pytest.mark.parametrize("fps_val", [0, -25])
def test_generate_invalid_fps_raises_error(sample_subtitles: Subtitles, fps_val: int) -> None:
    """Test that a ValueError is raised for zero or negative FPS."""
    with pytest.raises(ValueError, match="A positive FPS value is required to generate MicroDVD files."):
        to_microdvd(sample_subtitles, fps=fps_val)


@pytest.mark.parametrize(
    ("start", "end", "fps", "expected_start_frame", "expected_end_frame"),
    [
        (1.001, 2.002, 23.976, 24, 48),
        (1.0, 2.0, 25, 25, 50),
        (1.001, 2.002, 29.97, 30, 60),
    ],
)
def test_generate_frame_number_accuracy(
    start: float, end: float, fps: float, expected_start_frame: float, expected_end_frame: float
) -> None:
    """Test frame number calculation accuracy at different framerates."""
    subs = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord(text="test", start=start, end=end)])])
    result = to_microdvd(subs, fps=fps)
    assert result.startswith(f"{{{expected_start_frame}}}{{{expected_end_frame}}}")


def test_generate_multiline_text() -> None:
    """Test that newlines in text are converted to pipe characters."""
    subs = Subtitles(segments=[SubtitleSegment(words=[SubtitleWord(text="Line 1\nLine 2", start=1.0, end=2.0)])])
    result = to_microdvd(subs, fps=25)
    assert result == "{25}{50}Line 1|Line 2\n"


def test_generate_empty_subtitles() -> None:
    """Test generating from an empty Subtitles object."""
    result = to_microdvd(Subtitles(segments=[]), fps=25)
    assert result == ""


# Round-trip Test


def test_round_trip_conversion(sample_subtitles: Subtitles) -> None:
    """Test that a generated file can be parsed back to the original structure."""
    fps = 29.97
    generated_content = to_microdvd(sample_subtitles, fps=fps)
    parsed_segments = parse_microdvd(generated_content, fps=fps)
    parsed_subtitles = Subtitles(segments=parsed_segments)

    assert len(parsed_subtitles.segments) == len(sample_subtitles.segments)
    for original, parsed in zip(sample_subtitles.segments, parsed_subtitles.segments, strict=False):
        assert parsed.start == pytest.approx(original.start, abs=1 / fps)
        assert parsed.end == pytest.approx(original.end, abs=1 / fps)
        assert parsed.text == original.text
