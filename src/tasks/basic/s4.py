"""S4: legal directions and random ghost decisions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from controller import Controller


def legal_directions(controller: Controller) -> list[tuple[int, int]]:
    """Report traversable cardinal directions without moving anyone."""
    return []


def random_direction(controller: Controller) -> tuple[int, int]:
    """Choose one legal direction, or wait when none exists."""
    return (0, 0)
