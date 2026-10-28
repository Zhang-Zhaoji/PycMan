"""S2: collectible items, scoring, and powered duration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import Player


def advance_power(player: Player) -> None:
    """Advance the existing powered timer at the start of a valid turn."""
    pass


def collect_item(player: Player) -> None:
    """Process the terrain item under a player after a successful move."""
    pass
