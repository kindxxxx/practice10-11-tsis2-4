import pygame
import sys
import os
import random
import json
from pygame.math import Vector2
import db

pygame.init()

CELL_SIZE = 40
CELL_NUMBER = 20
SIDEBAR_WIDTH = 250
GAME_WIDTH = CELL_SIZE * CELL_NUMBER
SCREEN_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = CELL_SIZE * CELL_NUMBER

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game Pro")
clock = pygame.time.Clock()

SCREEN_UPDATE = pygame.USEREVENT
pygame.time.set_timer(SCREEN_UPDATE, 150)

# Settings
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"snake_color": [0, 255, 0], "grid_visible": True, "sound_on": True, "volume": 0.5}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except:
        pass

settings = load_settings()

GRAPHICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Graphics")

def load_image(name, colorkey=None):
    path = os.path.join(GRAPHICS_DIR, name)
    if os.path.exists(path):
        surf = pygame.image.load(path).convert_alpha()
        if colorkey:
            surf.set_colorkey(colorkey)
        return surf
    else:
        # Fallback surface if image not found
        surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        surf.fill((255, 0, 255))
        return surf

# Load all graphics
apple_img = load_image('apple.png')
poison_apple_img = load_image('POISON_apple.png')
head_up = load_image('head_up.png')
head_down = load_image('head_down.png')
head_right = load_image('head_right.png')
head_left = load_image('head_left.png')
tail_up = load_image('tail_up.png')
tail_down = load_image('tail_down.png')
tail_right = load_image('tail_right.png')
tail_left = load_image('tail_left.png')
body_v = load_image('body_vertical.png')
body_h = load_image('body_horizontal.png')
body_tr = load_image('body_topright.png')
body_tl = load_image('body_topleft.png')
body_br = load_image('body_bottomright.png')
body_bl = load_image('body_bottomleft.png')

# Load effect icons with white transparency
speed_icon = pygame.transform.scale(load_image('speed_icon.png', (255, 255, 255)), (40, 40))
score_icon = pygame.transform.scale(load_image('score_icon.png', (255, 255, 255)), (40, 40))
ghost_icon = pygame.transform.scale(load_image('ghost_icon.png', (255, 255, 255)), (40, 40))

font_main = pygame.font.SysFont("Segoe UI", 36, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 24)

# Colors
COLOR_BG = (175, 215, 70)
COLOR_TEXT = (50, 50, 50)
COLOR_BUTTON = (50, 150, 250)
COLOR_BUTTON_HOVER = (100, 200, 255)

# --- CLASS: SNAKE ---
# Handles the logic, movement, and rendering of the snake
class SNAKE:
    def __init__(self):
        # Initial snake body with 3 blocks
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(1, 0)
        self.new_block = False

    def draw_snake(self, screen, snake_color_setting):
        # Update graphics for head and tail before drawing
        self.update_head_graphics()
        self.update_tail_graphics()
        
        for index, block in enumerate(self.body):
            x_pos = int(block.x * CELL_SIZE)
            y_pos = int(block.y * CELL_SIZE)
            block_rect = pygame.Rect(x_pos, y_pos, CELL_SIZE, CELL_SIZE)
            
            if index == 0:
                screen.blit(self.head, block_rect)
            elif index == len(self.body) - 1:
                screen.blit(self.tail, block_rect)
            else:
                previous_block = self.body[index + 1] - block
                next_block = self.body[index - 1] - block
                if previous_block.x == next_block.x:
                    screen.blit(body_v, block_rect)
                elif previous_block.y == next_block.y:
                    screen.blit(body_h, block_rect)
                else:
                    if previous_block.x == -1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == -1:
                        screen.blit(body_tl, block_rect)
                    elif previous_block.x == -1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == -1:
                        screen.blit(body_bl, block_rect)
                    elif previous_block.x == 1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == 1:
                        screen.blit(body_tr, block_rect)
                    elif previous_block.x == 1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == 1:
                        screen.blit(body_br, block_rect)

    def update_head_graphics(self):
        head_relation = self.body[1] - self.body[0]
        if head_relation == Vector2(1, 0): self.head = head_left
        elif head_relation == Vector2(-1, 0): self.head = head_right
        elif head_relation == Vector2(0, 1): self.head = head_up
        elif head_relation == Vector2(0, -1): self.head = head_down

    def update_tail_graphics(self):
        tail_relation = self.body[-2] - self.body[-1]
        if tail_relation == Vector2(1, 0): self.tail = tail_left
        elif tail_relation == Vector2(-1, 0): self.tail = tail_right
        elif tail_relation == Vector2(0, 1): self.tail = tail_up
        elif tail_relation == Vector2(0, -1): self.tail = tail_down

    def move_snake(self):
        if self.new_block:
            body_copy = self.body[:]
            self.new_block = False
        else:
            body_copy = self.body[:-1]
        
        body_copy.insert(0, body_copy[0] + self.direction)
        self.body = body_copy[:]

    def add_block(self):
        self.new_block = True
        
    def shrink(self):
        if len(self.body) > 1:
            self.body.pop()

# --- CLASS: FOOD ---
# Handles normal food and poison food spawning and rendering
class FOOD:
    def __init__(self, is_poison=False):
        self.is_poison = is_poison
        self.pos = Vector2(0, 0)
        
    def randomize(self, snake_body, obstacles, powerups, other_foods):
        # Keep generating coordinates until an empty spot is found
        while True:
            self.x = random.randint(0, CELL_NUMBER - 1)
            self.y = random.randint(0, CELL_NUMBER - 1)
            self.pos = Vector2(self.x, self.y)
            
            overlap = False
            if self.pos in snake_body or self.pos in obstacles: overlap = True
            for p in powerups:
                if p.pos == self.pos: overlap = True
            for f in other_foods:
                if f.pos == self.pos: overlap = True
            if not overlap:
                break

    def draw_food(self, screen):
        x_pos = int(self.pos.x * CELL_SIZE)
        y_pos = int(self.pos.y * CELL_SIZE)
        food_rect = pygame.Rect(x_pos, y_pos, CELL_SIZE, CELL_SIZE)
        if self.is_poison:
            screen.blit(poison_apple_img, food_rect)
        else:
            screen.blit(apple_img, food_rect)

# --- CLASS: POWERUP ---
# Handles 3 types of power-ups with timed effects
class POWERUP:
    def __init__(self, type_id):
        self.type_id = type_id # 0: Speed Boost, 1: Score Multiplier (2x), 2: Ghost Mode (No Wall Collision)
        self.pos = Vector2(0,0)
        self.spawn_time = pygame.time.get_ticks()
        
    def randomize(self, snake_body, obstacles, foods):
        # Keep generating coordinates until an empty spot is found
        while True:
            self.x = random.randint(0, CELL_NUMBER - 1)
            self.y = random.randint(0, CELL_NUMBER - 1)
            self.pos = Vector2(self.x, self.y)
            overlap = False
            if self.pos in snake_body or self.pos in obstacles: overlap = True
            for f in foods:
                if f.pos == self.pos: overlap = True
            if not overlap: break
            
    def draw(self, screen):
        x = int(self.pos.x * CELL_SIZE)
        y = int(self.pos.y * CELL_SIZE)
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        if self.type_id == 0:
            pygame.draw.ellipse(screen, (0, 0, 255), rect)
            txt = font_small.render("S", True, (255,255,255))
        elif self.type_id == 1:
            pygame.draw.ellipse(screen, (255, 215, 0), rect)
            txt = font_small.render("2x", True, (0,0,0))
        elif self.type_id == 2:
            pygame.draw.ellipse(screen, (200, 200, 200), rect)
            txt = font_small.render("G", True, (0,0,0))
        screen.blit(txt, (x + CELL_SIZE//2 - txt.get_width()//2, y + CELL_SIZE//2 - txt.get_height()//2))

# --- CLASS: MAIN ---
# The core game manager handling UI states, game loop, inputs, and collisions
class MAIN:
    def __init__(self):
        self.username = ""
        self.state = "MENU" # Screens: MENU, GAME, GAME_OVER, LEADERBOARD, SETTINGS
        self.personal_best = 0
        self.volume = settings.get("volume", 0.5)
        
        # Load music
        try:
            pygame.mixer.music.load(os.path.join(GRAPHICS_DIR, 'Travis Scott feat. Drake - Sicko Mode.mp3'))
            pygame.mixer.music.set_volume(self.volume)
            if settings.get("sound_on", True):
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading music: {e}")
            
        self.reset_game()

    def reset_game(self):
        # Reset all game variables for a new session
        self.snake = SNAKE()
        self.foods = [FOOD(is_poison=False)]
        self.obstacles = []
        self.powerups = []
        self.score = 0
        self.level = 1
        self.foods_eaten_level = 0
        self.ghost_mode = False
        self.multiplier = 1
        self.active_powerup_type = -1
        self.powerup_end_time = 0
        self.game_over_flag = False
        self.direction_changed = False
        
        self.update_speed()
        self.spawn_initial_entities()

    def spawn_initial_entities(self):
        self.foods[0].randomize(self.snake.body, self.obstacles, self.powerups, [])

    def update_speed(self):
        # Decrease timer interval (increase speed) based on the current level
        self.tick_delay = max(50, 150 - (self.level - 1) * 15)
        if self.active_powerup_type == 0: # Speed powerup makes it 1.35x faster
            self.tick_delay = int(self.tick_delay / 1.35)
        pygame.time.set_timer(SCREEN_UPDATE, self.tick_delay)

    def generate_obstacles(self):
        # Obstacles appear from Level 3 onwards
        if self.level >= 3:
            num_obs = min(10, self.level) # Up to 10 obstacles randomly placed
            self.obstacles = []
            for _ in range(num_obs):
                while True:
                    x = random.randint(0, CELL_NUMBER - 1)
                    y = random.randint(0, CELL_NUMBER - 1)
                    pos = Vector2(x, y)
                    if pos not in self.snake.body and pos not in [f.pos for f in self.foods]:
                        self.obstacles.append(pos)
                        break

    def check_collision(self):
        head = self.snake.body[0]
        
        # Check foods
        for f in self.foods[:]:
            if head == f.pos:
                if f.is_poison:
                    self.snake.shrink()
                    if len(self.snake.body) < 3:
                        self.game_over()
                    self.foods.remove(f)
                else:
                    self.snake.add_block()
                    self.score += 10 * self.multiplier
                    self.foods_eaten_level += 1
                    self.foods.remove(f)
                    
                    if self.foods_eaten_level >= 3:
                        self.level += 1
                        self.foods_eaten_level = 0
                        self.update_speed()
                        self.generate_obstacles()
                        
                # Ensure at least 1 normal food
                if not any(not f.is_poison for f in self.foods):
                    new_food = FOOD(is_poison=False)
                    new_food.randomize(self.snake.body, self.obstacles, self.powerups, self.foods)
                    self.foods.append(new_food)
                    
                # Chance to spawn poison
                if random.random() < 0.2 and not any(f.is_poison for f in self.foods):
                    p_food = FOOD(is_poison=True)
                    p_food.randomize(self.snake.body, self.obstacles, self.powerups, self.foods)
                    self.foods.append(p_food)

                # Chance to spawn powerup
                if random.random() < 0.15 and len(self.powerups) == 0:
                    p = POWERUP(random.randint(0,2))
                    p.randomize(self.snake.body, self.obstacles, self.foods)
                    self.powerups.append(p)

        # Check powerups
        for p in self.powerups[:]:
            if head == p.pos:
                self.active_powerup_type = p.type_id
                self.powerup_end_time = pygame.time.get_ticks() + 10000 # 10 secs
                self.powerups.remove(p)
                
                if self.active_powerup_type == 0:
                    self.update_speed()
                elif self.active_powerup_type == 1:
                    self.multiplier = 2
                elif self.active_powerup_type == 2:
                    self.ghost_mode = True

        # Check walls and self
        if not self.ghost_mode:
            if not (0 <= head.x < CELL_NUMBER and 0 <= head.y < CELL_NUMBER):
                self.game_over()
            for block in self.snake.body[1:]:
                if block == head:
                    self.game_over()
            if head in self.obstacles:
                self.game_over()
        else:
            # Wrap around walls in ghost mode
            if head.x < 0: self.snake.body[0].x = CELL_NUMBER - 1
            elif head.x >= CELL_NUMBER: self.snake.body[0].x = 0
            if head.y < 0: self.snake.body[0].y = CELL_NUMBER - 1
            elif head.y >= CELL_NUMBER: self.snake.body[0].y = 0

    def update(self):
        if self.state == "GAME" and not self.game_over_flag:
            self.snake.move_snake()
            self.check_collision()
            
            # Update powerups logic
            if self.active_powerup_type != -1 and pygame.time.get_ticks() > self.powerup_end_time:
                self.active_powerup_type = -1
                self.multiplier = 1
                self.ghost_mode = False
                self.update_speed()
                
            current_time = pygame.time.get_ticks()
            for p in self.powerups[:]:
                if current_time - p.spawn_time > 15000:
                    self.powerups.remove(p)

    def draw_elements(self):
        if settings.get("grid_visible", True):
            for x in range(CELL_NUMBER + 1):
                pygame.draw.line(screen, (160, 200, 60), (x*CELL_SIZE, 0), (x*CELL_SIZE, SCREEN_HEIGHT))
            for y in range(CELL_NUMBER + 1):
                pygame.draw.line(screen, (160, 200, 60), (0, y*CELL_SIZE), (GAME_WIDTH, y*CELL_SIZE))

        # Sidebar background
        sidebar_rect = pygame.Rect(GAME_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (40, 40, 40), sidebar_rect)
        pygame.draw.line(screen, (100, 100, 100), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

        for obs in self.obstacles:
            r = pygame.Rect(int(obs.x * CELL_SIZE), int(obs.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (100, 50, 50), r)

        for p in self.powerups:
            p.draw(screen)

        for f in self.foods:
            f.draw_food(screen)
            
        self.snake.draw_snake(screen, settings.get("snake_color", [0, 255, 0]))
        self.draw_hud()
        self.draw_sidebar()

    def draw_hud(self):
        score_text = font_small.render(f"Score: {self.score}", True, COLOR_TEXT)
        pb_text = font_small.render(f"PB: {self.personal_best}", True, COLOR_TEXT)
        screen.blit(score_text, (10, 10))
        screen.blit(pb_text, (10, 40))

    def draw_sidebar(self):
        # Sidebar Header
        header_font = pygame.font.SysFont("Segoe UI", 30, bold=True)
        header = header_font.render("EFFECTS", True, (255, 255, 255))
        screen.blit(header, (GAME_WIDTH + SIDEBAR_WIDTH // 2 - header.get_width() // 2, 20))

        y_offset = 80
        
        # 1. Level Info
        level_txt = font_small.render(f"Level: {self.level}", True, (200, 200, 200))
        screen.blit(level_txt, (GAME_WIDTH + 20, y_offset))
        y_offset += 40
        
        # Progress to next level
        pygame.draw.rect(screen, (60, 60, 60), (GAME_WIDTH + 20, y_offset, SIDEBAR_WIDTH - 40, 10))
        progress_w = (self.foods_eaten_level / 3) * (SIDEBAR_WIDTH - 40)
        pygame.draw.rect(screen, (0, 255, 100), (GAME_WIDTH + 20, y_offset, progress_w, 10))
        y_offset += 60

        # 2. Speed Effect
        current_speed_factor = 150 / self.tick_delay
        
        speed_icon_rect = pygame.Rect(GAME_WIDTH + 20, y_offset, 40, 40)
        screen.blit(speed_icon, speed_icon_rect)
        speed_text = font_small.render(f"Speed: x{current_speed_factor:.1f}", True, (255, 255, 255))
        screen.blit(speed_text, (GAME_WIDTH + 70, y_offset + 5))
        y_offset += 60

        # 3. Multiplier Effect
        mult_icon_rect = pygame.Rect(GAME_WIDTH + 20, y_offset, 40, 40)
        screen.blit(score_icon, mult_icon_rect)
        mult_text = font_small.render(f"Score: x{self.multiplier}", True, (255, 255, 255))
        screen.blit(mult_text, (GAME_WIDTH + 70, y_offset + 5))
        y_offset += 60

        # 4. Ghost Mode
        ghost_icon_rect = pygame.Rect(GAME_WIDTH + 20, y_offset, 40, 40)
        screen.blit(ghost_icon, ghost_icon_rect)
        ghost_color = (0, 255, 100) if self.ghost_mode else (150, 150, 150)
        ghost_text = font_small.render("Ghost Mode", True, ghost_color)
        screen.blit(ghost_text, (GAME_WIDTH + 70, y_offset + 5))
        y_offset += 70

        # Active Powerup Countdown
        if self.active_powerup_type != -1:
            time_left = max(0, (self.powerup_end_time - pygame.time.get_ticks()) // 1000)
            timer_text = font_small.render(f"Active: {time_left}s", True, (255, 100, 100))
            # Draw a small countdown circle
            pygame.draw.arc(screen, (255, 100, 100), (GAME_WIDTH + SIDEBAR_WIDTH - 50, y_offset - 100, 30, 30), 0, (time_left/10) * 6.28, 3)
            screen.blit(timer_text, (GAME_WIDTH + 20, y_offset))

    def game_over(self):
        self.game_over_flag = True
        self.state = "GAME_OVER"
        if self.username:
            try:
                db.save_game_session(self.username, self.score, self.level)
            except Exception as e:
                print(f"Error saving session: {e}")

    def draw_menu(self):
        screen.fill(COLOR_BG)
        title = big_font.render("SNAKE GAME PRO", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        prompt = font_small.render("Enter Username:", True, COLOR_TEXT)
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 250))
        
        pygame.draw.rect(screen, (255,255,255), (SCREEN_WIDTH//2 - 150, 290, 300, 40))
        name_txt = font_main.render(self.username, True, (0,0,0))
        screen.blit(name_txt, (SCREEN_WIDTH//2 - 140, 285))
        
        self.draw_button("START", SCREEN_WIDTH//2, 400)
        self.draw_button("LEADERBOARD", SCREEN_WIDTH//2, 470)
        self.draw_button("SETTINGS", SCREEN_WIDTH//2, 540)

    def draw_button(self, text, x, y, w=250, h=50):
        mouse_pos = pygame.mouse.get_pos()
        rect = pygame.Rect(x - w//2, y, w, h)
        color = COLOR_BUTTON_HOVER if rect.collidepoint(mouse_pos) else COLOR_BUTTON
        pygame.draw.rect(screen, color, rect, border_radius=10)
        txt = font_main.render(text, True, (255,255,255))
        screen.blit(txt, (x - txt.get_width()//2, y + h//2 - txt.get_height()//2))
        return rect

    def draw_game_over(self):
        screen.fill(COLOR_BG)
        title = big_font.render("GAME OVER", True, (200, 50, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        info = font_main.render(f"Score: {self.score} | Level: {self.level}", True, COLOR_TEXT)
        screen.blit(info, (SCREEN_WIDTH//2 - info.get_width()//2, 250))
        
        self.btn_menu = self.draw_button("MAIN MENU", SCREEN_WIDTH//2, 400)
        self.btn_restart = self.draw_button("RESTART", SCREEN_WIDTH//2, 470)

    def draw_leaderboard(self):
        screen.fill(COLOR_BG)
        title = big_font.render("LEADERBOARD", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        try:
            top10 = db.get_top_10()
            y = 130
            for i, row in enumerate(top10):
                txt = font_small.render(f"{i+1}. {row[0]} - Score: {row[1]} (Lvl {row[2]})", True, COLOR_TEXT)
                screen.blit(txt, (100, y))
                y += 40
        except Exception as e:
            err = font_small.render("Database error (check connection)", True, (255,0,0))
            screen.blit(err, (100, 150))
            
        self.btn_back = self.draw_button("BACK", SCREEN_WIDTH//2, 600)

    def draw_settings(self):
        screen.fill(COLOR_BG)
        title = big_font.render("SETTINGS", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        grid_status = "ON" if settings.get("grid_visible", True) else "OFF"
        self.btn_grid = self.draw_button(f"Grid: {grid_status}", SCREEN_WIDTH//2, 250)
        
        sound_status = "ON" if settings.get("sound_on", True) else "OFF"
        self.btn_sound = self.draw_button(f"Sound: {sound_status}", SCREEN_WIDTH//2, 320)

        # Volume control
        vol_label = font_small.render(f"Volume: {int(self.volume * 100)}%", True, COLOR_TEXT)
        screen.blit(vol_label, (SCREEN_WIDTH//2 - vol_label.get_width()//2, 380))
        
        # Volume bar
        bar_x = SCREEN_WIDTH//2 - 100
        bar_y = 420
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, 200, 10), border_radius=5)
        pygame.draw.rect(screen, COLOR_BUTTON, (bar_x, bar_y, int(self.volume * 200), 10), border_radius=5)
        
        self.btn_vol_down = self.draw_button("-", SCREEN_WIDTH//2 - 130, 405, w=40, h=40)
        self.btn_vol_up = self.draw_button("+", SCREEN_WIDTH//2 + 130, 405, w=40, h=40)
        
        self.btn_back = self.draw_button("BACK", SCREEN_WIDTH//2, 600)

    def run(self):
        global big_font # Need to init here in case pygame.init isn't fully ready
        big_font = pygame.font.SysFont("Segoe UI", 50, bold=True)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if self.state == "GAME":
                    if event.type == SCREEN_UPDATE:
                        self.direction_changed = False
                        self.update()
                    if event.type == pygame.KEYDOWN and not self.game_over_flag:
                        if not self.direction_changed:
                            if event.key == pygame.K_UP and self.snake.direction.y != 1:
                                self.snake.direction = Vector2(0, -1)
                                self.direction_changed = True
                            elif event.key == pygame.K_DOWN and self.snake.direction.y != -1:
                                self.snake.direction = Vector2(0, 1)
                                self.direction_changed = True
                            elif event.key == pygame.K_LEFT and self.snake.direction.x != 1:
                                self.snake.direction = Vector2(-1, 0)
                                self.direction_changed = True
                            elif event.key == pygame.K_RIGHT and self.snake.direction.x != -1:
                                self.snake.direction = Vector2(1, 0)
                                self.direction_changed = True
                            
                elif self.state == "MENU":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            self.username = self.username[:-1]
                        else:
                            if len(self.username) < 15 and event.unicode.isprintable():
                                self.username += event.unicode
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.draw_button("START", SCREEN_WIDTH//2, 400).collidepoint(event.pos):
                            if self.username.strip() == "": self.username = "Guest"
                            try:
                                self.personal_best = db.get_personal_best(self.username)
                            except:
                                self.personal_best = 0
                            self.reset_game()
                            self.state = "GAME"
                        elif self.draw_button("LEADERBOARD", SCREEN_WIDTH//2, 470).collidepoint(event.pos):
                            self.state = "LEADERBOARD"
                        elif self.draw_button("SETTINGS", SCREEN_WIDTH//2, 540).collidepoint(event.pos):
                            self.state = "SETTINGS"
                            
                elif self.state == "GAME_OVER":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_menu.collidepoint(event.pos):
                            self.state = "MENU"
                        elif self.btn_restart.collidepoint(event.pos):
                            try:
                                self.personal_best = db.get_personal_best(self.username)
                            except:
                                self.personal_best = 0
                            self.reset_game()
                            self.state = "GAME"
                            
                elif self.state == "LEADERBOARD":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_back.collidepoint(event.pos):
                            self.state = "MENU"
                            
                elif self.state == "SETTINGS":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_grid.collidepoint(event.pos):
                            settings["grid_visible"] = not settings.get("grid_visible", True)
                            save_settings(settings)
                        elif self.btn_sound.collidepoint(event.pos):
                            settings["sound_on"] = not settings.get("sound_on", True)
                            if settings["sound_on"]:
                                pygame.mixer.music.play(-1)
                            else:
                                pygame.mixer.music.stop()
                            save_settings(settings)
                        elif self.btn_vol_down.collidepoint(event.pos):
                            self.volume = max(0, self.volume - 0.1)
                            pygame.mixer.music.set_volume(self.volume)
                            settings["volume"] = self.volume
                            save_settings(settings)
                        elif self.btn_vol_up.collidepoint(event.pos):
                            self.volume = min(1.0, self.volume + 0.1)
                            pygame.mixer.music.set_volume(self.volume)
                            settings["volume"] = self.volume
                            save_settings(settings)
                        elif self.btn_back.collidepoint(event.pos):
                            self.state = "MENU"

            if self.state == "GAME":
                screen.fill(COLOR_BG)
                self.draw_elements()
            elif self.state == "MENU":
                self.draw_menu()
            elif self.state == "GAME_OVER":
                self.draw_game_over()
            elif self.state == "LEADERBOARD":
                self.draw_leaderboard()
            elif self.state == "SETTINGS":
                self.draw_settings()
                
            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    try:
        db.init_db()
    except Exception as e:
        print(f"DB Init Warning: {e}")
    game = MAIN()
    game.run()
