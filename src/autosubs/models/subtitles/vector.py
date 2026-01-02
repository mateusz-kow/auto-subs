r"""Models for representing and transforming ASS vector drawings.

ASS format supports vector drawings via the \p tag and \clip tag, which use
drawing commands like 'm' (move), 'l' (line), 'b' (bezier curve), 's' (spline),
'p' (extend spline), and 'c' (close spline).
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AssVectorCommand(ABC):
    """Base class for ASS vector drawing commands."""

    @abstractmethod
    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        pass

    @abstractmethod
    def scale(self, scale_x: float, scale_y: float) -> AssVectorCommand:
        """Return a new command with scaled coordinates."""
        pass

    @abstractmethod
    def translate(self, dx: float, dy: float) -> AssVectorCommand:
        """Return a new command with translated coordinates."""
        pass

    @abstractmethod
    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> AssVectorCommand:
        """Return a new command with rotated coordinates around a given origin."""
        pass

    @abstractmethod
    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        pass

    @staticmethod
    def _format_coord(value: float) -> str:
        """Format a coordinate value, dropping .0 for whole numbers."""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)


@dataclass(frozen=True)
class MoveCommand(AssVectorCommand):
    """Represents a move command (m x y) in ASS vector drawing."""

    x: float
    y: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return f"m {self._format_coord(self.x)} {self._format_coord(self.y)}"

    def scale(self, scale_x: float, scale_y: float) -> MoveCommand:
        """Return a new command with scaled coordinates."""
        return MoveCommand(x=self.x * scale_x, y=self.y * scale_y)

    def translate(self, dx: float, dy: float) -> MoveCommand:
        """Return a new command with translated coordinates."""
        return MoveCommand(x=self.x + dx, y=self.y + dy)

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> MoveCommand:
        """Return a new command with rotated coordinates around a given origin."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Translate to origin
        x_rel = self.x - origin_x
        y_rel = self.y - origin_y

        # Rotate
        x_rot = x_rel * cos_a - y_rel * sin_a
        y_rot = x_rel * sin_a + y_rel * cos_a

        # Translate back
        return MoveCommand(x=x_rot + origin_x, y=y_rot + origin_y)

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        return [(self.x, self.y)]


@dataclass(frozen=True)
class LineCommand(AssVectorCommand):
    """Represents a line command (l x y) in ASS vector drawing."""

    x: float
    y: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return f"l {self._format_coord(self.x)} {self._format_coord(self.y)}"

    def scale(self, scale_x: float, scale_y: float) -> LineCommand:
        """Return a new command with scaled coordinates."""
        return LineCommand(x=self.x * scale_x, y=self.y * scale_y)

    def translate(self, dx: float, dy: float) -> LineCommand:
        """Return a new command with translated coordinates."""
        return LineCommand(x=self.x + dx, y=self.y + dy)

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> LineCommand:
        """Return a new command with rotated coordinates around a given origin."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Translate to origin
        x_rel = self.x - origin_x
        y_rel = self.y - origin_y

        # Rotate
        x_rot = x_rel * cos_a - y_rel * sin_a
        y_rot = x_rel * sin_a + y_rel * cos_a

        # Translate back
        return LineCommand(x=x_rot + origin_x, y=y_rot + origin_y)

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        return [(self.x, self.y)]


@dataclass(frozen=True)
class BezierCommand(AssVectorCommand):
    """Represents a bezier curve command (b x1 y1 x2 y2 x3 y3) in ASS vector drawing."""

    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        coords = [self.x1, self.y1, self.x2, self.y2, self.x3, self.y3]
        formatted = " ".join(self._format_coord(c) for c in coords)
        return f"b {formatted}"

    def scale(self, scale_x: float, scale_y: float) -> BezierCommand:
        """Return a new command with scaled coordinates."""
        return BezierCommand(
            x1=self.x1 * scale_x,
            y1=self.y1 * scale_y,
            x2=self.x2 * scale_x,
            y2=self.y2 * scale_y,
            x3=self.x3 * scale_x,
            y3=self.y3 * scale_y,
        )

    def translate(self, dx: float, dy: float) -> BezierCommand:
        """Return a new command with translated coordinates."""
        return BezierCommand(
            x1=self.x1 + dx,
            y1=self.y1 + dy,
            x2=self.x2 + dx,
            y2=self.y2 + dy,
            x3=self.x3 + dx,
            y3=self.y3 + dy,
        )

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> BezierCommand:
        """Return a new command with rotated coordinates around a given origin."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        def rotate_point(x: float, y: float) -> tuple[float, float]:
            x_rel = x - origin_x
            y_rel = y - origin_y
            x_rot = x_rel * cos_a - y_rel * sin_a
            y_rot = x_rel * sin_a + y_rel * cos_a
            return x_rot + origin_x, y_rot + origin_y

        x1_rot, y1_rot = rotate_point(self.x1, self.y1)
        x2_rot, y2_rot = rotate_point(self.x2, self.y2)
        x3_rot, y3_rot = rotate_point(self.x3, self.y3)

        return BezierCommand(x1=x1_rot, y1=y1_rot, x2=x2_rot, y2=y2_rot, x3=x3_rot, y3=y3_rot)

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        return [(self.x1, self.y1), (self.x2, self.y2), (self.x3, self.y3)]


@dataclass(frozen=True)
class SplineCommand(AssVectorCommand):
    """Represents a cubic spline command (s x1 y1 x2 y2 x3 y3) in ASS vector drawing."""

    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        coords = [self.x1, self.y1, self.x2, self.y2, self.x3, self.y3]
        formatted = " ".join(self._format_coord(c) for c in coords)
        return f"s {formatted}"

    def scale(self, scale_x: float, scale_y: float) -> SplineCommand:
        """Return a new command with scaled coordinates."""
        return SplineCommand(
            x1=self.x1 * scale_x,
            y1=self.y1 * scale_y,
            x2=self.x2 * scale_x,
            y2=self.y2 * scale_y,
            x3=self.x3 * scale_x,
            y3=self.y3 * scale_y,
        )

    def translate(self, dx: float, dy: float) -> SplineCommand:
        """Return a new command with translated coordinates."""
        return SplineCommand(
            x1=self.x1 + dx,
            y1=self.y1 + dy,
            x2=self.x2 + dx,
            y2=self.y2 + dy,
            x3=self.x3 + dx,
            y3=self.y3 + dy,
        )

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> SplineCommand:
        """Return a new command with rotated coordinates around a given origin."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        def rotate_point(x: float, y: float) -> tuple[float, float]:
            x_rel = x - origin_x
            y_rel = y - origin_y
            x_rot = x_rel * cos_a - y_rel * sin_a
            y_rot = x_rel * sin_a + y_rel * cos_a
            return x_rot + origin_x, y_rot + origin_y

        x1_rot, y1_rot = rotate_point(self.x1, self.y1)
        x2_rot, y2_rot = rotate_point(self.x2, self.y2)
        x3_rot, y3_rot = rotate_point(self.x3, self.y3)

        return SplineCommand(x1=x1_rot, y1=y1_rot, x2=x2_rot, y2=y2_rot, x3=x3_rot, y3=y3_rot)

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        return [(self.x1, self.y1), (self.x2, self.y2), (self.x3, self.y3)]


@dataclass(frozen=True)
class ExtendSplineCommand(AssVectorCommand):
    """Represents an extend spline command (p x y) in ASS vector drawing."""

    x: float
    y: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return f"p {self._format_coord(self.x)} {self._format_coord(self.y)}"

    def scale(self, scale_x: float, scale_y: float) -> ExtendSplineCommand:
        """Return a new command with scaled coordinates."""
        return ExtendSplineCommand(x=self.x * scale_x, y=self.y * scale_y)

    def translate(self, dx: float, dy: float) -> ExtendSplineCommand:
        """Return a new command with translated coordinates."""
        return ExtendSplineCommand(x=self.x + dx, y=self.y + dy)

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> ExtendSplineCommand:
        """Return a new command with rotated coordinates around a given origin."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        x_rel = self.x - origin_x
        y_rel = self.y - origin_y

        x_rot = x_rel * cos_a - y_rel * sin_a
        y_rot = x_rel * sin_a + y_rel * cos_a

        return ExtendSplineCommand(x=x_rot + origin_x, y=y_rot + origin_y)

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command."""
        return [(self.x, self.y)]


@dataclass(frozen=True)
class CloseSplineCommand(AssVectorCommand):
    """Represents a close spline command (c) in ASS vector drawing."""

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return "c"

    def scale(self, scale_x: float, scale_y: float) -> CloseSplineCommand:
        """Return a new command with scaled coordinates (no change for close command)."""
        return self

    def translate(self, dx: float, dy: float) -> CloseSplineCommand:
        """Return a new command with translated coordinates (no change for close command)."""
        return self

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> CloseSplineCommand:
        """Return a new command with rotated coordinates (no change for close command)."""
        return self

    def get_coords(self) -> list[tuple[float, float]]:
        """Return all coordinate pairs in this command (none for close command)."""
        return []


@dataclass(frozen=True)
class AssVector:
    """Represents an ASS vector drawing, which is a sequence of drawing commands."""

    commands: tuple[AssVectorCommand, ...]

    @classmethod
    def from_string(cls, vector_str: str) -> AssVector:
        """Parse an ASS vector string into structured commands.

        Args:
            vector_str: ASS vector string like "m 0 0 l 10 10 20 20" (supports implicit commands)

        Returns:
            AssVector instance with parsed commands.

        Raises:
            ValueError: If the vector string is invalid or malformed.
        """
        vector_str = vector_str.strip()
        if not vector_str:
            return cls(commands=())

        # Normalize separators: replace commas and multiple spaces with single spaces
        vector_str = re.sub(r"[,\s]+", " ", vector_str)

        # Tokenize the input string into command letters and numbers
        # Use a more precise regex that only matches valid decimal numbers or command letters
        tokens = re.findall(r"[mlbspc]|[-+]?(?:\d+\.?\d*|\d*\.\d+)", vector_str, re.IGNORECASE)

        commands: list[AssVectorCommand] = []
        i = 0
        last_cmd: str | None = None  # Track the last command for implicit repetition

        while i < len(tokens):
            token = tokens[i].lower()

            # Check if this is a command letter or a number
            if token in ("m", "l", "b", "s", "p", "c"):
                last_cmd = token
                i += 1
            elif last_cmd is None:
                # Numbers without a preceding command are invalid
                raise ValueError(f"Unexpected number '{token}' at position {i} without a command")

            # Now process based on the command type
            if last_cmd == "m":
                # Move command: m x y
                if i + 2 > len(tokens):
                    raise ValueError(f"Incomplete move command at position {i}")
                try:
                    x = float(tokens[i])
                    y = float(tokens[i + 1])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates for move command at position {i}: {e}") from e
                commands.append(MoveCommand(x=x, y=y))
                i += 2

            elif last_cmd == "l":
                # Line command: l x y (can repeat)
                if i + 2 > len(tokens):
                    raise ValueError(f"Incomplete line command at position {i}")
                try:
                    x = float(tokens[i])
                    y = float(tokens[i + 1])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates for line command at position {i}: {e}") from e
                commands.append(LineCommand(x=x, y=y))
                i += 2

            elif last_cmd == "b":
                # Bezier command: b x1 y1 x2 y2 x3 y3 (can repeat)
                if i + 6 > len(tokens):
                    raise ValueError(f"Incomplete bezier command at position {i}")
                try:
                    x1 = float(tokens[i])
                    y1 = float(tokens[i + 1])
                    x2 = float(tokens[i + 2])
                    y2 = float(tokens[i + 3])
                    x3 = float(tokens[i + 4])
                    y3 = float(tokens[i + 5])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates for bezier command at position {i}: {e}") from e
                commands.append(BezierCommand(x1=x1, y1=y1, x2=x2, y2=y2, x3=x3, y3=y3))
                i += 6

            elif last_cmd == "s":
                # Spline command: s x1 y1 x2 y2 x3 y3 (can repeat)
                if i + 6 > len(tokens):
                    raise ValueError(f"Incomplete spline command at position {i}")
                try:
                    x1 = float(tokens[i])
                    y1 = float(tokens[i + 1])
                    x2 = float(tokens[i + 2])
                    y2 = float(tokens[i + 3])
                    x3 = float(tokens[i + 4])
                    y3 = float(tokens[i + 5])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates for spline command at position {i}: {e}") from e
                commands.append(SplineCommand(x1=x1, y1=y1, x2=x2, y2=y2, x3=x3, y3=y3))
                i += 6

            elif last_cmd == "p":
                # Extend spline command: p x y (can repeat)
                if i + 2 > len(tokens):
                    raise ValueError(f"Incomplete extend spline command at position {i}")
                try:
                    x = float(tokens[i])
                    y = float(tokens[i + 1])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates for extend spline command at position {i}: {e}") from e
                commands.append(ExtendSplineCommand(x=x, y=y))
                i += 2

            elif last_cmd == "c":
                # Close spline command: c (no coordinates, no repetition)
                commands.append(CloseSplineCommand())
                # After close, we need an explicit new command before more coordinates
                # But we don't want to break if there are more explicit commands
                # So we keep processing but require explicit command letters

        return cls(commands=tuple(commands))

    def to_string(self) -> str:
        """Convert the vector back to ASS vector string format.

        Returns:
            ASS vector string representation.
        """
        return " ".join(cmd.to_string() for cmd in self.commands)

    def scale(self, scale_factor: float) -> AssVector:
        """Return a new AssVector with all coordinates scaled uniformly.

        Args:
            scale_factor: Factor to scale all coordinates by.

        Returns:
            New AssVector instance with scaled commands.
        """
        return AssVector(commands=tuple(cmd.scale(scale_factor, scale_factor) for cmd in self.commands))

    def scale_xy(self, scale_x: float, scale_y: float) -> AssVector:
        """Return a new AssVector with coordinates scaled separately in X and Y.

        Args:
            scale_x: Factor to scale X coordinates by.
            scale_y: Factor to scale Y coordinates by.

        Returns:
            New AssVector instance with scaled commands.
        """
        return AssVector(commands=tuple(cmd.scale(scale_x, scale_y) for cmd in self.commands))

    def translate(self, dx: float, dy: float) -> AssVector:
        """Return a new AssVector with all coordinates translated.

        Args:
            dx: Amount to translate in X direction.
            dy: Amount to translate in Y direction.

        Returns:
            New AssVector instance with translated commands.
        """
        return AssVector(commands=tuple(cmd.translate(dx, dy) for cmd in self.commands))

    def rotate(self, angle_degrees: float, origin_x: float = 0, origin_y: float = 0) -> AssVector:
        """Return a new AssVector with all coordinates rotated around an origin.

        Args:
            angle_degrees: Angle to rotate by in degrees (counter-clockwise).
            origin_x: X coordinate of rotation origin (default: 0).
            origin_y: Y coordinate of rotation origin (default: 0).

        Returns:
            New AssVector instance with rotated commands.
        """
        return AssVector(commands=tuple(cmd.rotate(angle_degrees, origin_x, origin_y) for cmd in self.commands))

    def flip(self, axis: str) -> AssVector:
        """Return a new AssVector with coordinates flipped along the specified axis.

        Args:
            axis: Axis to flip along ('x', 'y', 'h' for horizontal, or 'v' for vertical).

        Returns:
            New AssVector instance with flipped coordinates.

        Raises:
            ValueError: If axis is not 'x', 'y', 'h', or 'v'.
        """
        axis = axis.lower()
        if axis in ("x", "v"):  # Flip vertically (along X-axis)
            return AssVector(commands=tuple(cmd.scale(1, -1) for cmd in self.commands))
        elif axis in ("y", "h"):  # Flip horizontally (along Y-axis)
            return AssVector(commands=tuple(cmd.scale(-1, 1) for cmd in self.commands))
        else:
            raise ValueError(f"Invalid axis '{axis}'. Must be 'x', 'y', 'h' (horizontal), or 'v' (vertical).")

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """Calculate the bounding box of the vector drawing.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) representing the bounding box.
            Returns (0, 0, 0, 0) if the vector has no coordinates.
        """
        all_coords: list[tuple[float, float]] = []
        for cmd in self.commands:
            all_coords.extend(cmd.get_coords())

        if not all_coords:
            return (0.0, 0.0, 0.0, 0.0)

        xs = [x for x, y in all_coords]
        ys = [y for x, y in all_coords]

        return (min(xs), min(ys), max(xs), max(ys))
