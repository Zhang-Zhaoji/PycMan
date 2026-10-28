"""Observable A1-C2 behavior on configured maps and action sequences."""

import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from collections import deque
import unittest

from .scenarios import run_case


def distance(env, start: tuple[int, int], goal: tuple[int, int]) -> int | None:
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (x, y), steps = queue.popleft()
        if (x, y) == goal:
            return steps
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            neighbor = (x + dx, y + dy)
            if neighbor not in seen and env.can_walk(*neighbor):
                seen.add(neighbor)
                queue.append((neighbor, steps + 1))
    return None


def assert_generated(test: unittest.TestCase, rows: list[str],
                     width: int, height: int) -> None:
    test.assertEqual(len(rows), height)
    test.assertTrue(all(isinstance(row, str) and len(row) == width for row in rows))
    test.assertTrue(all(set(row) <= set('# .ocg') for row in rows))
    test.assertEqual(rows[0], '#' * width)
    test.assertEqual(rows[-1], '#' * width)
    test.assertTrue(all(row[0] == row[-1] == '#' for row in rows))
    text = ''.join(rows)
    test.assertEqual(text.count('c'), 1)
    test.assertGreaterEqual(text.count('g'), 1)
    test.assertGreaterEqual(text.count('.'), 1)
    start = next((x, y) for y, row in enumerate(rows)
                 for x, char in enumerate(row) if char == 'c')
    walkable = {(x, y) for y, row in enumerate(rows)
                for x, char in enumerate(row) if char != '#'}
    queue = deque([start])
    reached = {start}
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            neighbor = (x + dx, y + dy)
            if neighbor in walkable and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    test.assertEqual(reached, walkable)


class AdvancedTaskTest(unittest.TestCase):
    def test_a1_freeze_radius_and_duration(self):
        _, states = run_case('a1_freeze')
        self.assertEqual(states[1]['score'], 0)
        self.assertEqual(states[1]['ghosts'][0], (4, 1))
        self.assertEqual(states[2]['ghosts'][0], (4, 1))
        self.assertEqual(states[3]['ghosts'][0], (3, 1))
        self.assertEqual(states[1]['ghosts'][1], (6, 3))

    def test_a1_refresh_and_frozen_collision(self):
        _, refreshed = run_case('a1_refresh')
        self.assertEqual(refreshed[3]['ghosts'][0], (4, 1))
        self.assertEqual(refreshed[4]['ghosts'][0], (3, 1))
        _, collision = run_case('a1_collision')
        self.assertEqual(collision[3]['status'], 'lost')
        self.assertEqual(collision[3]['ghosts'][0], (4, 1))

    def test_a2_matching_key_opens_one_door(self):
        _, states = run_case('a2_red_doors')
        self.assertEqual(states[1]['player'], (2, 1))
        self.assertEqual(states[1]['score'], 0)
        self.assertEqual(states[2]['player'], (3, 1))
        self.assertTrue(states[2]['walkable'][(3, 1)])
        self.assertEqual(states[3]['player'], (4, 1))
        self.assertEqual(states[4]['player'], (4, 1))
        self.assertFalse(states[4]['walkable'][(5, 1)])

    def test_a2_closed_door_blocks_ghost(self):
        _, states = run_case('a2_ghost_blocked')
        self.assertEqual(states[0]['ghosts'][0], (4, 1))
        self.assertEqual(states[1]['ghosts'][0], (4, 1))

    def test_b1_visibility_and_patrol(self):
        _, visible = run_case('b1_visible')
        _, blocked = run_case('b1_blocked')
        self.assertEqual(visible[1]['ghosts'][0], (3, 1))
        self.assertEqual(blocked[1]['ghosts'][0], (5, 1))

    def test_b2_shortest_detour(self):
        game, states = run_case('b2_detour')
        for before, after in zip(states, states[1:]):
            original = distance(game.env, before['ghosts'][0], after['player'])
            updated = distance(game.env, after['ghosts'][0], after['player'])
            self.assertIsNotNone(original)
            self.assertEqual(updated, original - 1)

    def test_b2_unreachable_waits(self):
        _, states = run_case('b2_unreachable')
        self.assertEqual(states[0]['ghosts'], states[1]['ghosts'])

    def test_c1_map_shape_and_reproducibility(self):
        from tasks.advanced.c1 import generate_map

        for width, height in ((9, 7), (8, 10)):
            with self.subTest(size=(width, height)):
                rows = generate_map(width, height, 42)
                assert_generated(self, rows, width, height)
                self.assertEqual(rows, generate_map(width, height, 42))
        layouts = {tuple(generate_map(9, 7, seed)) for seed in range(10)}
        self.assertGreaterEqual(len(layouts), 2)

    def test_c2_independent_periods(self):
        _, states = run_case('c2_periods')
        self.assertEqual(states[0]['walkable'], {(2, 1): True, (4, 1): False})
        self.assertEqual(states[1]['walkable'], {(2, 1): True, (4, 1): False})
        self.assertEqual(states[2]['walkable'], {(2, 1): False, (4, 1): False})
        self.assertEqual(states[3]['walkable'], {(2, 1): False, (4, 1): True})

    def test_c2_invalid_and_finished_turns_do_not_advance(self):
        game, states = run_case('c2_periods')
        expected = states[-1]['walkable']
        with self.assertRaises(ValueError):
            game.step((2, 0))
        self.assertEqual({position: game.env.can_walk(*position)
                          for position in expected}, expected)
        game.status = 'won'
        self.assertEqual(game.step((0, 0)), 'won')
        self.assertEqual({position: game.env.can_walk(*position)
                          for position in expected}, expected)


class AdvancedIntegrationTest(unittest.TestCase):
    """An additional full-game scenario is required for each 15-point task."""

    def test_integration_a1(self):
        _, states = run_case('a1_outside')
        self.assertEqual(states[1]['ghosts'][0], (3, 1))

    def test_integration_a2(self):
        _, states = run_case('a2_wrong_color')
        self.assertEqual(states[1]['player'], (2, 1))
        self.assertEqual(states[2]['player'], (2, 1))
        self.assertFalse(states[2]['walkable'][(3, 1)])

    def test_integration_b1(self):
        _, states = run_case('b1_visible')
        self.assertNotEqual(states[2]['ghosts'][0], (4, 1))
        waypoint = (5, 1)
        before = sum(abs(a - b) for a, b in zip(states[2]['ghosts'][0], waypoint))
        after = sum(abs(a - b) for a, b in zip(states[3]['ghosts'][0], waypoint))
        self.assertLess(after, before)

    def test_integration_b2(self):
        game, states = run_case('b2_replan')
        for before, after in zip(states, states[1:]):
            original = distance(game.env, before['ghosts'][0], after['player'])
            updated = distance(game.env, after['ghosts'][0], after['player'])
            self.assertEqual(updated, original - 1)

    def test_integration_c1(self):
        game, states = run_case('c1_generated')
        self.assertEqual((game.env.cols, game.env.rows), (9, 7))
        self.assertEqual(states[0]['status'], 'running')
        self.assertEqual(len(states), 2)
        self.assertIn(states[1]['status'], ('running', 'won', 'lost'))
        self.assertTrue(game.env.can_walk(game.player.x, game.player.y))
        self.assertGreaterEqual(len(game.env.ghosts), 1)

    def test_integration_c2(self):
        _, states = run_case('c2_occupied')
        self.assertEqual(states[1]['player'], (2, 1))
        self.assertTrue(states[2]['walkable'][(2, 1)])
        self.assertEqual(states[3]['player'], (3, 1))
        self.assertFalse(states[3]['walkable'][(2, 1)])


class AdvancedCombinationTest(unittest.TestCase):
    """Run selected pairs together, with the same configured action sequence."""

    def test_combo_a2_c2(self):
        _, states = run_case('a2_c2')
        self.assertEqual(states[2]['player'], (3, 1))
        self.assertEqual(states[3]['player'], (3, 1))
        self.assertEqual(states[5]['player'], (4, 1))

    def test_combo_b1_b2(self):
        _, states = run_case('b1_b2')
        self.assertEqual(states[1]['ghosts'][0], (3, 1))
        waypoint = (5, 1)
        before = sum(abs(a - b) for a, b in zip(states[2]['ghosts'][0], waypoint))
        after = sum(abs(a - b) for a, b in zip(states[3]['ghosts'][0], waypoint))
        self.assertLess(after, before)

    def test_combo_c1_c2(self):
        game, _ = run_case('c1_c2')
        gates = game.feature_config['C2']['gates']
        self.assertEqual(len(gates), 2)
        self.assertNotEqual((gates[0]['x'], gates[0]['y']),
                            (gates[1]['x'], gates[1]['y']))
        self.assertFalse(game.env.can_walk(gates[0]['x'], gates[0]['y']))


if __name__ == '__main__':
    unittest.main()
