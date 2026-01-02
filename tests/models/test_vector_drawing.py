"""Tests for ASS vector drawing parsing and transformation."""

import math

import pytest

from autosubs.models.subtitles.vector import AssVector, BezierCommand, LineCommand, MoveCommand


class TestVectorCommandSerialization:
    """Test serialization of individual vector commands."""

    def test_move_command_to_string(self) -> None:
        """Test MoveCommand serialization."""
        cmd = MoveCommand(x=0, y=0)
        assert cmd.to_string() == "m 0 0"

        cmd = MoveCommand(x=10.5, y=20.5)
        assert cmd.to_string() == "m 10.5 20.5"

        # Test integer formatting (should drop .0)
        cmd = MoveCommand(x=10.0, y=20.0)
        assert cmd.to_string() == "m 10 20"

    def test_line_command_to_string(self) -> None:
        """Test LineCommand serialization."""
        cmd = LineCommand(x=100, y=200)
        assert cmd.to_string() == "l 100 200"

        cmd = LineCommand(x=10.5, y=20.5)
        assert cmd.to_string() == "l 10.5 20.5"

    def test_bezier_command_to_string(self) -> None:
        """Test BezierCommand serialization."""
        cmd = BezierCommand(x1=10, y1=20, x2=30, y2=40, x3=50, y3=60)
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
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], LineCommand)
        assert vector.commands[0].x == 0
        assert vector.commands[0].y == 0
        assert vector.commands[1].x == 10
        assert vector.commands[1].y == 10

    def test_parse_with_floats(self) -> None:
        """Test parsing vector string with float coordinates."""
        vector = AssVector.from_string("m 0.5 1.5 l 10.25 20.75")
        assert len(vector.commands) == 2
        assert vector.commands[0].x == 0.5
        assert vector.commands[0].y == 1.5
        assert vector.commands[1].x == 10.25
        assert vector.commands[1].y == 20.75

    def test_parse_bezier_command(self) -> None:
        """Test parsing bezier curve command."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        assert len(vector.commands) == 2
        assert isinstance(vector.commands[0], MoveCommand)
        assert isinstance(vector.commands[1], BezierCommand)
        bezier = vector.commands[1]
        assert isinstance(bezier, BezierCommand)
        assert bezier.x1 == 10
        assert bezier.y1 == 20
        assert bezier.x2 == 30
        assert bezier.y2 == 40
        assert bezier.x3 == 50
        assert bezier.y3 == 60

    def test_parse_complex_vector(self) -> None:
        """Test parsing a complex vector with multiple command types."""
        vector = AssVector.from_string("m 0 0 l 100 0 l 100 100 l 0 100")
        assert len(vector.commands) == 4
        assert all(isinstance(cmd, (MoveCommand, LineCommand)) for cmd in vector.commands)

    def test_parse_negative_coordinates(self) -> None:
        """Test parsing vector with negative coordinates."""
        vector = AssVector.from_string("m -10 -20 l 30 -40")
        assert vector.commands[0].x == -10
        assert vector.commands[0].y == -20
        assert vector.commands[1].x == 30
        assert vector.commands[1].y == -40

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
        """Test that unknown command raises ValueError."""
        with pytest.raises(ValueError, match="Unknown or unexpected token"):
            AssVector.from_string("m 0 0 x 10 10")


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
        translated = vector.translate(5, 5)
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_translate_negative(self) -> None:
        """Test translation with negative values."""
        vector = AssVector.from_string("m 10 10 l 20 20")
        translated = vector.translate(-5, -5)
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_translate_bezier(self) -> None:
        """Test translation of bezier curve."""
        vector = AssVector.from_string("m 0 0 b 10 20 30 40 50 60")
        translated = vector.translate(10, 10)
        assert translated.to_string() == "m 10 10 b 20 30 40 50 60 70"


class TestVectorRotation:
    """Test vector rotation transformations."""

    def test_rotate_90_degrees(self) -> None:
        """Test 90-degree rotation around origin."""
        vector = AssVector.from_string("m 0 0 l 10 0")
        rotated = vector.rotate(90)

        # After 90-degree rotation, (10, 0) should become approximately (0, 10)
        assert isinstance(rotated.commands[1], LineCommand)
        assert math.isclose(rotated.commands[1].x, 0, abs_tol=1e-10)
        assert math.isclose(rotated.commands[1].y, 10, abs_tol=1e-10)

    def test_rotate_180_degrees(self) -> None:
        """Test 180-degree rotation around origin."""
        vector = AssVector.from_string("m 0 0 l 10 10")
        rotated = vector.rotate(180)

        # After 180-degree rotation, (10, 10) should become approximately (-10, -10)
        assert isinstance(rotated.commands[1], LineCommand)
        assert math.isclose(rotated.commands[1].x, -10, abs_tol=1e-10)
        assert math.isclose(rotated.commands[1].y, -10, abs_tol=1e-10)

    def test_rotate_with_custom_origin(self) -> None:
        """Test rotation around a custom origin point."""
        vector = AssVector.from_string("m 10 10 l 20 10")
        rotated = vector.rotate(90, origin_x=10, origin_y=10)

        # Rotating (20, 10) around (10, 10) by 90 degrees should give approximately (10, 20)
        assert isinstance(rotated.commands[1], LineCommand)
        assert math.isclose(rotated.commands[1].x, 10, abs_tol=1e-10)
        assert math.isclose(rotated.commands[1].y, 20, abs_tol=1e-10)

    def test_rotate_bezier(self) -> None:
        """Test rotation of bezier curve."""
        vector = AssVector.from_string("m 0 0 b 10 0 20 0 30 0")
        rotated = vector.rotate(90)

        # All points should rotate 90 degrees
        assert isinstance(rotated.commands[1], BezierCommand)
        bezier = rotated.commands[1]
        assert math.isclose(bezier.x1, 0, abs_tol=1e-10)
        assert math.isclose(bezier.y1, 10, abs_tol=1e-10)


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
        translated = original.translate(5, 5)
        assert original is not translated
        assert original.to_string() == "m 0 0 l 10 10"
        assert translated.to_string() == "m 5 5 l 15 15"

    def test_rotate_returns_new_object(self) -> None:
        """Test that rotation returns a new AssVector."""
        original = AssVector.from_string("m 0 0 l 10 0")
        rotated = original.rotate(90)
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
