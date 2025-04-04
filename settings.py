from pygame.mixer import Sound, init
from pygame.locals import *
import os

init()

# Controls for keyboard (Player 1)
keyboard_binds = [
            [K_w, K_s, K_a, K_d],  # Up, down, left, right
            [K_u, K_i, K_o, K_j, K_k, K_l]  # Low punch, med punch, high punch, low kick, med kick, high kick
]

# Controls for keyboard (Player 2)
keyboard_binds_p2 = [
            [K_UP, K_DOWN, K_LEFT, K_RIGHT],  # Up, down, left, right
            [K_1, K_2, K_3, K_4, K_5, K_6]  # Low punch, med punch, high punch, low kick, med kick, high kick
]

# Mapping the controls allows the program to easily know which inputs are being activated
keyboard_map = {
            keyboard_binds[0][0]: 'up', keyboard_binds[0][1]: 'down', keyboard_binds[0][2]: 'left', keyboard_binds[0][3]: 'right',
            keyboard_binds[1][0]: 'lpunch', keyboard_binds[1][1]: 'mpunch', keyboard_binds[1][2]: 'hpunch', keyboard_binds[1][3]: 'lkick',
            keyboard_binds[1][4]: 'mkick', keyboard_binds[1][5]: 'hkick'
}

keyboard_map_p2 = {
            keyboard_binds_p2[0][0]: 'up', keyboard_binds_p2[0][1]: 'down', keyboard_binds_p2[0][2]: 'left', keyboard_binds_p2[0][3]: 'right',
            keyboard_binds_p2[1][0]: 'lpunch', keyboard_binds_p2[1][1]: 'mpunch', keyboard_binds_p2[1][2]: 'hpunch', keyboard_binds_p2[1][3]: 'lkick',
            keyboard_binds_p2[1][4]: 'mkick', keyboard_binds_p2[1][5]: 'hkick'
}

# Controller controls, joystick controls are handled separately
controller_binds = [2, 3, 5, 0, 1, 4]  # Low punch, med punch, high punch, low kick, med kick, high kick
controller_map = {
                controller_binds[0]: 'lpunch', controller_binds[1]: 'mpunch', controller_binds[2]: 'hpunch',
                controller_binds[3]: 'lkick', controller_binds[4]: 'mkick', controller_binds[5]: 'hkick'
}

# Game constants
SPEED = 7
AIR_SPEED = 12
GRAVITY = 2
XGRAVITY = 3
SCREEN_WIDTH = 1920
FLOOR = 980
JUMP_STR = -50
ATTACK_CD = 100
TOTAL_HEALTH = 50
TOLERANCE = 0.5  # Joystick tolerance

# Template values for inputs
DEFAULT_INPUTS = [
        [False, False, False, False],  # Up, down, left, right
        [False, False, False,  False, False, False]  # Low punch, med punch, high punch, low kick, med kick, high kick
    ]

# Animations
RYU_JUMP_STRAIGHT = "iter((self.frames[27], None, None, None, None, None, self.frames[28],None, None, None, None, None, self.frames[29], None, None, None,  self.frames[30], None, None, None, None, None, self.frames[31], None, None, None, None, None, None, None,self.frames[32], None, None, None, None, None, None, None, self.frames[33], None, None, self.frames[27], None, None, None, None, None, None, None, None, None))"
RYU_JUMP_SIDE = "iter((self.frames[36], None, None, None, None,None, None, None, self.frames[37], None, None,None, None, None, self.frames[38],None, None, None, None, self.frames[39],None, None, self.frames[40],None, None,None,None,None, None, None, self.frames[41],None, None, None, self.frames[42],None, None,None, None,  self.frames[43], None, None,self.frames[27],None, None,None,None,None,None,None, None))"

RYU_LPUNCH = "iter((None, None, self.frames[46], self.frames[47], None, None, None, self.frames[46], None, None, None, None, None, None))"
RYU_MPUNCH = "iter((self.frames[48], None, None, None,self.frames[49], self.frames[50], None, None, None, None,None,None, self.frames[49], None, None, None, None, None, None, None, None, None, None, None, None," \
             " self.frames[48], None, None, None, None, None, None, None))"
RYU_HPUNCH = "iter((self.frames[51], None, None,None, None, None, self.frames[52], None, None,None, None, None, None, None, None, None,  None,None, None, None,None, None, None, None, None, self.frames[51], None, None, None, None, None, " \
             "None))"
RYU_LKICK = "iter((self.frames[60], None, self.frames[56],None,  self.frames[57], None, None,  self.frames[58], None, None, None, None, None, None, self.frames[59], None, None, None, None, None, None, None, None, None))"
RYU_MKICK = "iter((self.frames[61], None, None, self.frames[62], None, None, self.frames[63], None, None, None, None, None, None, None, None, self.frames[62], None, None, None, None, None, None, " \
            "None, self.frames[61], None, None, None, None, None ))"
RYU_HKICK = "iter((self.frames[64], None, None, None, None, self.frames[65], None, None, None,None, None, None, None, self.frames[66], None, None, None, None, None, self.frames[67], None, None, None, self.frames[68], " \
            "None, None, None, None, None, None, None, self.frames[69], None, None, None, None, None, None))"

RYU_CROUCH_PUNCH = "iter((self.frames[78], None, None, self.frames[79], None, None, None, None, self.frames[80], None, None, None, self.frames[79], None, None, None, None, None,self.frames[78], None, None, None, None, None, None))"
RYU_CROUCH_KICK = "iter((self.frames[81], None, None, None, None, self.frames[82], None, None, None, None, None,  self.frames[83], None, None, None, None, None, None, self.frames[84], None, None,None, None, None, self.frames[85], " \
                  "None, None, None, None, None, self.frames[86], None, None, None, None, None))"

RYU_AIR_KICK = "iter((None, None, self.frames[70], None, None, None, None, None, None,None, None,  self.frames[71], None, None, None, self.frames[72], None, None, None, None, None, None))"
RYU_AIR_PUNCH = "iter((None, None, self.frames[75], None, None, None, self.frames[76], None, None, None, None, self.frames[77], None, None, None, None, None, None, None, None, None, None,))"

# Hitboxes
RYU_LPUNCH_HBOX = [180, 100]
RYU_MPUNCH_HBOX = [195, 100]
RYU_HPUNCH_HBOX = [210, 100]
RYU_LKICK_HBOX = [200, 400]
RYU_MKICK_HBOX = [230, 100]
RYU_HKICK_HBOX = [250, 100]

RYU_CROUCH_PUNCH_HBOX = [180, 100]
RYU_CROUCH_KICK_HBOX = [300, 100]

RYU_AIR_PUNCH_HBOX = [150, 300]
RYU_AIR_KICK_HBOX = [300, 300]

# Knockback
RYU_LPUNCH_KB = 1
RYU_MPUNCH_KB = 3
RYU_HPUNCH_KB = 6
RYU_LKICK_KB = 2
RYU_MKICK_KB = 4
RYU_HKICK_KB = 6

RYU_CROUCH_PUNCH_KB = 1
RYU_CROUCH_KICK_KB = 3

RYU_AIR_PUNCH_KB = 5
RYU_AIR_KICK_KB = 12

RYU_HADOUKEN_KB = 2

# Stun times
RYU_LPUNCH_ST = 2
RYU_MPUNCH_ST = 8
RYU_HPUNCH_ST = 16
RYU_LKICK_ST = 4
RYU_MKICK_ST = 10
RYU_HKICK_ST = 14

RYU_CROUCH_PUNCH_ST = 3
RYU_CROUCH_KICK_ST = 6

RYU_AIR_PUNCH_ST = 8
RYU_AIR_KICK_ST = 18

RYU_HADOUKEN_ST = 5

# Damage
RYU_LPUNCH_DMG = 6
RYU_MPUNCH_DMG = 14
RYU_HPUNCH_DMG = 17
RYU_LKICK_DMG = 7
RYU_MKICK_DMG = 13
RYU_HKICK_DMG = 16

RYU_CROUCH_PUNCH_DMG = 4
RYU_CROUCH_KICK_DMG = 8

RYU_AIR_PUNCH_DMG = 9
RYU_AIR_KICK_DMG = 16

RYU_HADOUKEN_DMG = 3

RYU_HADOUKEN_SPEED = 15
RYU_HADOUKEN_LEEWAY = 200  # How fast the inputs must be for multi step actions

# SFX
def load_sound(path):
    try:
        return Sound(path)
    except:
        print(f"Warning: Could not load sound file {path}")
        return None

# Create SFX directory if it doesn't exist
if not os.path.exists("./SFX"):
    os.makedirs("./SFX")
if not os.path.exists("./SFX/Ryu"):
    os.makedirs("./SFX/Ryu")

RYU_DEATH_SFX = load_sound("./SFX/Ryu/death.wav")
RYU_HURT_SFX = load_sound("./SFX/Ryu/hurt.wav")
RYU_JUMP_SFX = load_sound("./SFX/Ryu/jump.wav")
RYU_HEAVY_SFX = load_sound("./SFX/Ryu/heavy.wav")
RYU_MEDIUM_SFX = load_sound("./SFX/Ryu/medium.wav")
RYU_LIGHT_SFX = load_sound("./SFX/Ryu/light.wav")
RYU_HADOUKEN_SFX = load_sound("./SFX/Ryu/hadouken.mp3")



