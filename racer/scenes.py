"""
Racer Game - Scene Classes
Menu, Game, GameOver, Leaderboard, Settings screens.
"""
import pygame
import random
import math
import os
from settings import *
from sprites import *

# --- Background Asset ---
GRAPHICS_DIR = os.path.join(os.path.dirname(__file__), "graphics")
ROAD_IMG_PATH = os.path.join(GRAPHICS_DIR, "road.png")
MUSIC_PATH = os.path.join(GRAPHICS_DIR, "Kavinsky_Nightcal_-_Nightcall_(SkySound.cc).mp3")

class Scene:
    def __init__(self, game):
        self.game = game
        self.road_img = None
        try:
            self.road_img = pygame.image.load(ROAD_IMG_PATH).convert()
            # Note: Tiling might be better if the image isn't SCREEN_HEIGHT tall, 
            # but we'll scale it to SCREEN_HEIGHT for simplicity in scrolling.
            self.road_img = pygame.transform.scale(self.road_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            pass

    def enter(self, **kw):
        pass
    def handle_event(self, event):
        pass
    def update(self, dt):
        pass
    def draw(self, surface):
        pass

def draw_road_bg(surface, scroll_offset, road_img=None):
    """Draw scrolling road background using texture."""
    if road_img:
        y1 = int(scroll_offset % SCREEN_HEIGHT)
        surface.blit(road_img, (0, y1))
        surface.blit(road_img, (0, y1 - SCREEN_HEIGHT))
    else:
        # Fallback to procedural if image fails
        surface.fill(GRASS_GREEN)
        pygame.draw.rect(surface, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT, 0, 4, SCREEN_HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT - 4, 0, 4, SCREEN_HEIGHT))


def draw_button(surface, rect, text, font, hovered=False):
    """Draw a styled button."""
    color = (80, 80, 120) if not hovered else (110, 110, 160)
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=12)
    txt = font.render(text, True, WHITE)
    surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))


# ================================================================
#  MAIN MENU
# ================================================================
class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont("Arial", 72, bold=True)
        self.font_btn = pygame.font.SysFont("Arial", 30, bold=True)
        self.buttons = ["PLAY", "LEADERBOARD", "SETTINGS", "QUIT"]
        self.btn_rects = []
        bw, bh = 260, 55
        start_y = 320
        for i in range(len(self.buttons)):
            r = pygame.Rect(0, 0, bw, bh)
            r.centerx = SCREEN_WIDTH // 2
            r.y = start_y + i * 75
            self.btn_rects.append(r)
        self.scroll = 0
        self.hovered = -1

    def enter(self, **kw):
        if self.game.settings.get("sound"):
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.load(MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                except:
                    pass
        else:
            pygame.mixer.music.stop()

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = -1
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    self.hovered = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    if i == 0:
                        self.game.change_scene("game")
                    elif i == 1:
                        self.game.change_scene("leaderboard")
                    elif i == 2:
                        self.game.change_scene("settings")
                    elif i == 3:
                        self.game.running = False

    def update(self, dt):
        self.scroll += 2

    def draw(self, surface):
        draw_road_bg(surface, self.scroll, self.road_img)
        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        surface.blit(ov, (0, 0))
        # Title
        title = self.font_title.render("RACER", True, (255, 220, 60))
        shadow = self.font_title.render("RACER", True, (40, 30, 0))
        surface.blit(shadow, (SCREEN_WIDTH//2 - shadow.get_width()//2 + 3, 103))
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        # Subtitle
        sub_font = pygame.font.SysFont("Arial", 20)
        sub = sub_font.render("Top-Down Racing Game", True, (180, 180, 200))
        surface.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 185))
        # Buttons
        for i, (label, rect) in enumerate(zip(self.buttons, self.btn_rects)):
            draw_button(surface, rect, label, self.font_btn, self.hovered == i)


# ================================================================
#  GAME SCENE
# ================================================================
class GameScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_hud = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 16)
        self.reset()

    def reset(self):
        settings = self.game.settings
        diff = DIFFICULTY[settings.get("difficulty", "medium")]
        self.base_speed = diff["base_speed"]
        self.spawn_interval = diff["spawn_interval"]
        self.coin_interval = diff["coin_interval"]
        self.game_speed = self.base_speed
        self.scroll = 0
        self.frame = 0
        self.coins_collected = 0
        self.speed_level = 0

        color = settings.get("car_color", "red")
        model = settings.get("car_model", "Sedan")
        self.player = Player(color, model)
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.paused = False
        self.obstacle_effect_timer = 0
        self.obstacle_effect_type = None

    def enter(self, **kw):
        self.reset()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                self.paused = not self.paused

    def spawn_enemy(self):
        r = random.random()
        if r < 0.55:
            t = "sedan"
        elif r < 0.80:
            t = "truck"
        else:
            t = "sports"
        lane = random.randint(0, NUM_LANES - 1)
        # Check lane not too crowded
        for e in self.enemies:
            if e.lane == lane and e.rect.top < 120:
                return
        self.enemies.add(EnemyCar(t, lane, self.game_speed))

    def spawn_coin(self):
        r = random.random()
        if r < 0.50:
            t = "bronze"
        elif r < 0.85:
            t = "silver"
        else:
            t = "gold"
        lane = random.randint(0, NUM_LANES - 1)
        self.coins.add(Coin(t, lane))

    def spawn_powerup(self):
        t = random.choice(["nitro", "shield", "repair"])
        lane = random.randint(0, NUM_LANES - 1)
        self.powerups.add(PowerUp(t, lane))

    def spawn_obstacle(self):
        t = random.choice(["oil", "pothole"])
        lane = random.randint(0, NUM_LANES - 1)
        self.obstacles.add(Obstacle(t, lane))

    def get_collision_type(self, enemy_rect):
        dx = abs(self.player.rect.centerx - enemy_rect.centerx)
        if dx < self.player.rect.width * 0.4:
            return "head_on"
        return "side"

    def update(self, dt):
        if self.paused:
            return
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        self.frame += 1

        # Nitro speed boost
        effective_speed = self.game_speed
        if self.player.has_nitro:
            effective_speed *= NITRO_MULTIPLIER

        # Obstacle effect
        if self.obstacle_effect_timer > 0:
            self.obstacle_effect_timer -= dt
            if self.obstacle_effect_type == "oil":
                # Slide player randomly
                self.player.rect.x += random.randint(-3, 3)
                self.player.rect.left = max(ROAD_LEFT + 5, self.player.rect.left)
                self.player.rect.right = min(ROAD_RIGHT - 5, self.player.rect.right)

        self.scroll += effective_speed

        # Spawn enemies
        interval = max(25, self.spawn_interval - self.speed_level * 4)
        if self.frame % interval == 0:
            self.spawn_enemy()
        # Spawn coins
        if self.frame % self.coin_interval == 0:
            self.spawn_coin()
        # Spawn power-ups (rarer)
        if self.frame % 350 == 0:
            self.spawn_powerup()
        # Spawn obstacles
        if self.frame % 280 == 0:
            self.spawn_obstacle()

        # Update sprites
        for e in self.enemies:
            e.update(effective_speed)
        for c in self.coins:
            c.update(effective_speed)
        for p in self.powerups:
            p.update(effective_speed)
        for o in self.obstacles:
            o.update(effective_speed)

        # --- Collisions ---
        # Player vs Enemies
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False,
                                           pygame.sprite.collide_rect_ratio(0.8))
        for enemy in hits:
            ctype = self.get_collision_type(enemy.rect)
            is_truck = self.player.model_name == "Truck"
            dmg_table = DAMAGE["truck"] if is_truck else DAMAGE["car"]
            dmg = dmg_table[ctype]
            self.player.take_damage(dmg)
            enemy.kill()
            if self.player.hp <= 0:
                self.game.change_scene("game_over", score=self.player.score)
                return

        # Player vs Coins
        coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True,
                                                pygame.sprite.collide_rect_ratio(0.7))
        for c in coin_hits:
            self.player.score += c.value
            self.coins_collected += c.value
            # Difficulty scaling: every 10 coins
            new_level = self.coins_collected // 10
            if new_level > self.speed_level:
                self.speed_level = new_level
                self.game_speed = self.base_speed + self.speed_level * 0.3

        # Player vs Power-ups
        pu_hits = pygame.sprite.spritecollide(self.player, self.powerups, True,
                                              pygame.sprite.collide_rect_ratio(0.7))
        for pu in pu_hits:
            if pu.pu_type == "nitro":
                self.player.activate_nitro()
            elif pu.pu_type == "shield":
                self.player.activate_shield()
            elif pu.pu_type == "repair":
                self.player.repair()

        # Player vs Obstacles
        obs_hits = pygame.sprite.spritecollide(self.player, self.obstacles, False,
                                               pygame.sprite.collide_rect_ratio(0.6))
        for obs in obs_hits:
            if obs.active:
                obs.active = False
                if obs.obs_type == "oil":
                    self.obstacle_effect_timer = 1.5
                    self.obstacle_effect_type = "oil"
                elif obs.obs_type == "pothole":
                    self.obstacle_effect_timer = 1.0
                    self.obstacle_effect_type = "pothole"

    def draw(self, surface):
        draw_road_bg(surface, self.scroll, self.road_img)

        # Draw obstacles (under everything)
        self.obstacles.draw(surface)
        # Draw coins
        self.coins.draw(surface)
        # Draw power-ups
        self.powerups.draw(surface)
        # Draw enemies
        self.enemies.draw(surface)
        # Draw player extras (shield glow, nitro flames)
        self.player.draw_extras(surface)
        # Draw player
        surface.blit(self.player.image, self.player.rect)

        # --- HUD ---
        self._draw_hud(surface)

        # Pause overlay
        if self.paused:
            ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            surface.blit(ov, (0, 0))
            pfont = pygame.font.SysFont("Arial", 56, bold=True)
            ptxt = pfont.render("PAUSED", True, WHITE)
            surface.blit(ptxt, (SCREEN_WIDTH//2 - ptxt.get_width()//2, SCREEN_HEIGHT//2 - 30))
            hint = self.font_hud.render("Press ESC to resume", True, (180, 180, 200))
            surface.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 40))

    def _draw_hud(self, surface):
        # Background bar
        hud = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
        hud.fill((10, 10, 20, 200))
        surface.blit(hud, (0, 0))

        # Score
        stxt = self.font_hud.render(f"Coins: {self.player.score}", True, GOLD_COLOR)
        surface.blit(stxt, (15, 14))

        # HP bar
        bar_x, bar_y, bar_w, bar_h = 420, 12, 150, 24
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        hp_ratio = max(0, self.player.hp / MAX_HP)
        fill_color = HP_GREEN if hp_ratio > 0.4 else ORANGE if hp_ratio > 0.2 else HP_RED
        pygame.draw.rect(surface, fill_color,
                         (bar_x + 2, bar_y + 2, int((bar_w - 4) * hp_ratio), bar_h - 4),
                         border_radius=4)
        hp_txt = self.font_hud.render(f"HP {self.player.hp}", True, WHITE)
        surface.blit(hp_txt, (bar_x + bar_w//2 - hp_txt.get_width()//2, bar_y + 2))

        # Speed indicator
        spd = self.font_big.render(f"Speed: {self.game_speed:.1f}", True, (180, 180, 200))
        surface.blit(spd, (220, 16))

        # Power-up indicators (below HUD bar)
        y_pu = 56
        if self.player.has_nitro:
            nt = self.font_big.render(f"NITRO {self.player.nitro_timer:.1f}s", True, NITRO_CYAN)
            surface.blit(nt, (15, y_pu))
            pygame.draw.rect(surface, DARK_GRAY, (15, y_pu + 20, 100, 8))
            pygame.draw.rect(surface, NITRO_CYAN, (15, y_pu + 20, 100 * (self.player.nitro_timer / NITRO_DURATION), 8))
        if self.player.has_shield:
            st = self.font_big.render(f"SHIELD {self.player.shield_timer:.1f}s", True, SHIELD_BLUE)
            surface.blit(st, (150, y_pu))
            pygame.draw.rect(surface, DARK_GRAY, (150, y_pu + 20, 100, 8))
            pygame.draw.rect(surface, SHIELD_BLUE, (150, y_pu + 20, 100 * (self.player.shield_timer / SHIELD_DURATION), 8))
        if self.obstacle_effect_timer > 0:
            eff = "OIL SLICK!" if self.obstacle_effect_type == "oil" else "POTHOLE!"
            et = self.font_big.render(eff, True, ORANGE)
            surface.blit(et, (300, y_pu))


# ================================================================
#  GAME OVER
# ================================================================
class GameOverScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_score = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_input = pygame.font.SysFont("Arial", 28)
        self.font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        self.score = 0
        self.name = ""
        self.submitted = False
        self.btn_retry = pygame.Rect(0, 0, 180, 50)
        self.btn_retry.center = (SCREEN_WIDTH//2 - 110, 620)
        self.btn_menu = pygame.Rect(0, 0, 180, 50)
        self.btn_menu.center = (SCREEN_WIDTH//2 + 110, 620)
        self.hovered = -1

    def enter(self, **kw):
        self.score = kw.get("score", 0)
        self.name = ""
        self.submitted = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = -1
            if self.btn_retry.collidepoint(event.pos):
                self.hovered = 0
            elif self.btn_menu.collidepoint(event.pos):
                self.hovered = 1
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_retry.collidepoint(event.pos):
                self.game.change_scene("game")
            elif self.btn_menu.collidepoint(event.pos):
                self.game.change_scene("menu")
        if event.type == pygame.KEYDOWN and not self.submitted:
            if event.key == pygame.K_RETURN and len(self.name) > 0:
                save_leaderboard(self.score, self.name)
                self.submitted = True
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif len(self.name) < 12 and event.unicode.isprintable() and event.unicode != '':
                self.name += event.unicode

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((20, 15, 30))
        # Title
        title = self.font_title.render("GAME OVER", True, RED)
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        # Score
        stxt = self.font_score.render(f"Score: {self.score}", True, GOLD_COLOR)
        surface.blit(stxt, (SCREEN_WIDTH//2 - stxt.get_width()//2, 220))

        if not self.submitted:
            # Name input
            prompt = self.font_input.render("Enter your name:", True, WHITE)
            surface.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 320))
            # Input box
            box = pygame.Rect(0, 0, 300, 45)
            box.centerx = SCREEN_WIDTH // 2
            box.y = 370
            pygame.draw.rect(surface, (50, 50, 70), box, border_radius=8)
            pygame.draw.rect(surface, WHITE, box, 2, border_radius=8)
            ntxt = self.font_input.render(self.name + ("_" if pygame.time.get_ticks() % 1000 < 500 else ""), True, WHITE)
            surface.blit(ntxt, (box.x + 12, box.y + 8))
            hint = pygame.font.SysFont("Arial", 18).render("Press ENTER to submit", True, (140, 140, 160))
            surface.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 425))
        else:
            saved = self.font_input.render("Score saved!", True, GREEN)
            surface.blit(saved, (SCREEN_WIDTH//2 - saved.get_width()//2, 360))

        # Buttons
        draw_button(surface, self.btn_retry, "RETRY", self.font_btn, self.hovered == 0)
        draw_button(surface, self.btn_menu, "MENU", self.font_btn, self.hovered == 1)


# ================================================================
#  LEADERBOARD
# ================================================================
class LeaderboardScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_entry = pygame.font.SysFont("Arial", 24)
        self.font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        self.btn_back = pygame.Rect(0, 0, 180, 50)
        self.btn_back.center = (SCREEN_WIDTH // 2, 720)
        self.hovered = False

    def enter(self, **kw):
        self.data = load_leaderboard()

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.btn_back.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.collidepoint(event.pos):
                self.game.change_scene("menu")

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((20, 15, 30))
        title = self.font_title.render("LEADERBOARD", True, GOLD_COLOR)
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))

        # Headers
        y = 120
        hdr = self.font_entry.render(f"{'#':<5}{'Name':<15}{'Score':>8}", True, (180, 180, 200))
        surface.blit(hdr, (120, y))
        pygame.draw.line(surface, (100, 100, 120), (120, y + 30), (480, y + 30), 1)

        for i, entry in enumerate(self.data[:10]):
            y = 160 + i * 42
            color = GOLD_COLOR if i == 0 else SILVER_COLOR if i == 1 else BRONZE_COLOR if i == 2 else WHITE
            row_bg = pygame.Surface((360, 36), pygame.SRCALPHA)
            row_bg.fill((40, 40, 60, 80) if i % 2 == 0 else (30, 30, 50, 60))
            surface.blit(row_bg, (120, y))
            txt = self.font_entry.render(
                f"{i+1:<5}{entry['name']:<15}{entry['score']:>8}", True, color
            )
            surface.blit(txt, (130, y + 6))

        if not self.data:
            empty = self.font_entry.render("No scores yet!", True, (140, 140, 160))
            surface.blit(empty, (SCREEN_WIDTH//2 - empty.get_width()//2, 300))

        draw_button(surface, self.btn_back, "BACK", self.font_btn, self.hovered)


# ================================================================
#  SETTINGS
# ================================================================
class SettingsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_val = pygame.font.SysFont("Arial", 22)
        self.font_btn = pygame.font.SysFont("Arial", 26, bold=True)

        self.btn_back = pygame.Rect(0, 0, 180, 50)
        self.btn_back.center = (SCREEN_WIDTH // 2, 720)

        self.model_names = ["Sedan", "Sport", "Truck", "Compact", "Coupe"]
        self.color_names = list(CAR_COLORS.keys())
        self.diff_names = ["easy", "medium", "hard"]
        self.hovered_item = None

    def enter(self, **kw):
        self.settings = self.game.settings.copy()

    def _get_rects(self):
        """Return clickable areas."""
        rects = {}
        # Sound toggle
        rects["sound"] = pygame.Rect(350, 120, 120, 40)
        # Car models
        for i, m in enumerate(self.model_names):
            rects[f"model_{m}"] = pygame.Rect(140 + i * 85, 200, 80, 40)
        # Car colors
        for i, cn in enumerate(self.color_names):
            rects[f"color_{cn}"] = pygame.Rect(140 + i * 52, 280, 44, 44)
        # Difficulty
        for i, d in enumerate(self.diff_names):
            rects[f"diff_{d}"] = pygame.Rect(140 + i * 140, 380, 120, 40)
        rects["back"] = self.btn_back
        return rects

    def handle_event(self, event):
        rects = self._get_rects()
        if event.type == pygame.MOUSEMOTION:
            self.hovered_item = None
            for key, r in rects.items():
                if r.collidepoint(event.pos):
                    self.hovered_item = key
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if rects["sound"].collidepoint(pos):
                self.settings["sound"] = not self.settings["sound"]
            for m in self.model_names:
                if rects[f"model_{m}"].collidepoint(pos):
                    self.settings["car_model"] = m
            for cn in self.color_names:
                if rects[f"color_{cn}"].collidepoint(pos):
                    self.settings["car_color"] = cn
            for d in self.diff_names:
                if rects[f"diff_{d}"].collidepoint(pos):
                    self.settings["difficulty"] = d
            if rects["back"].collidepoint(pos):
                self.game.settings = self.settings
                save_settings(self.settings)
                self.game.change_scene("menu")

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((20, 15, 30))
        rects = self._get_rects()

        title = self.font_title.render("SETTINGS", True, (180, 200, 255))
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))

        # --- Sound ---
        lbl = self.font_label.render("Sound:", True, WHITE)
        surface.blit(lbl, (140, 125))
        r = rects["sound"]
        val = "ON" if self.settings["sound"] else "OFF"
        col = GREEN if self.settings["sound"] else RED
        pygame.draw.rect(surface, (50, 50, 70), r, border_radius=8)
        pygame.draw.rect(surface, col, r, 2, border_radius=8)
        vtxt = self.font_val.render(val, True, col)
        surface.blit(vtxt, (r.centerx - vtxt.get_width()//2, r.centery - vtxt.get_height()//2))

        # --- Car Model ---
        lbl_model = self.font_label.render("Model:", True, WHITE)
        surface.blit(lbl_model, (140, 175))
        for m in self.model_names:
            r = rects[f"model_{m}"]
            active = self.settings["car_model"] == m
            bg = (80, 80, 120) if active else (40, 40, 60)
            pygame.draw.rect(surface, bg, r, border_radius=8)
            border = WHITE if active else (80, 80, 100)
            pygame.draw.rect(surface, border, r, 2, border_radius=8)
            mtxt = self.font_val.render(m, True, WHITE if active else (140, 140, 160))
            surface.blit(mtxt, (r.centerx - mtxt.get_width()//2, r.centery - mtxt.get_height()//2))

        # --- Car Color ---
        lbl2 = self.font_label.render("Color:", True, WHITE)
        surface.blit(lbl2, (140, 255))
        for cn in self.color_names:
            r = rects[f"color_{cn}"]
            pygame.draw.rect(surface, CAR_COLORS[cn], r, border_radius=8)
            if self.settings["car_color"] == cn:
                pygame.draw.rect(surface, WHITE, r.inflate(6, 6), 3, border_radius=10)

        # --- Difficulty ---
        lbl3 = self.font_label.render("Difficulty:", True, WHITE)
        surface.blit(lbl3, (140, 345))
        for d in self.diff_names:
            r = rects[f"diff_{d}"]
            active = self.settings["difficulty"] == d
            bg = (80, 80, 120) if active else (40, 40, 60)
            pygame.draw.rect(surface, bg, r, border_radius=8)
            border = WHITE if active else (80, 80, 100)
            pygame.draw.rect(surface, border, r, 2, border_radius=8)
            dtxt = self.font_val.render(d.upper(), True, WHITE if active else (140, 140, 160))
            surface.blit(dtxt, (r.centerx - dtxt.get_width()//2, r.centery - dtxt.get_height()//2))

        # Preview car
        preview_model = self.settings["car_model"]
        preview_path = os.path.join(GRAPHICS_DIR, preview_model, f"{preview_model.lower()}_{self.settings['car_color']}.png")
        if not os.path.exists(preview_path):
            preview_path = os.path.join(GRAPHICS_DIR, "Sedan", "sedan_red.png")
        
        # scale based on model
        if preview_model == "Truck":
            pw, ph = 55, 110
        elif preview_model == "Sport":
            pw, ph = 44, 80
        elif preview_model in ["Compact", "Coupe"]:
            pw, ph = 46, 84
        else: # Sedan
            pw, ph = 48, 88
            
        car_surf = load_image(preview_path, (pw * 1.5, ph * 1.5))
        surface.blit(car_surf, (SCREEN_WIDTH//2 - car_surf.get_width()//2, 450))
        prev_lbl = self.font_val.render("Preview", True, (140, 140, 160))
        surface.blit(prev_lbl, (SCREEN_WIDTH//2 - prev_lbl.get_width()//2, 630))

        draw_button(surface, self.btn_back, "SAVE & BACK", self.font_btn,
                    self.hovered_item == "back")
