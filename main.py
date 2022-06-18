# Street Fighter Alpha 3 using Pygame
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

# Initialize pygame
pygame.init()
#disp = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
disp = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()

playersize = [144*5, 130*5]
#playersize = [144, 130] #  small

# Load all music into a list
music = []
for filename in os.listdir("./music"):
    if filename.endswith(".mp3"):
        music.append("./music/" + filename)

# Start up music
pygame.mixer.set_num_channels(2)
pygame.mixer.music.load(random.choice(music))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play()
pygame.mixer.music.set_endevent(MIDIIN)

# Game is designed for keyboard + controller. Without controller both characters will be mirrors of each other
try:
    controller = pygame.joystick.Joystick(0)

except:
    print("No joystick found")
    controller = None

player1 = Ryu(False, None, [0, FLOOR], playersize, None, disp)
#player2 = Ryu(True, controller, [500, FLOOR], playersize)
player2 = Ryu(True, controller, [1600, FLOOR], playersize, player1, disp)
player1.opponent = player2

# Load in background
running = True
background = pygame.transform.scale(pygame.image.load("./stage.png").convert_alpha(), (1920, 1080))
pygame.display.update()

# Game loop
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        # Randomly pick a new song once the current one finishes
        if event.type == pygame.MIDIIN:
            pygame.mixer.music.load(random.choice(music))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(MIDIIN)

    disp.blit(background, (0,0))
    # pygame.draw.rect(disp, (0,0,255), player1.rect)  # View player rectangles
    # pygame.draw.rect(disp, (0,0,255), player2.rect)
    player1.attack()
    player2.attack()
    player1.update()
    player2.update()
    player1.move()
    player2.move()

    draw_hpbar(disp, player1, player2)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


