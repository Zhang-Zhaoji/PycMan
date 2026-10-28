"""S3: collisions and game result."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from utils import Env


def resolve_collisions(env: Env) -> None:
    """Resolve collisions between living characters."""
    pass


def check_result(game: Game) -> str:
    """Report running, won, or lost after collision processing."""
    return 'running'
