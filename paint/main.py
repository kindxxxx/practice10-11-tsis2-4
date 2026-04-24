import pygame
import sys
import math
import os
from datetime import datetime
from collections import deque

# ===========================================
# Инициализация Pygame
# ===========================================
pygame.init()

# --- Размеры окна ---
WIDTH, HEIGHT = 900, 700  # Чуть больше для простора
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Modern Paint Pro")

# --- Цветовая палитра (Modern Dark Theme) ---
COLOR_ACCENT = (114, 137, 218)    # Акцентный синий (Discord-style)
COLOR_BG_DARK = (40, 42, 54)      # Фон панели (Dracula theme)
COLOR_BTN_NORMAL = (56, 58, 89)   # Цвет кнопок
COLOR_BTN_HOVER = (68, 71, 90)    # При наведении
COLOR_TEXT = (248, 248, 242)      # Светлый текст
COLOR_BORDER = (98, 114, 164)     # Границы

# --- Шрифты ---
font_main = pygame.font.SysFont("Segoe UI", 14, bold=True)
font_small = pygame.font.SysFont("Segoe UI", 12)
font_text_tool = pygame.font.SysFont("Arial", 22)

# ===========================================
# Холст (Canvas)
# ===========================================
UI_WIDTH = 130
canvas_rect = pygame.Rect(UI_WIDTH, 0, WIDTH - UI_WIDTH, HEIGHT)
canvas = pygame.Surface((canvas_rect.width, canvas_rect.height))
canvas.fill((255, 255, 255))

# ===========================================
# Инструменты и Кнопки
# ===========================================
tool_defs = [
    {"id": "brush",     "label": "Кисть",       "icon": "B"},
    {"id": "pencil",    "label": "Карандаш",    "icon": "P"},
    {"id": "eraser",    "label": "Ластик",      "icon": "E"},
    {"id": "line",      "label": "Линия",       "icon": "/"},
    {"id": "rect",      "label": "Квадрат",     "icon": "□"},
    {"id": "circle",    "label": "Круг",        "icon": "○"},
    {"id": "rtriangle", "label": "Тр-к (90°)",  "icon": "⊿"},
    {"id": "etriangle", "label": "Тр-к (Рав)",  "icon": "△"},
    {"id": "rhombus",   "label": "Ромб",        "icon": "◇"},
    {"id": "fill",      "label": "Заливка",     "icon": "F"},
    {"id": "text",      "label": "Текст",       "icon": "T"},
]

color_palette = [
    (40, 42, 54), (255, 255, 255), (255, 85, 85), (255, 184, 108),
    (241, 250, 140), (80, 250, 123), (139, 233, 253), (189, 147, 249)
]

# --- Состояние ---
current_tool = "brush"
current_color = (40, 42, 54)
brush_radius = 5
is_drawing = False
start_pos = None
prev_pos = None
text_input_active = False
text_buffer = ""
text_pos = None

# ===========================================
# Функции рисования (Логика)
# ===========================================

def get_canvas_pos(screen_pos):
    """Преобразует координаты экрана в координаты холста."""
    return (screen_pos[0] - UI_WIDTH, screen_pos[1])

def flood_fill(surface, start_x, start_y, fill_color):
    target_color = surface.get_at((start_x, start_y))
    if target_color == fill_color: return
    w, h = surface.get_size()
    queue = deque([(start_x, start_y)])
    visited = {(start_x, start_y)}
    target_tuple = (target_color.r, target_color.g, target_color.b, target_color.a)
    surface.lock()
    while queue:
        x, y = queue.popleft()
        if (surface.get_at((x, y)) != target_tuple): continue
        surface.set_at((x, y), fill_color)
        for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    surface.unlock()

def save_canvas(surface):
    save_dir = "saved"
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    fname = f"paint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    pygame.image.save(surface, os.path.join(save_dir, fname))

# ===========================================
# Отрисовка интерфейса (Дизайн)
# ===========================================

def draw_ui():
    # Фон боковой панели
    pygame.draw.rect(screen, COLOR_BG_DARK, (0, 0, UI_WIDTH, HEIGHT))
    # Разделительная линия
    pygame.draw.line(screen, COLOR_BORDER, (UI_WIDTH, 0), (UI_WIDTH, HEIGHT), 2)

    y = 15
    # Заголовок
    title = font_main.render("TOOLS", True, COLOR_ACCENT)
    screen.blit(title, (UI_WIDTH // 2 - title.get_width() // 2, y))
    y += 25

    # Кнопки инструментов
    btn_w, btn_h = UI_WIDTH - 20, 30
    for tool in tool_defs:
        rect = pygame.Rect(10, y, btn_w, btn_h)
        active = (current_tool == tool["id"])
        
        # Дизайн кнопки
        color = COLOR_ACCENT if active else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, color, rect, border_radius=8)
        if not active and rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, COLOR_BTN_HOVER, rect, border_radius=8)
        
        # Текст и "иконка"
        txt = font_small.render(tool["label"], True, COLOR_TEXT)
        icon = font_main.render(tool["icon"], True, COLOR_TEXT)
        screen.blit(icon, (18, y + btn_h // 2 - icon.get_height() // 2))
        screen.blit(txt, (40, y + btn_h // 2 - txt.get_height() // 2))
        
        y += btn_h + 6

    # Секция цветов
    y += 10
    title_colors = font_main.render("COLORS", True, COLOR_ACCENT)
    screen.blit(title_colors, (UI_WIDTH // 2 - title_colors.get_width() // 2, y))
    y += 25

    grid_x, grid_y = 15, y
    for i, col in enumerate(color_palette):
        rect = pygame.Rect(grid_x + (i % 3) * 35, grid_y + (i // 3) * 35, 30, 30)
        pygame.draw.rect(screen, col, rect, border_radius=6)
        if col == current_color:
            pygame.draw.rect(screen, (255, 255, 255), rect, 3, border_radius=6)
        else:
            pygame.draw.rect(screen, COLOR_BORDER, rect, 1, border_radius=6)
    
    y = grid_y + (len(color_palette) // 3 + 1) * 35 + 15



    #Размеры кист
    title_size = font_main.render("SIZE", True, COLOR_ACCENT)
    screen.blit(title_size, (UI_WIDTH // 2 - title_size.get_width() // 2, y))
    y += 25
    sizes = [3, 7, 12]
    for i, s in enumerate(sizes):
        rect = pygame.Rect(15 + i * 35, y, 30, 30)
        active = (brush_radius == s)
        bg = COLOR_ACCENT if active else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.circle(screen, COLOR_TEXT, rect.center, s//2 + 1)
    
    # Кнопка сохранения в самом низу
    save_rect = pygame.Rect(10, HEIGHT - 50, UI_WIDTH - 20, 35)
    pygame.draw.rect(screen, (40, 167, 69), save_rect, border_radius=10)
    save_txt = font_main.render("SAVE", True, (255, 255, 255))
    screen.blit(save_txt, (save_rect.centerx - save_txt.get_width()//2, save_rect.centery - save_txt.get_height()//2))

# ===========================================
# Функции фигур (Оптимизация)
# ===========================================

def draw_shape(surf, tool, p1, p2, color, radius):
    w = max(2, radius // 2)
    if tool == "line": pygame.draw.line(surf, color, p1, p2, w)
    elif tool == "rect":
        r = pygame.Rect(min(p1[0], p2[0]), min(p1[1], p2[1]), abs(p2[0]-p1[0]), abs(p2[1]-p1[1]))
        if r.width > 0 and r.height > 0: pygame.draw.rect(surf, color, r, w)
    elif tool == "circle":
        rad = int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]))
        if rad > 0: pygame.draw.circle(surf, color, p1, rad, w)
    elif tool == "rtriangle":
        pts = [(p1[0], p2[1]), (p2[0], p2[1]), (p1[0], p1[1])]
        pygame.draw.polygon(surf, color, pts, w)
    elif tool == "etriangle":
        bw = abs(p2[0] - p1[0])
        if bw > 0:
            h = int(bw * 0.866)
            pts = [(min(p1[0], p2[0]), max(p1[1], p2[1])), (max(p1[0], p2[0]), max(p1[1], p2[1])), ((p1[0]+p2[0])//2, max(p1[1], p2[1]) - h)]
            pygame.draw.polygon(surf, color, pts, w)
    elif tool == "rhombus":
        mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2
        pts = [(mx, min(p1[1], p2[1])), (max(p1[0], p2[0]), my), (mx, max(p1[1], p2[1])), (min(p1[0], p2[0]), my)]
        pygame.draw.polygon(surf, color, pts, w)

# ===========================================
# Главный цикл
# ===========================================
clock = pygame.time.Clock()
while True:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if text_input_active:
                if event.key == pygame.K_RETURN:
                    if text_buffer:
                        canvas.blit(font_text_tool.render(text_buffer, True, current_color), text_pos)
                    text_input_active = False; text_buffer = ""
                elif event.key == pygame.K_BACKSPACE: text_buffer = text_buffer[:-1]
                elif event.key == pygame.K_ESCAPE: text_input_active = False
                else: text_buffer += event.unicode
            else:
                if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL): save_canvas(canvas)
                if event.key == pygame.K_1: brush_radius = 3
                if event.key == pygame.K_2: brush_radius = 7
                if event.key == pygame.K_3: brush_radius = 12

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mouse_pos[0] < UI_WIDTH:
                # Клик по UI
                y = 40
                for tool in tool_defs:
                    if pygame.Rect(10, y, UI_WIDTH-20, 30).collidepoint(mouse_pos):
                        current_tool = tool["id"]
                    y += 36
                y += 35 # Colors
                for i, col in enumerate(color_palette):
                    if pygame.Rect(15 + (i%3)*35, y + (i//3)*35, 30, 30).collidepoint(mouse_pos):
                        current_color = col
                y += 85 # Si
                for i, s in enumerate([3, 7, 12]):
                    if pygame.Rect(15 + i*35, y, 30, 30).collidepoint(mouse_pos):
                        brush_radius = s
                if pygame.Rect(10, HEIGHT-50, UI_WIDTH-20, 35).collidepoint(mouse_pos):
                    save_canvas(canvas)
            else:
                # Клик по холсту
                c_pos = get_canvas_pos(mouse_pos)
                if current_tool == "text":
                    text_input_active = True; text_pos = c_pos; text_buffer = ""
                elif current_tool == "fill": flood_fill(canvas, c_pos[0], c_pos[1], current_color)
                else:
                    is_drawing = True; start_pos = c_pos; prev_pos = c_pos
                    if current_tool == "brush": pygame.draw.circle(canvas, current_color, c_pos, brush_radius)
                    elif current_tool == "pencil": canvas.set_at(c_pos, current_color)
                    elif current_tool == "eraser": pygame.draw.circle(canvas, (255,255,255), c_pos, brush_radius+3)

        if event.type == pygame.MOUSEBUTTONUP:
            if is_drawing:
                c_pos = get_canvas_pos(mouse_pos)
                if current_tool in ["line", "rect", "circle", "rtriangle", "etriangle", "rhombus"]:
                    draw_shape(canvas, current_tool, start_pos, c_pos, current_color, brush_radius)
            is_drawing = False

        if event.type == pygame.MOUSEMOTION and is_drawing:
            c_pos = get_canvas_pos(mouse_pos)
            if current_tool == "brush":
                pygame.draw.line(canvas, current_color, prev_pos, c_pos, brush_radius*2)
                pygame.draw.circle(canvas, current_color, c_pos, brush_radius)
            elif current_tool == "pencil": pygame.draw.line(canvas, current_color, prev_pos, c_pos, 1)
            elif current_tool == "eraser":
                pygame.draw.line(canvas, (255,255,255), prev_pos, c_pos, (brush_radius+3)*2)
                pygame.draw.circle(canvas, (255,255,255), c_pos, brush_radius+3)
            prev_pos = c_pos

    # Отрисовка
    screen.fill((50, 54, 66)) # Фон за холстом
    screen.blit(canvas, (UI_WIDTH, 0))
    
    if is_drawing and current_tool in ["line", "rect", "circle", "rtriangle", "etriangle", "rhombus"]:
        # Превью
        preview = canvas.copy()
        draw_shape(preview, current_tool, start_pos, get_canvas_pos(mouse_pos), current_color, brush_radius)
        screen.blit(preview, (UI_WIDTH, 0))
    
    if text_input_active:
        txt_surf = font_text_tool.render(text_buffer + "|", True, current_color)
        screen.blit(txt_surf, (text_pos[0] + UI_WIDTH, text_pos[1]))

    draw_ui()
    pygame.display.flip()
    clock.tick(60)