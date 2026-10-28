"""Optional game-rule interfaces used by cumulative task stages."""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from controller import Controller, KeyboardController
    from game import Game
    from utils import Agent, Env, Player


@dataclass(frozen=True)
class GameRules:
    can_walk: Callable[[Env, int, int], bool] | None = None
    move: Callable[[Agent, tuple[int, int]], bool] | None = None
    advance_power: Callable[[Player], None] | None = None
    collect_item: Callable[[Player], None] | None = None
    resolve_collisions: Callable[[Env], None] | None = None
    check_result: Callable[[Game], str] | None = None
    legal_directions: Callable[[Controller], list[tuple[int, int]]] | None = None
    random_direction: Callable[[Controller], tuple[int, int]] | None = None
    handle_key: Callable[[KeyboardController, str], bool] | None = None
    continuous_direction: Callable[[KeyboardController], tuple[int, int]] | None = None


STAGES = ('S1', 'S2', 'S3', 'S4', 'S5')


def stage_rules(stage: str, implementation: ModuleType | None = None) -> GameRules:
    """Activate a cumulative prefix of student rule interfaces."""
    stage = stage.upper()
    if stage not in STAGES:
        raise ValueError(f'Unknown stage: {stage}')
    if implementation is None:
        from tasks import basic
        implementation = basic
    level = int(stage[1:])
    return GameRules(
        can_walk=implementation.can_walk,
        move=implementation.move,
        advance_power=implementation.advance_power if level >= 2 else None,
        collect_item=implementation.collect_item if level >= 2 else lambda player: None,
        resolve_collisions=(implementation.resolve_collisions if level >= 3
                            else lambda env: None),
        check_result=(implementation.check_result if level >= 3
                      else lambda game: 'running'),
        legal_directions=implementation.legal_directions if level >= 4 else None,
        random_direction=implementation.random_direction if level >= 4 else None,
        handle_key=implementation.handle_key if level >= 5 else None,
        continuous_direction=implementation.continuous_direction if level >= 5 else None,
    )
