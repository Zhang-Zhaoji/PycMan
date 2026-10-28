"""Public S1-S5 behavior checks. Failures are expected before implementation."""

import unittest
from pathlib import Path

from tasks import basic as student
from controller import Controller, KeyboardController
from game import Game
from rules import GameRules
from utils import Env, POINT, ROAD

MAP_DIR = Path(__file__).resolve().parents[1] / 'assets/maps/basic'


class PublicTaskTest(unittest.TestCase):
    def env(self, name: str, *, allowed: set[tuple[int, int]] | None = None) -> Env:
        walkable = student.can_walk if allowed is None else (
            lambda env, x, y: (x, y) in allowed)
        return Env(MAP_DIR / name, rules=GameRules(can_walk=walkable))

    def test_s1_move_and_wait(self):
        env = self.env('corridor.txt')
        player = env.player
        self.assertTrue(student.move(player, (1, 0)))
        self.assertEqual((player.x, player.y), (2, 1))
        self.assertFalse(student.move(player, (0, 0)))
        self.assertEqual((player.x, player.y), (2, 1))
        self.assertFalse(student.move(player, (0, -1)))
        self.assertEqual((player.x, player.y), (2, 1))

    def test_s1_walkability(self):
        env = self.env('corridor.txt')
        self.assertTrue(student.can_walk(env, 2, 1))
        self.assertFalse(student.can_walk(env, 0, 1))
        self.assertFalse(student.can_walk(env, -1, 1))
        self.assertFalse(student.can_walk(env, 5, 1))

    def test_s1_invalid_direction(self):
        env = self.env('corridor.txt')
        with self.assertRaises(ValueError):
            student.move(env.player, (2, 0))
        self.assertEqual((env.player.x, env.player.y), (1, 1))

    def test_s2_regular_and_power_items(self):
        env = self.env('items.txt')
        player = env.player
        player.x = 2
        student.collect_item(player)
        self.assertEqual(player.score, env.config.get_point)
        self.assertEqual(env.get_tile(2, 1), ROAD)
        student.collect_item(player)
        self.assertEqual(player.score, env.config.get_point)
        player.x = 3
        student.collect_item(player)
        self.assertEqual(player.score, env.config.get_point + env.config.get_power)
        self.assertEqual(player.state, env.config.power_turns)
        self.assertEqual(env.get_tile(3, 1), ROAD)

    def test_s2_power_timer(self):
        env = self.env('corridor.txt')
        player = env.player
        player.state = 2
        student.advance_power(player)
        self.assertEqual(player.state, 1)
        student.advance_power(player)
        student.advance_power(player)
        self.assertEqual(player.state, 0)

    def test_s3_normal_and_powered_collision(self):
        env = self.env('collision.txt')
        player, ghost = env.player, env.ghosts[0]
        player.x = ghost.x
        player.score = 10
        student.resolve_collisions(env)
        self.assertFalse(player.live)
        self.assertEqual(player.score, 0)

        env = self.env('collision.txt')
        player, ghost = env.player, env.ghosts[0]
        player.x = ghost.x
        player.state = 1
        student.resolve_collisions(env)
        self.assertTrue(player.live)
        self.assertFalse(ghost.live)
        self.assertEqual(player.score, env.config.beat_ghost)
        student.resolve_collisions(env)
        self.assertEqual(player.score, env.config.beat_ghost)

    def test_s3_result_and_death_priority(self):
        game = Game(MAP_DIR / 'corridor.txt')
        self.assertEqual(student.check_result(game), 'running')
        for y, row in enumerate(game.env.env):
            for x, tile in enumerate(row):
                if tile == POINT:
                    game.env.set_tile(x, y, ROAD)
        self.assertEqual(student.check_result(game), 'won')
        game.player.live = False
        self.assertEqual(student.check_result(game), 'lost')

    def test_s4_legal_directions(self):
        env = self.env('junction.txt', allowed={(2, 1), (3, 2), (4, 1)})
        controller = Controller(env.player)
        before = [row[:] for row in env.env]
        self.assertCountEqual(student.legal_directions(controller),
                              [(1, 0), (0, 1), (-1, 0)])
        self.assertEqual((env.player.x, env.player.y), (3, 1))
        self.assertEqual(env.env, before)

    def test_s4_random_direction_and_trapped(self):
        env = self.env('corridor.txt', allowed={(2, 1)})
        controller = Controller(env.player)
        controller.legal_directions = lambda: student.legal_directions(controller)
        self.assertIn(student.random_direction(controller), [(1, 0)])
        env = self.env('trapped.txt', allowed=set())
        controller = Controller(env.player)
        controller.legal_directions = lambda: student.legal_directions(controller)
        self.assertEqual(student.random_direction(controller), (0, 0))

    def test_s5_key_handling(self):
        env = self.env('corridor.txt', allowed={(2, 1), (3, 1)})
        keyboard = KeyboardController(env.player)
        keyboard.legal_directions = lambda: [(1, 0)]
        self.assertTrue(student.handle_key(keyboard, 'RIGHT'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        self.assertFalse(student.handle_key(keyboard, 'invalid'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        self.assertTrue(student.handle_key(keyboard, ''))
        self.assertEqual(student.continuous_direction(keyboard), (0, 0))

    def test_s5_buffered_turn(self):
        env = self.env('buffered_turn.txt', allowed={(2, 1), (3, 1), (3, 2), (4, 1), (5, 1)})
        keyboard = KeyboardController(env.player)
        keyboard.legal_directions = lambda: {
            1: [(1, 0)], 2: [(1, 0), (-1, 0)],
            3: [(1, 0), (0, 1), (-1, 0)],
        }[env.player.x]
        self.assertTrue(student.handle_key(keyboard, 'right'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        env.player.x += 1
        self.assertTrue(student.handle_key(keyboard, 'down'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        env.player.x += 1
        self.assertEqual(student.continuous_direction(keyboard), (0, 1))

    def test_s5_new_request_replaces_old(self):
        env = self.env('buffered_turn.txt', allowed={(2, 1), (3, 1), (3, 2), (4, 1), (5, 1)})
        keyboard = KeyboardController(env.player)
        keyboard.legal_directions = lambda: {
            1: [(1, 0)], 2: [(1, 0), (-1, 0)],
            3: [(1, 0), (0, 1), (-1, 0)],
        }[env.player.x]
        student.handle_key(keyboard, 'right')
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        env.player.x += 1
        student.handle_key(keyboard, 'down')
        student.handle_key(keyboard, 'up')
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        env.player.x += 1
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))

    def test_s5_wait_and_resume(self):
        env = self.env('corridor.txt', allowed={(2, 1), (3, 1)})
        keyboard = KeyboardController(env.player)
        keyboard.legal_directions = lambda: [(1, 0)]
        self.assertTrue(student.handle_key(keyboard, 'right'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))
        self.assertTrue(student.handle_key(keyboard, ''))
        self.assertEqual(student.continuous_direction(keyboard), (0, 0))
        self.assertTrue(student.handle_key(keyboard, 'right'))
        self.assertEqual(student.continuous_direction(keyboard), (1, 0))


class BasicIntegrationTest(unittest.TestCase):
    """Cumulative checks required for each stage's points."""

    def test_integration_s1(self):
        game = Game.for_stage('S1', path=MAP_DIR / 'corridor.txt')
        game.step((1, 0))
        self.assertEqual((game.player.x, game.player.y), (2, 1))
        self.assertEqual(game.env.get_tile(2, 1), POINT)

    def test_integration_s2(self):
        game = Game.for_stage('S2', path=MAP_DIR / 'items.txt')
        game.step((1, 0))
        self.assertEqual(game.player.score, game.config.get_point)
        self.assertEqual(game.env.get_tile(2, 1), ROAD)
        game.step((1, 0))
        self.assertEqual(game.player.state, game.config.power_turns)

    def test_integration_s3(self):
        game = Game.for_stage('S3', path=MAP_DIR / 'collision.txt')
        self.assertEqual(game.step((1, 0)), 'lost')
        game = Game.for_stage('S3', path=MAP_DIR / 'collision.txt')
        game.player.state = 2
        game.step((1, 0))
        self.assertTrue(game.player.live)
        self.assertFalse(game.env.ghosts[0].live)

    def test_integration_s4(self):
        game = Game.for_stage('S4')
        ghost = game.env.ghosts[0]
        start = (ghost.x, ghost.y)
        game.step((0, 0))
        self.assertNotEqual((ghost.x, ghost.y), start)
        self.assertTrue(game.env.can_walk(ghost.x, ghost.y))

    def test_integration_s5(self):
        game = Game.for_stage('S5', path=MAP_DIR / 'buffered_turn.txt')
        keyboard = game.controllers[game.player]
        self.assertTrue(keyboard.handle_key('right'))
        game.step()
        self.assertEqual((game.player.x, game.player.y), (2, 1))
        self.assertTrue(keyboard.handle_key('down'))
        game.step()
        self.assertEqual((game.player.x, game.player.y), (3, 1))
        game.step()
        self.assertEqual((game.player.x, game.player.y), (3, 2))


if __name__ == '__main__':
    unittest.main()
