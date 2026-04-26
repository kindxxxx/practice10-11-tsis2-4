"""
Racer - Top-Down Racing Game
Entry point. Uses Scene Dictionary pattern for state management.
Controls: Left/Right arrows (or A/D) to steer, ESC to pause.
"""
import pygame
from settings import *
from scenes import MenuScene, GameScene, GameOverScene, LeaderboardScene, SettingsScene


class Game:
    """Main game controller. Manages scenes and the main loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racer")
        self.clock = pygame.time.Clock()
        self.settings = load_settings()
        self.running = True

        # Scene dictionary
        self.scenes = {
            "menu":        MenuScene(self),
            "game":        GameScene(self),
            "game_over":   GameOverScene(self),
            "leaderboard": LeaderboardScene(self),
            "settings":    SettingsScene(self),
        }
        self.current_scene = "menu"

    def change_scene(self, name, **kwargs):
        """Switch to a new scene, calling its enter() method."""
        self.current_scene = name
        self.scenes[name].enter(**kwargs)

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.scenes[self.current_scene].handle_event(event)

            self.scenes[self.current_scene].update(dt)
            self.scenes[self.current_scene].draw(self.screen)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
