"""Tests for ASS vector drawing parsing and transformation."""

import pytest

from autosubs.models.subtitles.vector import (
    AssVector,
    BezierCommand,
    CloseSplineCommand,
    ExtendSplineCommand,
    LineCommand,
    MoveCommand,
    SplineCommand,
)


class TestVectorCommandSerialization:
    """Test serialization of individual vector commands."""

    def test_move_command_to_string(self) -> None:
        """Test MoveCommand serialization."""
        cmd = MoveCommand(x=0.0, y=0.0)
        assert cmd.to_string() == "m 0 0"

        cmd = MoveCommand(x=10.5, y=20.5)
        assert cmd.to_string() == "m 10.5 20.5"

        # Test integer formatting (should drop .0)
        cmd = MoveCommand(x=10.0, y=20.0)
        assert cmd.to_string() == "m 10 20"

    def test_line_command_to_string(self) -> None:
        """Test LineCommand serialization."""
        cmd = LineCommand(x=100.0, y=200.0)
        assert cmd.to_string() == "l 100 200"

        cmd = LineCommand(x=10.5, y=20.5)
        assert cmd.to_string() == "l 10.5 20.5"

    def test_bezier_command_to_string(self) -> None:
        """Test BezierCommand serialization."""
        cmd = BezierCommand(x1=10.0, y1=20.0, x2=30.0, y2=40.0, x3=50.0, y3=60.0)
        assert cmd.to_string() == "b 10 20 30 40 50 60"

        cmd = BezierCommand(x1=10.5, y1=20.5, x2=30.5, y2=40.5, x3=50.5, y3=60.5)
        assert cmd.to_string() == "b 10.5 20.5 30.5 40.5 50.5 60.5"


class TestVectorParsing:
    """Test parsing of ASS vector strings."""

    def test_parse_empty_string(self) -> None:
        """Test parsing empty vector string."""
        vector = AssVector.from_string("")
        assert len(vector.commands) == 0
        assert vector.to_string() == ""

    def test_parse_simple_move_line(self) -> None:
        """Test parsing simple move and line commands."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        assert len(vector.commands) == 2

        cmd0 = vector.commands[0]
        cmd1 = vector.commands[1]

        assert isinstance(cmd0, MoveCommand)
        assert isinstance(cmd1, LineCommand)
        assert cmd0.x == pytest.approx(0.0)
        assert cmd0.y == pytest.approx(0.0)
        assert cmd1.x == pytest.approx(10.0)
        assert cmd1.y == pytest.approx(10.0)

    def test_parse_with_floats(self) -> None:
        """Test parsing vector string with float coordinates."""
        vector = AssVector.from_string("m 0.5 1.5 l 10.25 20.75")
        assert len(vector.commands) == 2

        cmd0 = vector.commands[0]
        cmd1 = vector.commands[1]

        assert isinstance(cmd0, MoveCommand)
        assert isinstance(cmd1, LineCommand)
        assert cmd0.x == pytest.approx(0.5)
        assert cmd0.y == pytest.approx(1.5)
        assert cmd1.x == pytest.approx(10.25)
        assert cmd1.y == pytest.approx(20.75)

    def test_parse_bezier_command(self) -> None:
        """Test parsing bezier curve command."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        assert len(vector.commands) == 2

        cmd1 = vector.commands[1]
        assert isinstance(cmd1, BezierCommand)
        assert cmd1.x1 == pytest.approx(10.0)
        assert cmd1.y1 == pytest.approx(20.0)
        assert cmd1.x2 == pytest.approx(30.0)
        assert cmd1.y2 == pytest.approx(40.0)
        assert cmd1.x3 == pytest.approx(50.0)
        assert cmd1.y3 == pytest.approx(60.0)

    def test_parse_complex_vector(self) -> None:
        """Test parsing a complex vector with multiple command types."""
        vector = AssVector.from_string("m 0 0 l 100 0 l 100 100 l 0 100")
        assert len(vector.commands) == 4
        assert all(isinstance(cmd, (MoveCommand, LineCommand)) for cmd in vector.commands)

    def test_parse_negative_coordinates(self) -> None:
        """Test parsing vector with negative coordinates."""
        vector = AssVector.from_string("m -10 -20 l 30 -40")

        cmd0 = vector.commands[0]
        cmd1 = vector.commands[1]

        assert isinstance(cmd0, MoveCommand)
        assert isinstance(cmd1, LineCommand)
        assert cmd0.x == pytest.approx(-10.0)
        assert cmd0.y == pytest.approx(-20.0)
        assert cmd1.x == pytest.approx(30.0)
        assert cmd1.y == pytest.approx(-40.0)

    def test_parse_case_insensitive(self) -> None:
        """Test that parsing is case insensitive."""
        vector = AssVector.from_string("M 0 0 L 10 10")
        assert len(vector.commands) == 2
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], LineCommand)

    def test_parse_incomplete_move_raises_error(self) -> None:
        """Test that incomplete move command raises ValueError."""
        with pytest.raises(ValueError, match="Incomplete move command"):
            AssVector.from_string("m 0")

    def test_parse_incomplete_line_raises_error(self) -> None:
        """Test that incomplete line command raises ValueError."""
        with pytest.raises(ValueError, match="Incomplete line command"):
            AssVector.from_string("m 0 0 l 10")

    def test_parse_incomplete_bezier_raises_error(self) -> None:
        """Test that incomplete bezier command raises ValueError."""
        with pytest.raises(ValueError, match="Incomplete bezier command"):
            AssVector.from_string("m 0 0 b 10 20 30")

    def test_parse_unknown_command_raises_error(self) -> None:
        """Test that numbers without a command raise ValueError."""
        with pytest.raises(ValueError, match="without a command"):
            AssVector.from_string("10 10 m 0 0")


class TestVectorRoundTrip:
    """Test round-trip parsing and serialization."""

    def test_simple_round_trip(self) -> None:
        """Test that parsing and serializing returns the same string."""
        original = "m 0 0 l 10 10"
        vector = AssVector.from_string(original)
        assert vector.to_string() == original

    def test_complex_round_trip(self) -> None:
        """Test round-trip with more complex vector."""
        original = "m 0 0 l 100 0 l 100 100 l 0 100"
        vector = AssVector.from_string(original)
        assert vector.to_string() == original

    def test_round_trip_with_bezier(self) -> None:
        """Test round-trip with bezier curves."""
        original = "m 0 0 b 10 20 30 40 50 60 l 100 100"
        vector = AssVector.from_string(original)
        assert vector.to_string() == original


class TestVectorScaling:
    """Test vector scaling transformations."""

    def test_scale_uniform(self) -> None:
        """Test uniform scaling of vector."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 l 20 20"

    def test_scale_xy_separate(self) -> None:
        """Test separate X and Y scaling."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        scaled = vector.scale_xy(2.0, 3.0)
        assert scaled.to_string() == "m 0 0 l 20 30"

    def test_scale_with_offset(self) -> None:
        """Test scaling vector that doesn't start at origin."""
        vector = AssVector.from_string("m 10 10 l 20 20")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 20 20 l 40 40"

    def test_scale_bezier(self) -> None:
        """Test scaling bezier curve."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 b 20 40 60 80 100 120"

    def test_scale_preserves_float_precision(self) -> None:
        """Test that scaling preserves necessary float precision."""
        vector = AssVector.from_string("m 0 0 l 15 15")
        scaled = vector.scale(1.5)
        assert scaled.to_string() == "m 0 0 l 22.5 22.5"

    def test_scale_drops_trailing_zero(self) -> None:
        """Test that scaling results drop .0 for whole numbers."""
        vector = AssVector.from_string("m 0 0 l 5 5")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 l 10 10"


class TestVectorTranslation:
    """Test vector translation transformations."""

    def test_translate_simple(self) -> None:
        """Test simple translation of vector."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        translated = vector.translate(5.0, 5.0)
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_translate_negative(self) -> None:
        """Test translation with negative values."""
        vector = AssVector.from_string("m 10 10 l 20 20")
        translated = vector.translate(-5.0, -5.0)
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_translate_bezier(self) -> None:
        """Test translation of bezier curve."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        translated = vector.translate(10.0, 10.0)
        assert translated.to_string() == "m 10 10 b 20 30 40 50 60 70"


class TestVectorRotation:
    """Test vector rotation transformations."""

    def test_rotate_90_degrees(self) -> None:
        """Test 90-degree rotation around origin."""
        vector = AssVector.from_string("m 0 0 l 10 0")
        rotated = vector.rotate(90.0)

        cmd1 = rotated.commands[1]
        assert isinstance(cmd1, LineCommand)
        assert cmd1.x == pytest.approx(0.0, abs=1e-10)
        assert cmd1.y == pytest.approx(10.0, abs=1e-10)

    def test_rotate_180_degrees(self) -> None:
        """Test 180-degree rotation around origin."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        rotated = vector.rotate(180.0)

        cmd1 = rotated.commands[1]
        assert isinstance(cmd1, LineCommand)
        assert cmd1.x == pytest.approx(-10.0, abs=1e-10)
        assert cmd1.y == pytest.approx(-10.0, abs=1e-10)

    def test_rotate_with_custom_origin(self) -> None:
        """Test rotation around a custom origin point."""
        vector = AssVector.from_string("m 10 10 l 20 10")
        rotated = vector.rotate(90.0, origin_x=10.0, origin_y=10.0)

        cmd1 = rotated.commands[1]
        assert isinstance(cmd1, LineCommand)
        assert cmd1.x == pytest.approx(10.0, abs=1e-10)
        assert cmd1.y == pytest.approx(20.0, abs=1e-10)

    def test_rotate_bezier(self) -> None:
        """Test rotation of bezier curve."""
        vector = AssVector.from_string("m 0 0 b 10 0 20 0 30 0")
        rotated = vector.rotate(90.0)

        cmd1 = rotated.commands[1]
        assert isinstance(cmd1, BezierCommand)
        assert cmd1.x1 == pytest.approx(0.0, abs=1e-10)
        assert cmd1.y1 == pytest.approx(10.0, abs=1e-10)


class TestVectorImmutability:
    """Test that transformations return new objects."""

    def test_scale_returns_new_object(self) -> None:
        """Test that scaling returns a new AssVector."""
        original = AssVector.from_string("m 0 0 l 10 10")
        scaled = original.scale(2.0)
        assert original is not scaled
        assert original.to_string() == "m 0 0 l 10 10"
        assert scaled.to_string() == "m 0 0 l 20 20"

    def test_translate_returns_new_object(self) -> None:
        """Test that translation returns a new AssVector."""
        original = AssVector.from_string("m 0 0 l 10 10")
        translated = original.translate(5.0, 5.0)
        assert original is not translated
        assert original.to_string() == "m 0 0 l 10 10"
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_rotate_returns_new_object(self) -> None:
        """Test that rotation returns a new AssVector."""
        original = AssVector.from_string("m 0 0 l 10 0")
        rotated = original.rotate(90.0)
        assert original is not rotated
        assert original.to_string() == "m 0 0 l 10 0"


class TestAcceptanceCriteria:
    """Test the specific acceptance criteria from the issue."""

    def test_acceptance_parse_simple_vector(self) -> None:
        """Test: AssVector.from_string('m 0 0 l 10 10') returns a structured object."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        assert isinstance(vector, AssVector)
        assert len(vector.commands) == 2
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], LineCommand)

    def test_acceptance_scale_vector(self) -> None:
        """Test: vector.scale(2.0) results in 'm 0 0 l 20 20'."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 l 20 20"


class TestImplicitCommands:
    """Test parsing of implicit repeated commands."""

    def test_implicit_line_commands(self) -> None:
        """Test: m 0 0 l 10 10 20 20 30 30 (implicit repeated line commands)."""
        vector = AssVector.from_string("m 0 0 l 10 10 20 20 30 30")
        assert len(vector.commands) == 4

        cmd1 = vector.commands[1]
        cmd2 = vector.commands[2]
        cmd3 = vector.commands[3]

        assert isinstance(cmd1, LineCommand)
        assert isinstance(cmd2, LineCommand)
        assert isinstance(cmd3, LineCommand)
        assert cmd1.x == pytest.approx(10.0)
        assert cmd1.y == pytest.approx(10.0)
        assert cmd2.x == pytest.approx(20.0)
        assert cmd2.y == pytest.approx(20.0)
        assert cmd3.x == pytest.approx(30.0)
        assert cmd3.y == pytest.approx(30.0)

    def test_implicit_bezier_commands(self) -> None:
        """Test implicit repeated bezier commands."""
        vector = AssVector.from_string("m 0 0 b 10 10 20 20 30 30 40 40 50 50 60 60")
        assert len(vector.commands) == 3
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], BezierCommand)
        assert isinstance(vector.commands[2], BezierCommand)


class TestMixedSeparators:
    """Test parsing with different separator styles."""

    def test_comma_separators(self) -> None:
        """Test parsing with comma separators."""
        vector = AssVector.from_string("m 0,0 l 10,10")
        assert len(vector.commands) == 2

        cmd0 = vector.commands[0]
        cmd1 = vector.commands[1]

        assert isinstance(cmd0, MoveCommand)
        assert isinstance(cmd1, LineCommand)
        assert cmd0.x == pytest.approx(0.0)
        assert cmd0.y == pytest.approx(0.0)
        assert cmd1.x == pytest.approx(10.0)
        assert cmd1.y == pytest.approx(10.0)

    def test_mixed_comma_and_space_separators(self) -> None:
        """Test parsing with mixed comma and space separators."""
        vector = AssVector.from_string("m 0,0 l 10 10,20 20")
        assert len(vector.commands) == 3

        cmd2 = vector.commands[2]
        assert isinstance(cmd2, LineCommand)
        assert cmd2.x == pytest.approx(20.0)
        assert cmd2.y == pytest.approx(20.0)

    def test_no_spaces_after_commands(self) -> None:
        """Test parsing with no spaces after command letters."""
        vector = AssVector.from_string("m0 0l10 10b20 20 30 30 40 40")
        assert len(vector.commands) == 3
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], LineCommand)
        assert isinstance(vector.commands[2], BezierCommand)

    def test_multiple_spaces(self) -> None:
        """Test parsing with multiple consecutive spaces."""
        vector = AssVector.from_string("m   0    0   l   10   10")
        assert len(vector.commands) == 2
        assert vector.to_string() == "m 0 0 l 10 10"


class TestNewCommands:
    """Test the new spline-related commands."""

    def test_spline_command(self) -> None:
        """Test parsing and serialization of spline commands."""
        vector = AssVector.from_string("m 0 0 s 10 20 30 40 50 60")
        assert len(vector.commands) == 2
        assert isinstance(vector.commands[1], SplineCommand)
        assert vector.to_string() == "m 0 0 s 10 20 30 40 50 60"

    def test_extend_spline_command(self) -> None:
        """Test parsing and serialization of extend spline commands."""
        vector = AssVector.from_string("m 0 0 p 10 20")
        assert len(vector.commands) == 2
        assert isinstance(vector.commands[1], ExtendSplineCommand)
        assert vector.to_string() == "m 0 0 p 10 20"

    def test_close_spline_command(self) -> None:
        """Test parsing and serialization of close spline commands."""
        vector = AssVector.from_string("m 0 0 l 10 0 l 10 10 c")
        assert len(vector.commands) == 4
        assert isinstance(vector.commands[3], CloseSplineCommand)
        assert vector.to_string() == "m 0 0 l 10 0 l 10 10 c"

    def test_implicit_spline_commands(self) -> None:
        """Test implicit repeated spline commands."""
        vector = AssVector.from_string("m 0 0 s 10 20 30 40 50 60 70 80 90 100 110 120")
        assert len(vector.commands) == 3
        assert all(isinstance(cmd, (MoveCommand, SplineCommand)) for cmd in vector.commands)


class TestFlipTransformation:
    """Test the flip transformation."""

    def test_flip_horizontal(self) -> None:
        """Test horizontal flip (along Y-axis)."""
        vector = AssVector.from_string("m 10 0 l 20 10")
        flipped = vector.flip("h")
        assert flipped.to_string() == "m -10 0 l -20 10"

    def test_flip_vertical(self) -> None:
        """Test vertical flip (along X-axis)."""
        vector = AssVector.from_string("m 0 10 l 10 20")
        flipped = vector.flip("v")
        assert flipped.to_string() == "m 0 -10 l 10 -20"

    def test_flip_x_axis(self) -> None:
        """Test flip along X-axis (same as vertical)."""
        vector = AssVector.from_string("m 0 10 l 10 20")
        flipped = vector.flip("x")
        assert flipped.to_string() == "m 0 -10 l 10 -20"

    def test_flip_y_axis(self) -> None:
        """Test flip along Y-axis (same as horizontal)."""
        vector = AssVector.from_string("m 10 0 l 20 10")
        flipped = vector.flip("y")
        assert flipped.to_string() == "m -10 0 l -20 10"

    def test_flip_invalid_axis_raises_error(self) -> None:
        """Test that invalid axis raises ValueError."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        with pytest.raises(ValueError, match="Invalid axis"):
            vector.flip("z")


class TestBoundingBox:
    """Test the get_bounding_box method."""

    def test_bounding_box_simple_square(self) -> None:
        """Test bounding box for a simple square."""
        vector = AssVector.from_string("m 0 0 l 10 0 l 10 10 l 0 10")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(0.0), pytest.approx(0.0), pytest.approx(10.0), pytest.approx(10.0))  # type: ignore[comparison-overlap]

    def test_bounding_box_offset_shape(self) -> None:
        """Test bounding box for an offset shape."""
        vector = AssVector.from_string("m 5 5 l 15 5 l 15 15 l 5 15")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(5.0), pytest.approx(5.0), pytest.approx(15.0), pytest.approx(15.0))  # type: ignore[comparison-overlap]

    def test_bounding_box_with_bezier(self) -> None:
        """Test bounding box with bezier curves."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(0.0), pytest.approx(0.0), pytest.approx(50.0), pytest.approx(60.0))  # type: ignore[comparison-overlap]

    def test_bounding_box_negative_coords(self) -> None:
        """Test bounding box with negative coordinates."""
        vector = AssVector.from_string("m -10 -10 l 10 10")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(-10.0), pytest.approx(-10.0), pytest.approx(10.0), pytest.approx(10.0))  # type: ignore[comparison-overlap]

    def test_bounding_box_empty_vector(self) -> None:
        """Test bounding box for empty vector."""
        vector = AssVector.from_string("")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(0.0), pytest.approx(0.0), pytest.approx(0.0), pytest.approx(0.0))  # type: ignore[comparison-overlap]

    def test_bounding_box_close_command_ignored(self) -> None:
        """Test that close command doesn't affect bounding box."""
        vector = AssVector.from_string("m 0 0 l 10 0 l 10 10 c")
        bbox = vector.get_bounding_box()
        assert bbox == (pytest.approx(0.0), pytest.approx(0.0), pytest.approx(10.0), pytest.approx(10.0))  # type: ignore[comparison-overlap]


class TestEdgeCases:
    """Test edge cases and robustness."""

    def test_scale_zero(self) -> None:
        """Test scaling by zero."""
        vector = AssVector.from_string("m 10 10 l 20 20")
        scaled = vector.scale(0.0)
        assert scaled.to_string() == "m 0 0 l 0 0"

    def test_scale_negative(self) -> None:
        """Test scaling by negative value (flip)."""
        vector = AssVector.from_string("m 10 10 l 20 20")
        scaled = vector.scale(-1.0)
        assert scaled.to_string() == "m -10 -10 l -20 -20"

    def test_large_numbers(self) -> None:
        """Test with large coordinate values."""
        vector = AssVector.from_string("m 0 0 l 10000 10000")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 l 20000 20000"

    def test_very_small_numbers(self) -> None:
        """Test with very small coordinate values."""
        vector = AssVector.from_string("m 0 0 l 0.001 0.001")
        scaled = vector.scale(2.0)
        assert scaled.to_string() == "m 0 0 l 0.002 0.002"

    def test_dangling_coordinates_raises_error(self) -> None:
        """Test that incomplete coordinate pairs at the end raise error."""
        with pytest.raises(ValueError, match="Incomplete"):
            AssVector.from_string("m 0 0 l 10 10 15")

    def test_multiple_rotations_precision(self) -> None:
        """Test precision after multiple rotations."""
        vector = AssVector.from_string("m 0 0 l 100 0")
        # Rotate 360 degrees in 4 steps
        rotated = vector.rotate(90.0).rotate(90.0).rotate(90.0).rotate(90.0)

        cmd1 = rotated.commands[1]
        assert isinstance(cmd1, LineCommand)
        assert cmd1.x == pytest.approx(100.0, abs=1e-9)
        assert cmd1.y == pytest.approx(0.0, abs=1e-9)
