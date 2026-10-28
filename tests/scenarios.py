"""Drive advanced tasks with configured maps and player action sequences."""

import json
from pathlib import Path

from controller import Controller, WAIT
from game import Game


ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / 'assets/maps/advanced'
CASES = json.loads((ROOT / 'assets/scenarios/advanced/cases.json').read_text(
    encoding='utf-8'))


class ScriptedGhost(Controller):
    def __init__(self, agent, actions):
        super().__init__(agent)
        self.actions = [tuple(action) for action in actions]
        self.index = 0

    def get_direction(self):
        if self.index >= len(self.actions):
            return WAIT
        direction = self.actions[self.index]
        self.index += 1
        return direction


def snapshot(game: Game, probes: list[list[int]] | None = None) -> dict:
    """Only public game observations; no student strategy fields."""
    return {
        'status': game.status,
        'player': (game.player.x, game.player.y),
        'player_live': game.player.live,
        'score': game.player.score,
        'ghosts': [(ghost.x, ghost.y) for ghost in game.env.ghosts],
        'ghosts_live': [ghost.live for ghost in game.env.ghosts],
        'walkable': {(x, y): game.env.can_walk(x, y)
                     for x, y in (probes or [])},
    }


def run_case(name: str) -> tuple[Game, list[dict]]:
    case = CASES[name]
    scripts = case.get('ghost_actions', [])
    next_ghost = iter(scripts)

    def scripted(agent):
        return ScriptedGhost(agent, next(next_ghost, []))

    game = Game.for_advanced(
        tuple(case['features']),
        path=MAPS / case['map'] if 'map' in case else None,
        feature_config=case.get('config', {}),
        ghost_controller=scripted,
    )
    probes = case.get('probe', [])
    states = [snapshot(game, probes)]
    for action in case['actions']:
        game.step(tuple(action))
        states.append(snapshot(game, probes))
    return game, states
