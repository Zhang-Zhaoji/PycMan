"""Pygame handles input and drawing; Game owns the game rules."""
from pathlib import Path
from types import ModuleType
from typing import Callable

import pygame

from game import Game, stage_setup
from config import DEFAULT_SETTINGS, PROJECT_ROOT, TURN_MS, GameConfig, load_config
from controller import Controller, KeyboardController, RandomController
from rules import GameRules
from utils import Agent, WALL, POINT, POWER

ARCADE_MAP = str(DEFAULT_SETTINGS.map_file)
TILE = 40
MARGIN = 24
HEADER = 100
BG = (10, 15, 29)
TEXT = (231, 240, 255)
MUTED = (132, 154, 184)
YELLOW = (255, 214, 82)
FLASH_TURNS = DEFAULT_SETTINGS.flash_turns
FLASH_INTERVAL = DEFAULT_SETTINGS.flash_interval


class GUI:
    @classmethod
    def for_stage(cls, stage: str, *, path: str | Path | None = None,
                  config: GameConfig | None = None,
                  implementation: ModuleType | None = None) -> 'GUI':
        selected_map, settings, rules, player_controller, ghost_controller = stage_setup(
            stage, path=path, config=config, implementation=implementation)
        return cls(selected_map, player_controller, ghost_controller,
                   config=settings, rules=rules)

    @classmethod
    def for_advanced(cls, features: tuple[str, ...], *,
                     path: str | Path | None = None,
                     config: GameConfig | None = None,
                     feature_config: dict[str, dict] | None = None,
                     implementation: ModuleType | None = None) -> 'GUI':
        settings = config if config is not None else load_config()
        return cls(config=settings, game_factory=lambda: Game.for_advanced(
            features, path=path, config=settings, feature_config=feature_config,
            implementation=implementation))

    def __init__(self, path: str | Path | None = None,
                 player_controller: Callable[[Agent], Controller] = KeyboardController,
                 ghost_controller: Callable[[Agent], Controller] = RandomController,
                 *, config: GameConfig | None = None,
                 rules: GameRules | None = None,
                 game_factory: Callable[[], Game] | None = None) -> None:
        pygame.init()
        self.config = config if config is not None else load_config()
        self.path = path
        self.player_controller_factory = player_controller
        self.ghost_controller_factory = ghost_controller
        self.rules = rules
        self.game_factory = game_factory
        self.reset()
        self.width = max(660, self.game.env.cols * TILE + 2 * MARGIN)
        self.height = HEADER + self.game.env.rows * TILE + 100
        self.board_x = (self.width - self.game.env.cols * TILE) // 2
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.key.stop_text_input()  # Game hotkeys do not need IME text entry.
        self.restart_button = pygame.Rect(self.width - 154, self.height - 44, 130, 30)
        pygame.display.set_caption('Pyc Man | Python Arcade')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 21)
        self.title = pygame.font.Font(None, 44)
        self.sprites = {}
        for name in ('player', 'ghost', 'ghost_blue', 'ghost_white'):
            sprite = pygame.image.load(str(PROJECT_ROOT / 'assets/sprites' / f'{name}.png')).convert_alpha()
            self.sprites[name] = pygame.transform.scale(sprite, (TILE, TILE))
        player = self.sprites['player']
        self.players = {
            (1, 0): player,
            (-1, 0): pygame.transform.flip(player, True, False),
            (0, -1): pygame.transform.rotate(player, 90),
            (0, 1): pygame.transform.rotate(player, -90),
        }
        pygame.display.set_icon(player)
        self.running = True

    def reset(self) -> None:
        self.game = (self.game_factory() if self.game_factory is not None else
                     Game(self.path, self.player_controller_factory,
                          self.ghost_controller_factory,
                          config=self.config, rules=self.rules))
        self.player_controller = self.game.controllers[self.game.player]
        self.facing = (1, 0)
        self.started = not isinstance(self.player_controller, KeyboardController)
        self.paused = False
        self.elapsed = 0

    def restart(self) -> None:
        self.reset()
        self.started = True
        self.player_controller.handle_key('right')

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.restart_button.collidepoint(event.pos):
                self.restart()
        elif event.type == pygame.WINDOWFOCUSLOST:
            if self.started:
                self.paused = True
                self.elapsed = 0
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_r or getattr(event, 'scancode', None) == pygame.KSCAN_R:
                self.restart()
            elif event.key in (pygame.K_SPACE, pygame.K_p):
                if self.started and self.game.status == 'running':
                    self.paused = not self.paused
                    self.elapsed = 0
            elif self.game.status == 'running' and not self.paused:
                if self.player_controller.handle_key(pygame.key.name(event.key)):
                    self.started = True

    def update(self, dt: int) -> None:
        if not self.started or self.paused or self.game.status != 'running':
            return
        self.elapsed += min(dt, self.config.turn_ms)  # Avoid bursts after a window stall.
        if self.elapsed < self.config.turn_ms:
            return
        self.elapsed -= self.config.turn_ms
        player = self.game.player
        old_position = (player.x, player.y)
        self.game.step()
        if old_position != (player.x, player.y):
            self.facing = (player.x - old_position[0], player.y - old_position[1])

    def label(self, text: str, position: tuple[int, int], color=TEXT, font=None) -> None:
        self.screen.blit((font or self.font).render(text, True, color), position)

    def ghost_sprite(self) -> pygame.Surface:
        """Frightened ghosts are blue; white flashes warn that power is ending.

        Use the simulation timer so pause also freezes the warning animation.
        White ghosts remain edible until the timer actually reaches zero.
        """
        turns = self.game.player.state
        if turns <= 0:
            return self.sprites['ghost']
        if turns <= self.config.flash_turns:
            phase = (self.config.flash_turns - turns) // self.config.flash_interval
            if phase % 2:
                return self.sprites['ghost_white']
        return self.sprites['ghost_blue']

    def draw(self) -> None:
        self.screen.fill(BG)
        self.label('PycMan', (MARGIN, 20), YELLOW, self.title)
        self.label('PYTHON ARCADE', (MARGIN, 65), MUTED, self.small)
        remaining = sum(row.count(POINT) + row.count(POWER) for row in self.game.env.env)
        self.label(f'SCORE  {self.game.player.score:04d}', (self.width - 205, 24), YELLOW)
        self.label(f'{remaining:03d} RELICS LEFT', (self.width - 205, 57), MUTED, self.small)
        turns = self.game.player.state
        seconds = turns * self.config.turn_ms / 1000
        self.label(f'ENCHANT  {seconds:.1f}s' if turns else 'ENCHANT  --',
                   (260, 24), YELLOW if turns else MUTED)
        bar = pygame.Rect(260, 58, 160, 8)
        pygame.draw.rect(self.screen, (29, 47, 70), bar, border_radius=4)
        if turns:
            fill = bar.copy()
            fill.width = max(1, round(bar.width * min(turns / self.config.power_turns, 1)))
            pygame.draw.rect(self.screen, YELLOW, fill, border_radius=4)
            if turns <= self.config.flash_turns:
                self.label('ENDING SOON', (260, 74), TEXT, self.small)
        for y, row in enumerate(self.game.env.env):
            for x, tile in enumerate(row):
                rect = pygame.Rect(self.board_x + x * TILE, HEADER + y * TILE, TILE, TILE)
                if tile == WALL:
                    pygame.draw.rect(self.screen, (18, 40, 72), rect.inflate(-2, -2), border_radius=7)
                    pygame.draw.rect(self.screen, (43, 99, 157), rect.inflate(-4, -4), 2, border_radius=6)
                elif tile == POINT:
                    pygame.draw.circle(self.screen, (255, 223, 160), rect.center, 3)
                elif tile == POWER:
                    pygame.draw.circle(self.screen, (78, 62, 32), rect.center, 13)
                    pygame.draw.circle(self.screen, YELLOW, rect.center, 9)
                    pygame.draw.circle(self.screen, TEXT, rect.center, 4)
        for item in self.game.emit('visuals', tiles=[])['tiles']:
            x, y = item['x'], item['y']
            rect = pygame.Rect(self.board_x + x * TILE, HEADER + y * TILE, TILE, TILE)
            kind = item['kind']
            open_now = item.get('open', False)
            named = {'red': (220, 91, 89), 'blue': (98, 153, 234),
                     'green': (88, 187, 121), 'yellow': (250, 200, 85)}
            if kind == 'rune':
                pygame.draw.circle(self.screen, (115, 219, 244), rect.center, 12, 3)
                pygame.draw.line(self.screen, (115, 219, 244),
                                 (rect.centerx - 8, rect.centery),
                                 (rect.centerx + 8, rect.centery), 2)
            elif kind == 'key':
                color = named.get(item.get('color'), (250, 200, 85))
                pygame.draw.circle(self.screen, color,
                                   (rect.centerx - 6, rect.centery), 7, 3)
                pygame.draw.line(self.screen, color,
                                 (rect.centerx, rect.centery),
                                 (rect.centerx + 12, rect.centery), 4)
            elif kind == 'door':
                color = ((63, 157, 109) if open_now else
                         named.get(item.get('color'), (166, 82, 80)))
                pygame.draw.rect(self.screen, color, rect.inflate(-10, -4),
                                 3 if open_now else 0, border_radius=3)
                if not open_now:
                    pygame.draw.circle(self.screen, TEXT,
                                       (rect.centerx + 6, rect.centery), 2)
            elif kind == 'gate':
                color = (63, 157, 109) if open_now else (166, 82, 80)
                pygame.draw.rect(self.screen, color, rect.inflate(-8, -8), 2)
                for offset in (-6, 0, 6):
                    pygame.draw.line(self.screen, color,
                                     (rect.centerx + offset, rect.top + 7),
                                     (rect.centerx + offset, rect.bottom - 7), 2)
        ghost_image = self.ghost_sprite()
        for ghost in self.game.env.ghosts:
            if ghost.live:
                self.screen.blit(ghost_image, (self.board_x + ghost.x * TILE, HEADER + ghost.y * TILE))
        player = self.game.player
        if player.live:
            center = (self.board_x + player.x * TILE + TILE // 2,
                      HEADER + player.y * TILE + TILE // 2)
            sprite = self.players[self.facing]
            self.screen.blit(sprite, sprite.get_rect(center=center))
        self.label('WASD / ARROWS   Move     SPACE   Pause     R   Restart     ESC   Exit',
                   (MARGIN, self.height - 76), MUTED, self.small)
        self.label('BLUE GHOSTS = VULNERABLE / WHITE FLASH = ENDING',
                   (MARGIN, self.height - 35), MUTED, self.small)
        if self.game.status != 'running':
            self.overlay('MAZE CLEARED' if self.game.status == 'won' else 'CAUGHT!',
                         f'Score {player.score}   /   Press R to try again')
        elif self.paused:
            self.overlay('PAUSED', 'Press SPACE to continue')
        elif not self.started:
            self.overlay('READY?', 'Press an arrow key or WASD to start')
        # Draw last: the restart button remains visible on every overlay.
        pygame.draw.rect(self.screen, (40, 65, 96), self.restart_button, border_radius=6)
        self.label('RESTART [R]', (self.restart_button.x + 12, self.restart_button.y + 7), TEXT, self.small)

    def overlay(self, title: str, subtitle: str) -> None:
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((5, 9, 20, 175))
        self.screen.blit(shade, (0, 0))
        panel = pygame.Rect(0, 0, 460, 144)
        panel.center = (self.width // 2, self.height // 2)
        pygame.draw.rect(self.screen, (17, 29, 49), panel, border_radius=16)
        pygame.draw.rect(self.screen, (59, 100, 146), panel, 2, border_radius=16)
        for text, font, color, offset in [(title, self.title, YELLOW, -24),
                                           (subtitle, self.font, TEXT, 27)]:
            surface = font.render(text, True, color)
            self.screen.blit(surface, surface.get_rect(center=(panel.centerx, panel.centery + offset)))

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(60)
                for event in pygame.event.get():
                    self.handle_event(event)
                if not self.running:
                    break
                self.update(dt)
                self.draw()
                pygame.display.flip()
        finally:
            pygame.quit()
