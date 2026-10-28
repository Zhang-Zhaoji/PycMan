"""S5: keyboard requests and buffered turns in continuous mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from controller import KeyboardController


def handle_key(controller: KeyboardController, key: str) -> bool:
    """Accept a movement key and update the requested direction."""
    return False


def continuous_direction(controller: KeyboardController) -> tuple[int, int]:
    """Choose a continuous-mode action, including a buffered turn."""
    return (0, 0)
