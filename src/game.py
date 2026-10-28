from typing import Callable
from pathlib import Path
from types import ModuleType
from importlib import import_module

from config import GameConfig, PROJECT_ROOT, TERMINAL_CONFIG, load_config

from controller import (Controller, ImmediateKeyboard, KeyboardController,
                        RandomController, WaitingGhost, DIRECTIONS, WAIT)
from rules import GameRules, STAGES, stage_rules
from utils import Agent, Env, Player


DEFAULT_MAP = str(load_config(TERMINAL_CONFIG).map_file)
STAGE_MAPS = {
    'S1': PROJECT_ROOT / 'assets/maps/training_map.txt',
    'S2': PROJECT_ROOT / 'assets/maps/training_map.txt',
    'S3': PROJECT_ROOT / 'assets/maps/basic/s3_collision.txt',
    'S4': PROJECT_ROOT / 'assets/maps/training_map.txt',
    'S5': PROJECT_ROOT / 'assets/maps/crossroads_map.txt',
}


def stage_setup(stage: str, *, path: str | Path | None = None,
                config: GameConfig | None = None,
                implementation: ModuleType | None = None) -> tuple[
                    str | Path, GameConfig, GameRules,
                    Callable[[Agent], Controller], Callable[[Agent], Controller]]:
    """Select stage map, rules, and simple behavior for unfinished stages."""
    stage = stage.upper()
    if stage not in STAGES:
        raise ValueError(f'Unknown stage: {stage}')
    settings = config if config is not None else load_config()
    selected_map = path if path is not None else (
        settings.map_file if config is not None else STAGE_MAPS[stage]
    )
    rules = stage_rules(stage, implementation)
    level = int(stage[1:])
    player_controller = KeyboardController if level >= 5 else ImmediateKeyboard
    ghost_controller = RandomController if level >= 4 else WaitingGhost
    return selected_map, settings, rules, player_controller, ghost_controller


class Game:
    def __init__(self, path: str | Path | list[str] | None = None,
                 player_controller: Callable[[Agent], Controller] = KeyboardController,
                 ghost_controller: Callable[[Agent], Controller] = RandomController,
                 *, config: GameConfig | None = None,
                 rules: GameRules | None = None,
                 features: tuple[str, ...] = (),
                 feature_config: dict[str, dict] | None = None) -> None:
        self.config = config if config is not None else load_config(TERMINAL_CONFIG)
        self.rules = rules if rules is not None else stage_rules('S1')
        self.features = tuple(name.upper() for name in features)
        self.feature_config = feature_config or {}
        self._handlers: dict[str, list[Callable]] = {}
        self.env: Env = Env(path if path is not None else self.config.map_file,
                            self.config, rules=self.rules)
        self.env.game = self
        assert self.env.player is not None
        self.player: Player  = self.env.player
        # Factories create a separate controller (and strategy memory) per agent.
        self.controllers: dict[Agent, Controller] = {
            self.player: player_controller(self.player),
        }
        for ghost in self.env.ghosts:
            self.controllers[ghost] = ghost_controller(ghost)
        self.status = 'running'  # running, won, lost, quit
        for name in self.features:
            if name == 'C1':
                continue
            install = getattr(import_module(f'tasks.advanced.{name.lower()}'), 'install')
            install(self, self.feature_config.get(name, {}))
        self.check_result()

    def on(self, event: str, callback: Callable[['Game', dict], None]) -> None:
        """Register one handler; callbacks may update the event context."""
        self._handlers.setdefault(event, []).append(callback)

    def emit(self, event: str, **values) -> dict:
        context = dict(values)
        for callback in self._handlers.get(event, ()):
            callback(self, context)
        return context

    @classmethod
    def for_stage(cls, stage: str, *, path: str | Path | None = None,
                  config: GameConfig | None = None,
                  implementation: ModuleType | None = None) -> 'Game':
        selected_map, settings, rules, player_controller, ghost_controller = stage_setup(
            stage, path=path, config=config, implementation=implementation)
        return cls(selected_map, player_controller, ghost_controller,
                   config=settings, rules=rules)

    @classmethod
    def for_advanced(cls, features: tuple[str, ...], *,
                     path: str | Path | None = None,
                     config: GameConfig | None = None,
                     feature_config: dict[str, dict] | None = None,
                     implementation: ModuleType | None = None,
                     ghost_controller: Callable[[Agent], Controller] | None = None) -> 'Game':
        """Run selected optional tasks over the completed S1-S5 rules."""
        names = tuple(name.upper() for name in features)
        if len(names) != len(set(names)) or any(
                name not in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2') for name in names):
            raise ValueError('Unknown or duplicate advanced task')
        names = tuple(sorted(names, key=('A1', 'A2', 'B1', 'B2', 'C1', 'C2').index))
        selected_map, settings, rules, player_controller, ghost_controller_factory = stage_setup(
            'S5', path=path, config=config, implementation=implementation)
        options = dict(feature_config or {})
        if 'C1' in names:
            if path is not None:
                raise ValueError('C1 creates the map; do not also pass a map path')
            from tasks.advanced.c1 import generate_map
            generation = options.get('C1', {})
            selected_map = generate_map(generation['width'], generation['height'],
                                        generation['seed'])
            if 'C2' in names:
                gate_config = dict(options.get('C2', {}))
                gates = [dict(gate) for gate in gate_config.get('gates', [])]
                available = [(x, y) for y, row in enumerate(selected_map)
                             for x, tile in enumerate(row) if tile == ' ']
                taken = {(gate['x'], gate['y']) for gate in gates
                         if 'x' in gate and 'y' in gate}
                for gate in gates:
                    if 'x' not in gate or 'y' not in gate:
                        position = next((point for point in available
                                         if point not in taken), None)
                        if position is None:
                            raise ValueError('Generated map has no room for a gate')
                        gate['x'], gate['y'] = position
                        taken.add(position)
                gate_config['gates'] = gates
                options['C2'] = gate_config
        return cls(selected_map, player_controller,
                   ghost_controller if ghost_controller is not None else
                   ghost_controller_factory,
                   config=settings, rules=rules, features=names,
                   feature_config=options)

    def check_result(self) -> str:
        """Death takes priority over eating the last point in the same move."""
        if self.status != 'running':
            return self.status
        if self.rules is not None and self.rules.check_result is not None:
            result = self.rules.check_result(self)
            if result not in ('running', 'won', 'lost'):
                raise ValueError(f'Invalid game result: {result!r}')
            self.status = result
        return self.status

    def step(self, direction: tuple[int, int] | None = None) -> str:
        """One turn: player first, then each living ghost.

        Waiting or walking into a wall still uses a turn. Collecting the last
        relic wins immediately if the player survives the collision there.
        Normally controllers supply actions. An explicit player direction is
        still accepted for tests and manual, single-step experiments.
        """
        if self.status != 'running':
            return self.status

        if direction is None:
            direction = self.controller_direction(self.player)
        if direction not in DIRECTIONS + [WAIT]:
            raise ValueError('Invalid direction')
        self.emit('turn_start')
        # The previous turn has elapsed. A new enchanted crystal refreshes
        # the timer below, before collisions, for the full duration.
        if self.rules is not None and self.rules.advance_power is not None:
            self.rules.advance_power(self.player)
        self.emit('before_player_move', direction=direction,
                  target=(self.player.x + direction[0], self.player.y + direction[1]))
        if self.player.move(direction):
            self.player.collect_item()
            self.emit('player_enter', x=self.player.x, y=self.player.y)
        self.env.resolve_collisions()
        if self.check_result() != 'running':
            self.emit('turn_end')
            return self.status

        for ghost in self.env.ghosts:
            if not ghost.live:
                continue
            selected = self.emit('ghost_action', ghost=ghost,
                                 direction=self.controller_direction(ghost))['direction']
            if selected not in DIRECTIONS + [WAIT]:
                raise ValueError(f'Advanced ghost action is invalid: {selected!r}')
            if not self.emit('before_ghost_move', ghost=ghost,
                             direction=selected, skip=False)['skip']:
                ghost.move(selected)
            self.env.resolve_collisions()
            if self.check_result() != 'running':
                break
        self.emit('turn_end')
        return self.status

    def controller_direction(self, agent: Agent) -> tuple[int, int]:
        controller = self.controllers[agent]
        direction = controller.get_direction()
        if direction not in DIRECTIONS + [WAIT]:
            raise ValueError(f'{type(controller).__name__} returned invalid direction: {direction!r}')
        return direction

    def run(self) -> None:
        """Keyboard-driven terminal demo, using one action per entered command."""
        keyboard = KeyboardController(self.player, continuous=False)
        self.controllers[self.player] = keyboard
        print('W/A/S/D + Enter: move | Enter: wait | Q: quit')
        self.env.print()
        print(f'Score: {self.player.score}')
        while self.status == 'running':
            try:
                command = input('Move: ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.status = 'quit'
                break
            if command == 'q':
                self.status = 'quit'
                break
            if not keyboard.handle_key(command):
                print('Use W, A, S, D, Enter or Q.')
                continue
            self.step()
            self.env.print()
            print(f'Score: {self.player.score}')
            if self.player.state:
                print(f'Enchant: {self.player.state} turns remaining')

        messages = {'won': 'You win!', 'lost': 'Game over!', 'quit': 'Goodbye!'}
        print(messages[self.status])


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run the terminal game')
    parser.add_argument('--config', default=TERMINAL_CONFIG, help='Path to a map JSON profile')
    args = parser.parse_args()
    Game(config=load_config(args.config), rules=stage_rules('S5')).run()
