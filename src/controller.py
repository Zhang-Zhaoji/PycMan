"""Controllers choose directions; they must not move agents or change the map.

No pygame dependency: key names arrive from the GUI or terminal as strings.
"""
from utils import Agent

DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
WAIT = (0, 0)


class Controller:
    """Choose actions; task implementations may add their own strategy fields."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def get_direction(self) -> tuple[int, int]:
        """Return one cardinal step or (0, 0) to wait. Override in a strategy."""
        raise NotImplementedError

    def handle_key(self, key: str) -> bool:
        """Return True if a movement key was accepted; AI ignores keys."""
        return False

    def legal_directions(self) -> list[tuple[int, int]]:
        rules = self.agent.env.rules
        if rules is not None and rules.legal_directions is not None:
            return rules.legal_directions(self)
        raise RuntimeError('No legal_directions rule is configured')

    def step_toward(self, target: tuple[int, int]) -> tuple[int, int]:
        """Simple local movement for B1; this does not find routes around walls."""
        x, y = self.agent.x, self.agent.y
        tx, ty = target
        candidates = []
        if tx != x:
            candidates.append((1 if tx > x else -1, 0))
        if ty != y:
            candidates.append((0, 1 if ty > y else -1))
        legal = self.legal_directions()
        return next((direction for direction in candidates if direction in legal), WAIT)

    def basic_chase_direction(self) -> tuple[int, int]:
        """Baseline pursuit for B1 when B2 is not selected."""
        player = self.agent.env.player
        return self.step_toward((player.x, player.y))


class KeyboardController(Controller):
    """Keyboard state may be extended without changing the public methods."""

    KEYS = {
        'left': (-1, 0), 'a': (-1, 0),
        'right': (1, 0), 'd': (1, 0),
        'up': (0, -1), 'w': (0, -1),
        'down': (0, 1), 's': (0, 1), '': WAIT,
    }

    def __init__(self, agent: Agent, continuous: bool = True) -> None:
        super().__init__(agent)
        self.continuous: bool = continuous
        self.direction: tuple[int, int] = WAIT
        self.pending: tuple[int, int] = WAIT

    def handle_key(self, key: str) -> bool:
        rules = self.agent.env.rules
        if self.continuous and rules is not None and rules.handle_key is not None:
            return rules.handle_key(self, key)
        if self.continuous:
            return False
        key = key.lower()
        if key not in self.KEYS:
            return False
        self.pending = self.KEYS[key]
        return True

    def get_direction(self) -> tuple[int, int]:
        if not self.continuous:
            # Terminal: each entered command is exactly one requested action.
            direction = self.pending
            self.pending = WAIT
            return direction
        rules = self.agent.env.rules
        if rules is not None and rules.continuous_direction is not None:
            return rules.continuous_direction(self)
        return self.direction


class RandomController(Controller):
    def get_direction(self) -> tuple[int, int]:
        rules = self.agent.env.rules
        if rules is not None and rules.random_direction is not None:
            return rules.random_direction(self)
        return WAIT


class ImmediateKeyboard(KeyboardController):
    """Keyboard baseline before S5; discard a blocked new turn request."""

    def __init__(self, agent: Agent, continuous: bool = True) -> None:
        super().__init__(agent, continuous)
        self.immediate_request: tuple[int, int] | None = None

    def handle_key(self, key: str) -> bool:
        if not self.continuous:
            return super().handle_key(key)
        action = self.KEYS.get(key.lower())
        if action is None:
            return False
        self.immediate_request = action
        return True

    def get_direction(self) -> tuple[int, int]:
        if not self.continuous:
            return super().get_direction()
        if self.immediate_request is not None:
            requested = self.immediate_request
            agent = self.agent
            if requested == WAIT or agent.env.can_walk(
                    agent.x + requested[0], agent.y + requested[1]):
                self.direction = requested
            self.immediate_request = None
        return self.direction


class WaitingGhost(Controller):
    def get_direction(self) -> tuple[int, int]:
        return WAIT

class BFSController(Controller):
    ...

class DFSController(Controller):
    ...


class AStarController(Controller):
    ...
