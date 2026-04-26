"""
Racer Game - Configuration & Utilities
Constants, colors, difficulty settings, and JSON load/save.
"""
import json
import os

# --- Screen ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# --- Road Layout ---
ROAD_LEFT = 100
ROAD_RIGHT = 500
ROAD_WIDTH = 400
NUM_LANES = 4
LANE_WIDTH = ROAD_WIDTH // NUM_LANES
LANE_CENTERS = [ROAD_LEFT + LANE_WIDTH * i + LANE_WIDTH // 2 for i in range(NUM_LANES)]

# --- Colors ---
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
GRAY        = (100, 100, 100)
DARK_GRAY   = (50,  50,  50)
ROAD_COLOR  = (60,  60,  65)
GRASS_GREEN = (34, 120,  34)
GRASS_DARK  = (28, 100,  28)
RED         = (220, 50,  50)
GREEN       = (50, 200,  80)
BLUE        = (50, 100, 220)
YELLOW      = (240, 220, 40)
CYAN        = (50, 200, 220)
ORANGE      = (240, 150, 30)
MAGENTA     = (200, 50, 180)
GOLD_COLOR  = (255, 215,  0)
SILVER_COLOR= (192, 192, 192)
BRONZE_COLOR= (205, 127, 50)
SHIELD_BLUE = (80, 160, 255)
NITRO_CYAN  = (0, 230, 255)
REPAIR_GREEN= (0, 230, 100)
HP_RED      = (200, 40, 40)
HP_GREEN    = (40, 200, 60)
OIL_COLOR   = (30,  30,  40)
POTHOLE_COLOR = (80, 70, 55)
HUD_BG      = (20, 20, 30, 180)

# --- Car Color Options ---
CAR_COLORS = {
    "red":    (220, 50,  50),
    "blue":   (50, 100, 220),
    "green":  (50, 180,  80),
    "yellow": (240, 220, 40),
    "purple": (150, 50, 200),
    "orange": (240, 150, 30),
    "cyan":   (50, 200, 220),
    "white":  (230, 230, 230),
}

# --- Coin Types ---
COIN_TYPES = {
    "bronze": {"value": 1, "color": BRONZE_COLOR, "radius": 12},
    "silver": {"value": 2, "color": SILVER_COLOR, "radius": 13},
    "gold":   {"value": 3, "color": GOLD_COLOR,   "radius": 14},
}

# --- Difficulty Presets ---
DIFFICULTY = {
    "easy":   {"base_speed": 2.0, "spawn_interval": 90, "coin_interval": 55},
    "medium": {"base_speed": 3.0, "spawn_interval": 70, "coin_interval": 45},
    "hard":   {"base_speed": 4.0, "spawn_interval": 50, "coin_interval": 35},
}

# --- Damage Table ---
# damage[player_type] = {"side": hp_loss, "head_on": hp_loss}
DAMAGE = {
    "car":   {"side": 35, "head_on": 100},
    "truck": {"side": 20, "head_on": 80},
}

# --- Power-up Durations (seconds) ---
NITRO_DURATION  = 5.0
SHIELD_DURATION = 10.0
NITRO_MULTIPLIER = 1.4
REPAIR_AMOUNT = 35
MAX_HP = 100

# --- Player ---
PLAYER_WIDTH  = 50
PLAYER_HEIGHT = 90
PLAYER_SPEED  = 5

# --- Files ---
SETTINGS_FILE    = os.path.join(os.path.dirname(__file__), "settings.json")
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "leaderboard.json")

DEFAULT_SETTINGS = {
    "sound": True,
    "car_model": "Sedan",
    "car_color": "red",
    "difficulty": "medium",
}


def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                loaded = json.load(f)
                settings.update(loaded)
        except Exception:
            pass
    # Ensure car_model exists if it was missing from an old save
    if "car_model" not in settings:
        settings["car_model"] = "Sedan"
    return settings


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_leaderboard(score, name):
    lb = load_leaderboard()
    lb.append({"name": name, "score": score})
    lb = sorted(lb, key=lambda x: x["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(lb, f, indent=4)
    return lb
