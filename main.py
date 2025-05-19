import pygame
import random
import os
import sqlite3
import math
from database import register_user, login_user, get_high_score, update_high_score, get_top_players

# Init
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🍎 Sugar Rush Run 🍩")

# Colors
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLACK = (0, 0, 0)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28)

# Load assets
def load_asset(name, size=(40, 40)):
    return pygame.transform.scale(
        pygame.image.load(os.path.join("assets", name)).convert_alpha(), size
    )

def load_sound(name):
    return pygame.mixer.Sound(os.path.join("assets", name))

# Load BG & Sounds
BG_IMG = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "background.png")).convert(), (WIDTH, HEIGHT)
)
collect_sound = load_sound("collect.wav")
powerup_sound = load_sound("powerup.wav")
gameover_sound = load_sound("gameover.wav")
explosion_sound = load_sound("explosion.wav")  # You'll need to add this sound file

# Characters
CHARACTER_OPTIONS = [
    load_asset(f"fp{i}.png", (60, 60)) for i in range(1, 10)
] + [
    load_asset(f"mp{i}.png", (60, 60)) for i in range(1, 10)
]

# Items
HEALTHY_ITEMS = [("apple.png", 10), ("banana.png", 10), ("carrot.png", 15),
                 ("orange.png", 10), ("pineapple.png", 15), ("watermelon.png", 20)]
SUGARY_ITEMS = [("donut.png", 10), ("cupcake.png", 15), ("icecream.png", 15),
                ("chocolate.png", 20), ("lollipop.png", 10),]
WATER_IMG = load_asset("waterbottle.png")

BOMB_IMG = load_asset("sugarcube.png")

# Particle class for explosion effect
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed = random.uniform(1, 5)
        self.angle = random.uniform(0, math.pi * 2)
        self.lifetime = random.randint(20, 40)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        if self.lifetime > 10:  # Shrink after initial burst
            self.size = max(1, self.size - 0.1)
        
    def draw(self, surface):
        alpha = min(255, self.lifetime * 6)  # Fade out
        color_with_alpha = (*self.color, alpha)
        particle_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color_with_alpha, (self.size, self.size), self.size)
        surface.blit(particle_surf, (self.x - self.size, self.y - self.size))

# Floating text class
class FloatingText:
    def __init__(self, x, y, text, color=GREEN):
        self.x = x
        self.y = y
        self.text = font.render(text, True, color)
        self.timer = 60

    def update(self):
        self.y -= 1
        self.timer -= 1

    def draw(self, surface):
        surface.blit(self.text, (self.x, self.y))

# Player
class Player:
    def __init__(self, image):
        self.image = image
        self.x = 100
        self.y = HEIGHT // 2
        self.speed = 5
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def move(self, keys):
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < HEIGHT - 60:
            self.y += self.speed
        self.rect.topleft = (self.x, self.y)

    def draw(self):
        win.blit(self.image, (self.x, self.y))

# Game item
class GameItem:
    def __init__(self, image, bad=False, value=10, powerup=False):
        self.x = WIDTH + random.randint(0, 200)
        self.y = random.randint(50, HEIGHT - 50)
        self.image = image
        self.bad = bad
        self.value = value
        self.powerup = powerup
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def move(self):
        self.x -= 7
        self.rect.topleft = (self.x, self.y)

    def draw(self):
        win.blit(self.image, (self.x, self.y))

# Screens
def draw_window(player, items, score, sugar_level, float_texts, particles):
    win.blit(BG_IMG, (0, 0))
    player.draw()
    for item in items:
        item.draw()
    for ftext in float_texts:
        ftext.draw(win)
    for particle in particles:
        particle.draw(win)

    score_text = font.render(f"Score: {score}", True, WHITE)
    win.blit(score_text, (10, 10))
    pygame.draw.rect(win, RED, (10, 50, sugar_level * 2, 20))
    pygame.draw.rect(win, WHITE, (10, 50, 200, 20), 2)
    pygame.display.update()

def game_over_screen(score):
    showing = True
    while showing:
        win.fill((0, 0, 0))

        game_over_text = font.render(f"Game Over! Score: {score}", True, (255, 0, 0))
        restart_text = font.render("Press R to Restart", True, (255, 255, 255))
        leaderboard_text = font.render("Press L to View Leaderboard", True, (255, 255, 255))

        win.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 200))
        win.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 300))
        win.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, 350))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    showing = False
                elif event.key == pygame.K_l:
                    leaderboard_screen()

def welcome_screen():
    title = pygame.font.SysFont("Arial", 40).render("Welcome to Sugar Rush Run", True, WHITE)
    instruction = font.render("Press Enter to Start!", True, WHITE)

    while True:
        win.fill((10, 10, 30))
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 40))
        win.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 10))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

def select_character():
    selected_index = 0
    cols = 9
    rows = (len(CHARACTER_OPTIONS) + cols - 1) // cols
    cell_w, cell_h = 80, 80
    margin_x = (WIDTH - cols * cell_w) // 2
    margin_y = 120

    while True:
        win.fill((20, 20, 40))
        title = font.render("Choose Your Character", True, WHITE)
        instruction = font.render("Use ← → ↑ ↓ to choose your runner. Press Enter to start!", True, WHITE)
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
        win.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 70))

        # Draw characters
        for idx, char in enumerate(CHARACTER_OPTIONS):
            row = idx // cols
            col = idx % cols
            x = margin_x + col * cell_w
            y = margin_y + row * cell_h
            rect = pygame.Rect(x, y, 60, 60)

            if idx == selected_index:
                pygame.draw.rect(win, GREEN, rect.inflate(10, 10), 3)
            else:
                pygame.draw.rect(win, WHITE, rect.inflate(10, 10), 1)

            win.blit(char, (x, y))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                row = selected_index // cols
                col = selected_index % cols

                if event.key == pygame.K_LEFT:
                    col = (col - 1 + cols) % cols
                elif event.key == pygame.K_RIGHT:
                    col = (col + 1) % cols
                elif event.key == pygame.K_UP:
                    row = (row - 1 + rows) % rows
                elif event.key == pygame.K_DOWN:
                    row = (row + 1) % rows
                elif event.key == pygame.K_RETURN:
                    return CHARACTER_OPTIONS[selected_index]

                new_index = row * cols + col
                if 0 <= new_index < len(CHARACTER_OPTIONS):
                    selected_index = new_index

def draw_input_box(surface, rect, text, active):
    color = (200, 200, 255) if active else (180, 180, 180)
    pygame.draw.rect(surface, color, rect, 2)
    txt_surface = font.render(text, True, WHITE)
    surface.blit(txt_surface, (rect.x + 5, rect.y + 5))

def login_screen():
    username = ""
    password = ""
    active_field = "username"
    info_msg = ""
    
    input_box_user = pygame.Rect(WIDTH//2 - 100, 200, 200, 40)
    input_box_pass = pygame.Rect(WIDTH//2 - 100, 260, 200, 40)
    button_login = pygame.Rect(WIDTH//2 - 100, 320, 90, 40)
    button_register = pygame.Rect(WIDTH//2 + 10, 320, 90, 40)

    while True:
        win.fill((30, 30, 60))
        title = font.render("Login / Register", True, WHITE)
        win.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        # Draw input fields
        draw_input_box(win, input_box_user, "Username: " + username, active_field == "username")
        draw_input_box(win, input_box_pass, "Password: " + '*'*len(password), active_field == "password")

        pygame.draw.rect(win, GREEN, button_login)
        pygame.draw.rect(win, RED, button_register)
        win.blit(font.render("Login", True, BLACK), (button_login.x + 10, button_login.y + 5))
        win.blit(font.render("Register", True, BLACK), (button_register.x + 5, button_register.y + 5))

        if info_msg:
            msg = font.render(info_msg, True, WHITE)
            win.blit(msg, (WIDTH//2 - msg.get_width()//2, 380))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box_user.collidepoint(event.pos):
                    active_field = "username"
                elif input_box_pass.collidepoint(event.pos):
                    active_field = "password"
                elif button_login.collidepoint(event.pos):
                    if login_user(username, password):
                        return username
                    else:
                        info_msg = "❌ Invalid credentials."
                elif button_register.collidepoint(event.pos):
                    if register_user(username, password):
                        info_msg = "✅ Registered! You can now login."
                    else:
                        info_msg = "⚠ Username taken."
            elif event.type == pygame.KEYDOWN:
                if active_field == "username":
                    if event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_field = "password"
                    else:
                        username += event.unicode
                elif active_field == "password":
                    if event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    elif event.key == pygame.K_RETURN:
                        pass
                    else:
                        password += event.unicode

def leaderboard_screen():
    from database import get_top_players

    running = True
    while running:
        win.fill((30, 30, 30))
        title = font.render("🏆 Leaderboard", True, (255, 255, 255))
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        top_players = get_top_players(5)
        for i, (username, score) in enumerate(top_players):
            entry = font.render(f"{i+1}. {username} - {score}", True, (255, 255, 255))
            win.blit(entry, (WIDTH // 2 - entry.get_width() // 2, 120 + i * 40))

        back_text = font.render("Press ESC to return", True, (200, 200, 200))
        win.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 60))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

def create_explosion(x, y):
    particles = []
    explosion_sound.play()
    for _ in range(50):  # Create 50 particles
        color = random.choice([(255, 255, 255), (255, 200, 200), (255, 255, 200)])
        particles.append(Particle(x, y, color))
    return particles

def main():
    welcome_screen()

    # 👤 Login system
    username = login_screen()
    high_score = get_high_score(username)

    player_img = select_character()
    player = Player(player_img)
    items = []
    score = 0
    sugar_level = 0
    float_texts = []
    particles = []

    run = True
    while run:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if random.randint(1, 40) == 1:
            name, value = random.choice(HEALTHY_ITEMS)
            image = load_asset(name)
            items.append(GameItem(image, bad=False, value=value))

        if random.randint(1, 60) == 1:
            name, value = random.choice(SUGARY_ITEMS)
            image = load_asset(name)
            items.append(GameItem(image, bad=True, value=value))

        if random.randint(1, 200) == 1:
            items.append(GameItem(WATER_IMG, powerup=True, value=25))

        if random.randint(1, 300) == 1:
            items.append(GameItem(BOMB_IMG, bad=True, value=100))

        player.move(keys)
        for item in items:
            item.move()
        items = [item for item in items if item.x + 40 > 0]

        # Update particles
        for particle in particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                particles.remove(particle)

        for item in items[:]:
            if player.rect.colliderect(item.rect):
                if item.powerup:
                    sugar_level = max(0, sugar_level - item.value)
                    powerup_sound.play()
                    float_texts.append(FloatingText(player.x + 40, player.y, f"-{item.value}", RED))
                elif item.bad:
                    if item.image == BOMB_IMG:  # Sugar cube explosion
                        particles.extend(create_explosion(item.x + 20, item.y + 20))
                        gameover_sound.play()
                    sugar_level += item.value
                else:
                    score += item.value
                    collect_sound.play()
                    float_texts.append(FloatingText(player.x + 40, player.y, f"+{item.value}", GREEN))
                items.remove(item)

        if sugar_level >= 100:
            if score > high_score:
                update_high_score(username, score)
            game_over_screen(score)
            main()  # Restart the game
            return  # Prevent further code from running

        for f in float_texts[:]:
            f.update()
            if f.timer <= 0:
                float_texts.remove(f)

        draw_window(player, items, score, sugar_level, float_texts, particles)

    pygame.quit()

if __name__ == "__main__":
    main()