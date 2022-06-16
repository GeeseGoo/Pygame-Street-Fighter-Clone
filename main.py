# Import the pygame module
import pygame
from pygame.locals import *
from lib import *
from time import sleep

# Initialize pygame
pygame.init()
#disp = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
disp = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()

playersize = [144*5, 130*5]
#playersize = [144, 130] # ANT MODE

keyboard = [
    [K_COMMA, K_o, K_a, K_e],  # [K_w, K_s, K_a, K_d] # Up, down, left, right
    [K_g, K_c, K_r,      K_h, K_t, K_n]  # Low punch, med punch, high punch, low kick, med kick, high kick
]

pygame.mixer.init()
pygame.mixer.music.load("1 2 oatmeal.mp3")
pygame.mixer.music.play(-1)
try:
    controller = pygame.joystick.Joystick(0)

except:
    print("No joystick found")
player1 = Ryu(False, None, [0, FLOOR], playersize)
#player2 = Ryu(True, controller, [500, FLOOR], playersize)
player2 = Ryu(True, None, [1500, FLOOR], playersize)
running = True
background = pygame.transform.scale(pygame.image.load("./stage.png").convert_alpha(), (1920, 1080))

pygame.display.update()

def kbd_input( player, prev_input):
    inputs = [[True if i == j.key else False for i in k for j in pygame.event.get() if j.type == pygame.KEYDOWN] for k in keyboard]
    print(inputs)
    print([[True for k in pygame.event.get() if k.type == pygame.KEYDOWN for j in i if j == k.key] for i in keyboard])


    # def con_input(self):
    #     TOLERANCE = 0.5
    #     controls = [
    #     [False, False, False, False],  # Up, down, left, right
    #     [False, False, False,      False, False, False]  # Low punch, med punch, high punch, low kick, med kick, high kick
    # ]
    #     # MOVEMENT
    #     if self.controller.get_axis(1) < -TOLERANCE:
    #         controls[0][0] = True
    #     if self.controller.get_axis(1) > TOLERANCE:
    #         controls[0][1] = True
    #     if self.controller.get_axis(0) < -TOLERANCE:
    #         controls[0][2] = True
    #     if self.controller.get_axis(0) > TOLERANCE:
    #         controls[0][3] = True
    #
    #     # ATTACK
    #     controls[1][0] = self.controller.get_button(2)
    #
    #     return controls

input_buffer = []
prevjoystick = 0
while running:
    KEYS_DOWN = []
    controller_down = []
    kbd_input(player1, input_buffer)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            KEYS_DOWN.append(event.key)
        if event.type == JOYBUTTONDOWN:
            controller_down.append(event.button)
        if event.type == JOYAXISMOTION:
            motion = event.axis * round(event.value)
            if motion != prevjoystick:  # MIGHT BUG OUT
                print(motion)
                prevjoystick = motion
                controller_down.append(event)
        if event.type == pygame.QUIT:
            running = False
    player1.keys_down = KEYS_DOWN
    player2.keys_down = controller_down
    disp.blit(background, (0,0))
    #pygame.draw.rect(disp, (0,0,255), player1.rect)
    #pygame.draw.rect(disp, (0,0,255), player2.rect)
    player1.update(disp)
    player2.update(disp)
    player1.attack(player2, disp)
    player2.attack(player1, disp)
    player1.move()
    player2.move()




    # print(f"{player.rect.left} {player.rect.top}")
    # print(clock.get_fps())

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


