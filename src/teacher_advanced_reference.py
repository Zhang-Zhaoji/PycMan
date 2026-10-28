"""Teacher-only sample implementations for validating advanced test scenarios."""

from collections import Counter, deque
import random

from controller import DIRECTIONS, WAIT


def _position(item):
    return item['x'], item['y']


def install_a1(game, config):
    runes = {_position(item) for item in config['runes']}
    frozen = {ghost: 0 for ghost in game.env.ghosts}
    radius, turns = config['radius'], config['turns']

    def tick(game, event):
        for ghost in frozen:
            frozen[ghost] = max(0, frozen[ghost] - 1)

    def collect(game, event):
        position = event['x'], event['y']
        if position not in runes:
            return
        runes.remove(position)
        for ghost in game.env.ghosts:
            if ghost.live and abs(ghost.x - position[0]) + abs(ghost.y - position[1]) <= radius:
                frozen[ghost] = turns

    def hold(game, event):
        event['skip'] = frozen[event['ghost']] > 0

    def visuals(game, event):
        event['tiles'].extend({'kind': 'rune', 'x': x, 'y': y} for x, y in runes)

    game.on('turn_start', tick)
    game.on('player_enter', collect)
    game.on('before_ghost_move', hold)
    game.on('visuals', visuals)


def install_a2(game, config):
    keys = {_position(item): item['color'] for item in config['keys']}
    doors = {_position(item): {'color': item['color'], 'open': False}
             for item in config['doors']}
    inventory = Counter()

    def can_walk(game, event):
        door = doors.get((event['x'], event['y']))
        if door is not None and not door['open']:
            event['allowed'] = False

    def before_move(game, event):
        door = doors.get(event['target'])
        if door is not None and not door['open'] and inventory[door['color']] > 0:
            inventory[door['color']] -= 1
            door['open'] = True

    def collect(game, event):
        color = keys.pop((event['x'], event['y']), None)
        if color is not None:
            inventory[color] += 1

    def visuals(game, event):
        event['tiles'].extend({'kind': 'key', 'x': x, 'y': y, 'color': color}
                              for (x, y), color in keys.items())
        event['tiles'].extend({'kind': 'door', 'x': x, 'y': y,
                               'color': door['color'], 'open': door['open']}
                              for (x, y), door in doors.items())

    game.on('can_walk', can_walk)
    game.on('before_player_move', before_move)
    game.on('player_enter', collect)
    game.on('visuals', visuals)


def install_b1(game, config):
    sight, memory = config['sight'], config['memory']
    routes = [[tuple(point) for point in route] for route in config['routes']]
    for ghost, route in zip(game.env.ghosts, routes):
        controller = game.controllers[ghost]
        controller.patrol_route = route
        controller.patrol_index = 0
        controller.alert = False
        controller.unseen = 0

    def visible(ghost):
        player = game.player
        if ghost.x != player.x and ghost.y != player.y:
            return False
        if abs(ghost.x - player.x) + abs(ghost.y - player.y) > sight:
            return False
        dx = (player.x > ghost.x) - (player.x < ghost.x)
        dy = (player.y > ghost.y) - (player.y < ghost.y)
        x, y = ghost.x + dx, ghost.y + dy
        while (x, y) != (player.x, player.y):
            if not game.env.can_walk(x, y):
                return False
            x, y = x + dx, y + dy
        return True

    def decide(game, event):
        ghost = event['ghost']
        controller = game.controllers[ghost]
        if visible(ghost):
            controller.alert = True
            controller.unseen = 0
        elif controller.alert:
            controller.unseen += 1
            if controller.unseen >= memory:
                controller.alert = False
        if controller.alert:
            event['direction'] = controller.basic_chase_direction()
            return
        route = controller.patrol_route
        if not route:
            event['direction'] = WAIT
            return
        if (ghost.x, ghost.y) == route[controller.patrol_index]:
            controller.patrol_index = (controller.patrol_index + 1) % len(route)
        event['direction'] = controller.step_toward(route[controller.patrol_index])

    game.on('ghost_action', decide)


def install_b2(game, config):
    def decide(game, event):
        ghost = event['ghost']
        if 'B1' in game.features and not game.controllers[ghost].alert:
            return
        start = ghost.x, ghost.y
        goal = game.player.x, game.player.y
        if start == goal:
            event['direction'] = WAIT
            return
        queue = deque([(start, WAIT)])
        seen = {start}
        while queue:
            (x, y), first = queue.popleft()
            for direction in DIRECTIONS:
                dx, dy = direction
                neighbor = (x + dx, y + dy)
                if neighbor in seen or not game.env.can_walk(*neighbor):
                    continue
                next_first = direction if first == WAIT else first
                if neighbor == goal:
                    event['direction'] = next_first
                    return
                seen.add(neighbor)
                queue.append((neighbor, next_first))
        event['direction'] = WAIT

    game.on('ghost_action', decide)


def generate_map(width, height, seed):
    rng = random.Random(seed)
    rows = [['#'] * width for _ in range(height)]
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            rows[y][x] = ' '
    rows[1][1], rows[1][2], rows[height - 2][width - 2] = 'c', '.', 'g'
    candidates = [(x, y) for y in range(2, height - 2)
                  for x in range(2, width - 2)]
    x, y = rng.choice(candidates)
    rows[y][x] = '#'
    return [''.join(row) for row in rows]


def install_c2(game, config):
    gates = {_position(item): {'period': item['period'], 'phase': 0,
                               'planned': item['open'], 'open': item['open']}
             for item in config['gates']}

    def can_walk(game, event):
        gate = gates.get((event['x'], event['y']))
        if gate is not None and not gate['open']:
            event['allowed'] = False

    def tick(game, event):
        occupants = {(game.player.x, game.player.y)} if game.player.live else set()
        occupants.update((ghost.x, ghost.y) for ghost in game.env.ghosts if ghost.live)
        for position, gate in gates.items():
            gate['phase'] += 1
            if gate['phase'] % gate['period'] == 0:
                gate['planned'] = not gate['planned']
            gate['open'] = gate['planned'] or position in occupants

    def visuals(game, event):
        event['tiles'].extend({'kind': 'gate', 'x': x, 'y': y, 'open': gate['open']}
                              for (x, y), gate in gates.items())

    game.on('can_walk', can_walk)
    game.on('turn_end', tick)
    game.on('visuals', visuals)
