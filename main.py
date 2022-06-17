# Import the pygame module
import pygame
from pygame.locals import *
from lib import *
from time import sleep
from anims import *

# Initialize pygame
pygame.init()
#disp = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
disp = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()

playersize = [144*5, 130*5]
#playersize = [144, 130] # ANT MODE

keyboard_binds = [
    [K_COMMA, K_o, K_a, K_e],  # [K_w, K_s, K_a, K_d] # Up, down, left, right
    [K_g, K_c, K_r,      K_h, K_t, K_n]  # Low punch, med punch, high punch, low kick, med kick, high kick
]
controller_binds = [
    [LSTICK_UP, LSTICK_DOWN, LSTICK_LEFT, LSTICK_DOWN],  # Up, down, left, right
    [2, 3, False, False, False]  # Low punch, med punch, high punch, low kick, med kick, high kick
]

TOLERANCE = 0.4

pygame.mixer.init()
pygame.mixer.music.load("./music/Alex & Ken's Stage - Jazzy NYC '99 (Arranged).mp3")
pygame.mixer.music.play(loops=-1)
try:
    controller = pygame.joystick.Joystick(0)

except:
    print("No joystick found")
    controller = None
player1 = Ryu(False, None, [0, FLOOR], playersize, None)
#player2 = Ryu(True, controller, [500, FLOOR], playersize)
player2 = Ryu(True, controller, [1500, FLOOR], playersize, player1)
player1.opponent = player2
running = True
background = pygame.transform.scale(pygame.image.load("./stage.png").convert_alpha(), (1920, 1080))

pygame.display.update()

while running:
    KEYS_DOWN = []
    events = pygame.event.get()
    controller_down = []

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    disp.blit(background, (0,0))

    player1.attack( disp)
    player2.attack( disp)
    player1.update(disp)
    player2.update(disp)

    player1.move()
    player2.move()

    draw_hpbar(disp, player1, player2)



    # print(f"{player.rect.left} {player.rect.top}")
    # print(clock.get_fps())

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


