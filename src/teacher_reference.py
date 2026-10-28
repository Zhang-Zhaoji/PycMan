"""Teacher-only reference rules. Excluded from the student package."""

import random

from codebook import POINT, POWER, ROAD, WALL
from controller import DIRECTIONS, WAIT
from rules import GameRules


def can_walk(env, x, y):
    return 0 <= x < env.cols and 0 <= y < env.rows and env.get_tile(x, y) != WALL


def move(agent, direction):
    if direction not in DIRECTIONS + [WAIT]:
        raise ValueError('Invalid direction')
    if not agent.live or direction == WAIT:
        return False
    dx, dy = direction
    x, y = agent.x + dx, agent.y + dy
    if not agent.env.can_walk(x, y):
        return False
    agent.moveForward((x, y))
    return True


def advance_power(player):
    player.state = max(0, player.state - 1)


def collect_item(player):
    env = player.env
    tile = env.get_tile(player.x, player.y)
    if tile == POINT:
        env.set_tile(player.x, player.y, ROAD)
        player.score += env.config.get_point
    elif tile == POWER:
        env.set_tile(player.x, player.y, ROAD)
        player.score += env.config.get_power
        player.state = env.config.power_turns


def resolve_collisions(env):
    player = env.player
    if player is None or not player.live:
        return
    for ghost in env.ghosts:
        if ghost.live and (player.x, player.y) == (ghost.x, ghost.y):
            if player.state > 0:
                ghost.live = False
                player.score += env.config.beat_ghost
            else:
                player.live = False
                player.score = 0
                return


def check_result(game):
    if not game.player.live:
        return 'lost'
    if not any(POINT in row or POWER in row for row in game.env.env):
        return 'won'
    return 'running'


def legal_directions(controller):
    agent = controller.agent
    return [(dx, dy) for dx, dy in DIRECTIONS
            if agent.env.can_walk(agent.x + dx, agent.y + dy)]


def random_direction(controller):
    choices = controller.legal_directions()
    return random.choice(choices) if choices else WAIT


def handle_key(controller, key):
    action = controller.KEYS.get(key.lower())
    if action is None:
        return False
    controller.pending = action
    return True


def continuous_direction(controller):
    if controller.pending == WAIT or controller.pending in controller.legal_directions():
        controller.direction = controller.pending
    return controller.direction


def reference_rules():
    return GameRules(
        can_walk=can_walk,
        move=move,
        advance_power=advance_power,
        collect_item=collect_item,
        resolve_collisions=resolve_collisions,
        check_result=check_result,
        legal_directions=legal_directions,
        random_direction=random_direction,
        handle_key=handle_key,
        continuous_direction=continuous_direction,
    )
