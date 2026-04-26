"""
Racer Game - Sprite Classes
All game objects: Player, Enemy Cars, Coins, Power-Ups, Obstacles.
Uses image assets from the graphics folder.
"""
import pygame
import random
import math
import os
from settings import *

# --- Asset Loading Helpers ---
def load_image(path, scale=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        # Return a placeholder surface if image fails to load
        surf = pygame.Surface(scale if scale else (50, 50))
        surf.fill((255, 0, 255)) # Magenta placeholder
        return surf

GRAPHICS_DIR = os.path.join(os.path.dirname(__file__), "graphics")

# ================================================================
#  Player Car
# ================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, color_name="red", model_name="Sedan"):
        super().__init__()
        self.color_name = color_name
        self.model_name = model_name
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        self.load_car_image()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30

        # State
        self.hp = MAX_HP
        self.score = 0
        self.speed = PLAYER_SPEED

        # Power-ups
        self.nitro_timer = 0.0
        self.shield_timer = 0.0
        self.has_nitro = False
        self.has_shield = False

        # Visual feedback
        self.flash_timer = 0.0
        self.flash_color = None  # "red" or "green"
        self.invuln_timer = 0.0  # brief invulnerability after hit

    def load_car_image(self):
        # Update width/height depending on model
        if self.model_name == "Truck":
            self.width, self.height = 55, 110
        elif self.model_name == "Sport":
            self.width, self.height = 44, 80
        elif self.model_name in ["Compact", "Coupe"]:
            self.width, self.height = 46, 84
        else: # Sedan
            self.width, self.height = 48, 88

        path = os.path.join(GRAPHICS_DIR, self.model_name, f"{self.model_name.lower()}_{self.color_name}.png")
        if not os.path.exists(path):
            # Fallback
            path = os.path.join(GRAPHICS_DIR, "Sedan", "sedan_red.png")
            self.width, self.height = 48, 88
        
        self.original_image = load_image(path, (self.width, self.height))
        self.image = self.original_image.copy()
        
        # Keep rect centered where it was if already initialized
        if hasattr(self, 'rect') and self.rect is not None:
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def set_model_color(self, model_name, color_name):
        self.model_name = model_name
        self.color_name = color_name
        self.load_car_image()

    def take_damage(self, amount):
        if self.has_shield or self.invuln_timer > 0:
            return
        self.hp = max(0, self.hp - amount)
        self.flash_timer = 0.4
        self.flash_color = "red"
        self.invuln_timer = 0.8  # brief invulnerability

    def repair(self, amount=REPAIR_AMOUNT):
        self.hp = min(MAX_HP, self.hp + amount)
        self.flash_timer = 0.4
        self.flash_color = "green"

    def activate_nitro(self):
        self.nitro_timer = NITRO_DURATION
        self.has_nitro = True

    def activate_shield(self):
        self.shield_timer = SHIELD_DURATION
        self.has_shield = True

    def update(self, dt, keys):
        # Movement
        speed = self.speed
        if self.has_nitro:
            speed *= NITRO_MULTIPLIER

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += speed

        # Clamp to road
        self.rect.left = max(ROAD_LEFT + 5, self.rect.left)
        self.rect.right = min(ROAD_RIGHT - 5, self.rect.right)

        # Power-up timers
        if self.has_nitro:
            self.nitro_timer -= dt
            if self.nitro_timer <= 0:
                self.has_nitro = False
                self.nitro_timer = 0

        if self.has_shield:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.has_shield = False
                self.shield_timer = 0

        # Invulnerability timer
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        # Flash timer
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Update image
        self._update_image()

    def _update_image(self):
        self.image = self.original_image.copy()

        # Flash overlay
        if self.flash_timer > 0 and self.flash_color:
            overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            alpha = int(180 * (self.flash_timer / 0.4))
            if self.flash_color == "red":
                overlay.fill((255, 0, 0, alpha))
            else:
                overlay.fill((0, 255, 0, alpha))
            self.image.blit(overlay, (0, 0))

        # Invulnerability blink
        if self.invuln_timer > 0:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def draw_extras(self, surface):
        if self.has_shield:
            pulse = int(60 + 40 * math.sin(pygame.time.get_ticks() / 200))
            glow_rect = self.rect.inflate(16, 16)
            glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*SHIELD_BLUE, pulse), glow.get_rect(), 3)
            surface.blit(glow, glow_rect.topleft)

        if self.has_nitro:
            # Flame behind car
            cx = self.rect.centerx
            by = self.rect.bottom
            flicker = random.randint(-3, 3)
            for i in range(3):
                r = 8 - i * 2
                y_off = i * 8
                alpha = 200 - i * 50
                color = (255, 100 + i * 40, 0, alpha)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (r, r), r)
                surface.blit(s, (cx - r + flicker, by + y_off))


# ================================================================
#  Enemy Car
# ================================================================
class EnemyCar(pygame.sprite.Sprite):
    def __init__(self, car_type, lane, base_speed):
        super().__init__()
        self.car_type = car_type
        self.lane = lane
        
        # Determine width/height based on type
        if car_type == "truck":
            w, h = 55, 110
            subdir = "Truck"
            prefix = "truck"
            colors = ["blue", "cream", "green", "red"]
        elif car_type == "sports":
            w, h = 44, 80
            subdir = "Sport"
            prefix = "sport"
            colors = ["blue", "green", "red", "yellow"]
        else: # sedan
            w, h = 48, 88
            subdir = "Sedan"
            prefix = "sedan"
            colors = ["blue", "gray", "green", "red"]

        color = random.choice(colors)
        path = os.path.join(GRAPHICS_DIR, subdir, f"{prefix}_{color}.png")
        
        # Load and rotate to face DOWN
        img = load_image(path, (w, h))
        self.image = pygame.transform.flip(img, False, True)
        self.rect = self.image.get_rect()
        self.rect.centerx = LANE_CENTERS[lane]
        self.rect.bottom = -10

        self.speed = base_speed * (1.3 if car_type == "sports" else 0.75 if car_type == "truck" else 1.0)

    def update(self, game_speed):
        self.rect.y += self.speed + game_speed * 0.5
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# ================================================================
#  Coin
# ================================================================
class Coin(pygame.sprite.Sprite):
    def __init__(self, coin_type, lane):
        super().__init__()
        info = COIN_TYPES[coin_type]
        self.coin_type = coin_type
        self.value = info["value"]
        r = info["radius"]

        self.image = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(self.image, info["color"], (r + 2, r + 2), r)
        pygame.draw.circle(self.image, (255, 255, 255, 150), (r, r), r // 2)
        font = pygame.font.SysFont("Arial", r, bold=True)
        txt = font.render("$", True, (40, 40, 40))
        self.image.blit(txt, (r + 2 - txt.get_width() // 2, r + 2 - txt.get_height() // 2))

        self.rect = self.image.get_rect()
        self.rect.centerx = LANE_CENTERS[lane]
        self.rect.bottom = -5

    def update(self, game_speed):
        self.rect.y += game_speed
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# ================================================================
#  Power-Up
# ================================================================
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pu_type, lane):
        super().__init__()
        self.pu_type = pu_type
        
        path = os.path.join(GRAPHICS_DIR, f"{pu_type}.png")
        self.image = load_image(path, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.centerx = LANE_CENTERS[lane]
        self.rect.bottom = -5

    def update(self, game_speed):
        self.rect.y += game_speed
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# ================================================================
#  Obstacle
# ================================================================
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, obs_type, lane):
        super().__init__()
        self.obs_type = obs_type
        if obs_type == "oil":
            w, h = 60, 30
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (*OIL_COLOR, 180), (0, 0, w, h))
        else: # pothole
            w, h = 36, 36
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(self.image, POTHOLE_COLOR, (w // 2, h // 2), w // 2)
            pygame.draw.circle(self.image, (30, 20, 10), (w // 2, h // 2), w // 3)

        self.rect = self.image.get_rect()
        self.rect.centerx = LANE_CENTERS[lane]
        self.rect.bottom = -5
        self.active = True

    def update(self, game_speed):
        self.rect.y += game_speed
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()
