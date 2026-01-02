r"""Models for representing and transforming ASS vector drawings.

ASS format supports vector drawings via the \p tag and \clip tag, which use
drawing commands like 'm' (move), 'l' (line), and 'b' (bezier curve).
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


@dataclass(frozen=True)
class MoveCommand(AssVectorCommand):
    """Represents a move command (m x y) in ASS vector drawing."""

    x: float
    y: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return f"m {self._format_coord(self.x)} {self._format_coord(self.y)}"

    @staticmethod
    def _format_coord(value: float) -> str:
        """Format a coordinate value, dropping .0 for whole numbers."""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

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


@dataclass(frozen=True)
class LineCommand(AssVectorCommand):
    """Represents a line command (l x y) in ASS vector drawing."""

    x: float
    y: float

    def to_string(self) -> str:
        """Convert the command back to ASS vector string format."""
        return f"l {self._format_coord(self.x)} {self._format_coord(self.y)}"

    @staticmethod
    def _format_coord(value: float) -> str:
        """Format a coordinate value, dropping .0 for whole numbers."""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

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

    @staticmethod
    def _format_coord(value: float) -> str:
        """Format a coordinate value, dropping .0 for whole numbers."""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

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


@dataclass(frozen=True)
class AssVector:
    """Represents an ASS vector drawing, which is a sequence of drawing commands."""

    commands: tuple[AssVectorCommand, ...]

    @classmethod
    def from_string(cls, vector_str: str) -> AssVector:
        """Parse an ASS vector string into structured commands.

        Args:
            vector_str: ASS vector string like "m 0 0 l 10 10 b 20 20 30 30 40 40"

        Returns:
            AssVector instance with parsed commands.

        Raises:
            ValueError: If the vector string is invalid or malformed.
        """
        vector_str = vector_str.strip()
        if not vector_str:
            return cls(commands=())

        # Tokenize the input string into command letters and numbers
        tokens = re.findall(r"[mlb]|[-+]?\d*\.?\d+", vector_str, re.IGNORECASE)

        commands: list[AssVectorCommand] = []
        i = 0

        while i < len(tokens):
            cmd = tokens[i].lower()

            if cmd == "m":
                # Move command: m x y
                if i + 2 >= len(tokens):
                    raise ValueError(f"Incomplete move command at position {i}")
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                commands.append(MoveCommand(x=x, y=y))
                i += 3

            elif cmd == "l":
                # Line command: l x y
                if i + 2 >= len(tokens):
                    raise ValueError(f"Incomplete line command at position {i}")
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                commands.append(LineCommand(x=x, y=y))
                i += 3

            elif cmd == "b":
                # Bezier command: b x1 y1 x2 y2 x3 y3
                if i + 6 >= len(tokens):
                    raise ValueError(f"Incomplete bezier command at position {i}")
                x1 = float(tokens[i + 1])
                y1 = float(tokens[i + 2])
                x2 = float(tokens[i + 3])
                y2 = float(tokens[i + 4])
                x3 = float(tokens[i + 5])
                y3 = float(tokens[i + 6])
                commands.append(BezierCommand(x1=x1, y1=y1, x2=x2, y2=y2, x3=x3, y3=y3))
                i += 7

            else:
                raise ValueError(f"Unknown or unexpected token '{tokens[i]}' at position {i}")

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
