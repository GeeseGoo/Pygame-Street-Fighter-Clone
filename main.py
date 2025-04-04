# Street Fighter Pygame Clone
# Version 1.0.0
# Created for itch.io
# Charles Huang 6/17/2022
# Keyboard Controls -- WASD for movement UIOJKL for attack
# Controller controls -- left stick for movement, abxy + bumpers for attack
# Special move -- Hadouken -- Down, Down-Forward, Forward + Punch
import pygame
from pygame.locals import *
from lib import *
from time import sleep
from settings import *
import random
import os
import sys

# Initialize pygame
pygame.init()
pygame.display.set_caption("Street Fighter Pygame Clone v1.0.0")
#disp = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
disp = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()

# Game states
MENU = 0
GAME = 1
GAME_OVER = 2
current_state = MENU

# Font setup
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

def draw_menu():
    disp.fill((0, 0, 0))
    title = font.render("Street Fighter Pygame Clone", True, (255, 255, 255))
    start_text = small_font.render("Press SPACE to Start", True, (255, 255, 255))
    
    # Basic controls
    controls_title = small_font.render("Basic Controls:", True, (255, 255, 255))
    p1_controls = small_font.render("Player 1: WASD + UIOJKL", True, (255, 255, 255))
    p2_controls = small_font.render("Player 2: Arrow Keys + 123456", True, (255, 255, 255))
    
    # Special moves
    special_title = small_font.render("Special Moves:", True, (255, 255, 255))
    hadouken = small_font.render("Hadouken: Down, Down-Forward, Forward + Punch", True, (255, 255, 255))
    shoryuken = small_font.render("Shoryuken: Forward, Down, Down-Forward + Punch", True, (255, 255, 255))
    
    # Attack descriptions
    attack_title = small_font.render("Attack Buttons:", True, (255, 255, 255))
    p1_attacks = small_font.render("Player 1: U=Low Punch, I=Medium Punch, O=High Punch, J=Low Kick, K=Medium Kick, L=High Kick", True, (255, 255, 255))
    p2_attacks = small_font.render("Player 2: 1=Low Punch, 2=Medium Punch, 3=High Punch, 4=Low Kick, 5=Medium Kick, 6=High Kick", True, (255, 255, 255))
    
    # Draw all elements
    disp.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
    disp.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 200))
    
    # Basic controls
    disp.blit(controls_title, (SCREEN_WIDTH//2 - controls_title.get_width()//2, 300))
    disp.blit(p1_controls, (SCREEN_WIDTH//2 - p1_controls.get_width()//2, 350))
    disp.blit(p2_controls, (SCREEN_WIDTH//2 - p2_controls.get_width()//2, 400))
    
    # Attack descriptions
    disp.blit(attack_title, (SCREEN_WIDTH//2 - attack_title.get_width()//2, 450))
    disp.blit(p1_attacks, (SCREEN_WIDTH//2 - p1_attacks.get_width()//2, 500))
    disp.blit(p2_attacks, (SCREEN_WIDTH//2 - p2_attacks.get_width()//2, 550))
    
    # Special moves
    disp.blit(special_title, (SCREEN_WIDTH//2 - special_title.get_width()//2, 600))
    disp.blit(hadouken, (SCREEN_WIDTH//2 - hadouken.get_width()//2, 650))
    disp.blit(shoryuken, (SCREEN_WIDTH//2 - shoryuken.get_width()//2, 700))

def draw_game_over(winner):
    disp.fill((0, 0, 0))
    game_over = font.render(f"PLAYER {winner} WINS!", True, (255, 255, 255))
    restart_text = small_font.render("PRESS ANY KEY TO PLAY AGAIN", True, (255, 255, 255))
    menu_text = small_font.render("PRESS ESC TO RETURN TO MENU", True, (255, 255, 255))
    
    # Draw all elements
    disp.blit(game_over, (SCREEN_WIDTH//2 - game_over.get_width()//2, 300))
    disp.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))
    disp.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, 450))

playersize = [144*5, 130*5]
#playersize = [144, 130] #  small

# Load all music into a list
music = []
try:
    if not os.path.exists("./music"):
        os.makedirs("./music")
    for filename in os.listdir("./music"):
        if filename.endswith(".mp3"):
            music.append("./music/" + filename)
except Exception as e:
    print(f"Warning: Could not load music directory: {e}")

# Start up music
pygame.mixer.set_num_channels(2)
if music:
    try:
        pygame.mixer.music.load(random.choice(music))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(MIDIIN)
    except Exception as e:
        print(f"Warning: Could not play music: {e}")

# Game is designed for keyboard + controller. Without controller both characters will be mirrors of each other
try:
    controller = pygame.joystick.Joystick(0)
    controller.init()
    print("Controller found, using controller for Player 2")
    use_controller = True
except:
    print("No controller found, using keyboard for both players")
    controller = None
    use_controller = False

# Load background
try:
    background = pygame.transform.scale(pygame.image.load("./stage.png").convert_alpha(), (1920, 1080))
except Exception as e:
    print(f"Warning: Could not load background: {e}")
    background = pygame.Surface((1920, 1080))
    background.fill((0, 0, 0))

# Initialize players
player1 = Ryu(False, None, [0, FLOOR], playersize, None, disp)
player1.player = 0  # Set player number for key binding
if use_controller:
    player2 = Ryu(True, controller, [1600, FLOOR], playersize, player1, disp)
else:
    player2 = Ryu(True, None, [1600, FLOOR], playersize, player1, disp)
    player2.player = 1  # Set player number for key binding
player1.opponent = player2

# Game loop
running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_state == GAME_OVER:
                    current_state = MENU
                elif current_state == GAME:
                    current_state = MENU
                else:
                    running = False
            if event.key == pygame.K_SPACE and current_state == MENU:
                current_state = GAME
                player1.reset()
                player2.reset()
            if current_state == GAME_OVER and event.key != pygame.K_ESCAPE:
                current_state = GAME
                player1.reset()
                player2.reset()
        # Randomly pick a new song once the current one finishes
        if event.type == pygame.MIDIIN and music:
            try:
                pygame.mixer.music.load(random.choice(music))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                pygame.mixer.music.set_endevent(MIDIIN)
            except Exception as e:
                print(f"Warning: Could not play next song: {e}")

    if current_state == MENU:
        draw_menu()
    elif current_state == GAME:
        disp.blit(background, (0,0))
        player1.attack()
        player2.attack()
        player1.update()
        player2.update()
        player1.move()
        player2.move()
        draw_hpbar(disp, player1, player2)
        
        # Check for game over
        if player1.health <= 0 or player2.health <= 0:
            current_state = GAME_OVER
            winner = 2 if player1.health <= 0 else 1
    elif current_state == GAME_OVER:
        draw_game_over(winner)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()


