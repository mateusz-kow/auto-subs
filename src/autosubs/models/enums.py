"""Shared enumerations for library configuration."""

from enum import StrEnum, auto


class TimingDistribution(StrEnum):
    """Defines the strategy for distributing time when generating word timings."""

    BY_WORD_COUNT = auto()
    BY_CHAR_COUNT = auto()
