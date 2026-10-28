"""S1: map walkability and one-tile movement."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Agent, Env


def can_walk(env: Env, x: int, y: int) -> bool:
    """Decide whether a map coordinate is traversable."""
    return False


def move(agent: Agent, direction: tuple[int, int]) -> bool:
    """Move one tile; return whether the position changed."""
    return False
