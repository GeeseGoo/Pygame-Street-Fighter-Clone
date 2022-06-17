import pygame
from anims import *
from itertools import cycle, chain
from pygame.locals import *

UP = K_COMMA
DOWN = [K_o, 2]
LEFT = K_a
RIGHT = K_e

SPEED = 7
AIR_SPEED = 12
GRAVITY = 2
XGRAVITY = 3
SCREEN_WIDTH = 1920
FLOOR = 980
JUMP_STR = -40
ATTACK_CD = 100

lpunch_con = 2
lpunch_kbd = K_g

TOTAL_HEALTH = 400

DEFAULT_INPUTS = [
        [False, False, False, False],  # Up, down, left, right
        [False, False, False,  False, False, False]# Low punch, med punch, high punch, low kick, med kick, high kick
    ]
def draw_hpbar(disp, player1, player2):
    pygame.draw.rect(disp, (255, 0, 0), pygame.Rect(0,0, player1.health / TOTAL_HEALTH * 500, 70))
    player2bar = player2.health / TOTAL_HEALTH * 500
    pygame.draw.rect(disp, (255, 0, 0), pygame.Rect(1920 - player2bar,0, player2bar, 70))
# Delay specifies how many frames to delay between each new frame
def add_delay(frames, delay):
    # Creates a list with the right number of delays + the number of frames. Then slots the frames in between the delays
    result = [None for i in range(delay*len(frames) + len(frames))]
    result[::delay + 1] = frames
    return iter(result)


def parse_spritesheet(spritesheet, cellsize, columns, rows, scale):
    frames = []
    for y in range(rows):
        for x in range(columns):
            location = (x * cellsize[0], y * cellsize[1])
            sprite = pygame.transform.scale(spritesheet.subsurface(pygame.Rect(location, cellsize)), scale)
            trimmed_sprite = pygame.Surface(sprite.get_bounding_rect().size, pygame.SRCALPHA)
            trimmed_sprite.blit(sprite, (0,0))
            frames.append(trimmed_sprite)
    return frames


class Character(pygame.sprite.Sprite):
    def __init__(self, flip, controller, size, opponent):  # Controls = [movement, attack]
        self.size = size
        self.flip = flip
        self.controller = controller
        self.vel_y = 0
        self.vel_x = 0
        self.opponent = opponent
        self.key_presses = None
        self.held_keys = None
        self.input_buffer = [None]
        self.frame_queue = None
        self.current_frame = None
        self.current_frame_index = None
        self.action = None  # [function, name, blit, extra, bounding_rect , input]
        self.last_attack = pygame.time.get_ticks()

        self.health = TOTAL_HEALTH
        self.ishit = False


    def queue_add_frames(self, frames, force=False):
        if not self.frame_queue or force:
            self.frame_queue = frames


    def keyboard_input(self, held=True):
        keyboard = [
            [K_COMMA, K_o, K_a, K_e],  # [K_w, K_s, K_a, K_d] # Up, down, left, right
            [K_g, K_c, K_r,      K_h, K_t, K_n]  # Low punch, med punch, high punch, low kick, med kick, high kick
        ]
        keys = pygame.key.get_pressed()
        inputs = [[keys[j] for j in i]for i in keyboard]
        if not held:
            if self.input_buffer[-1] == inputs:
                return DEFAULT_INPUTS
        self.input_buffer.append(inputs)
        return inputs


    def controller_input(self, held=True):
        TOLERANCE = 0.5
        controls = [
            [False, False, False, False],  # Up, down, left, right
            [False, False, False,      False, False, False]  # Low punch, med punch, high punch, low kick, med kick, high kick
        ]
        # MOVEMENT
        if self.controller.get_axis(1) < -TOLERANCE:
            controls[0][0] = True
        if self.controller.get_axis(1) > TOLERANCE:
            controls[0][1] = True
        if self.controller.get_axis(0) < -TOLERANCE:
            controls[0][2] = True
        if self.controller.get_axis(0) > TOLERANCE:
            controls[0][3] = True

        # ATTACK
        controls[1][0] = self.controller.get_button(2)
        controls[1][1] = self.controller.get_button(3)
        controls[1][2] = self.controller.get_button(4)
        controls[1][3] = self.controller.get_button(0)
        controls[1][4] = self.controller.get_button(1)
        controls[1][5] = self.controller.get_button(5)


        if not held:
            if self.input_buffer[-1] == controls:
                return DEFAULT_INPUTS
        self.input_buffer.append(controls)
        return controls

    def get_input(self, held=True):
        if self.controller:
            return self.controller_input(held)
        else:
            return self.keyboard_input(held)

    def move(self, *, jump_side_frames, jump_frames, walk_right_frames, walk_left_frames, crouching_frames, crouch_up_frames):
        dx = 0
        dy = 0
        def jumping():
            if self.rect.bottom >= FLOOR:
                self.rect.bottom = FLOOR
                self.finish_action()

        def walk_right():
            held_keys = self.get_input()
            keys = self.get_input(held=False)
            if not held_keys[0][3] or any(any(i) for i in keys):
                self.finish_action()

        def walk_left():
            held_keys = self.get_input()
            keys = self.get_input(held=False)
            print(keys)
            if not held_keys[0][2] or any(any(i) for i in keys):
                print('OMOGOG')
                self.finish_action()

        def crouching():
            held_keys = self.get_input()
            keys = self.get_input(held=False)
            if not held_keys[0][1] or any(any(i) for i in keys):
                self.finish_action()

                def crouch_up():
                    self.finish_action()
                self.action = [crouch_up, "crouch_up", "bot", None,None, None]
                self.queue_add_frames(crouch_up_frames)  # Might break something

        if not self.action or self.action[1] == "walk_left" or self.action[1] == "walk_right":
            self.vel_x -= XGRAVITY
            if not self.ishit or self.vel_x < 0:
                self.vel_x = 0
            sideways = None

            keys = self.get_input(held=False)
            held_keys = self.get_input()


            # Python arguments are immutable references, making new variables so they can be changed
            walk_left_frames_ = walk_left_frames
            walk_right_frames_ = walk_right_frames
            jump_side_frames_ = jump_side_frames
            if self.flip:  # swap walk animations
                walk_left_frames_, walk_right_frames_ = walk_right_frames_, walk_left_frames_
                jump_side_frames_ = reversed(list(jump_side_frames_))

            if keys[0][1]:  # Crouch
                dx = 0
                self.action = [crouching, "crouching", "bot", None, None, None]
                self.queue_add_frames(crouching_frames)



            elif held_keys[0][2]:  # Left
                dx = -SPEED
                self.action = [walk_left, "walk_left", "center", None, None, None]
                self.queue_add_frames(walk_left_frames_)
                if held_keys[0][0]:  # Sideways jump has different animation
                    self.vel_x = -AIR_SPEED
                    sideways = "left"
                    self.queue_add_frames(reversed(list(jump_side_frames_)), force=True)

            elif held_keys[0][3]:  # Right
                dx = SPEED
                self.action = [walk_right, "walk_right", "center", None,None, None]
                self.queue_add_frames(walk_right_frames_)
                if held_keys[0][0]:
                    self.vel_x = AIR_SPEED
                    sideways = "right"
                    self.queue_add_frames(jump_side_frames_, force=True)

            if held_keys[0][2] and held_keys[0][3]:
                self.action = None
                self.frame_queue = None
                dx = 0

            elif held_keys[0][0]:  # Jump
                self.vel_y = JUMP_STR
                self.action = [jumping, "jumping", "top", sideways,None, None]
                self.queue_add_frames(jump_frames)

        dx += self.vel_x
        self.vel_y += GRAVITY
        dy += self.vel_y


        # Player can't go inside of another player
        jumping = False
        if self.action:
            if self.action[1] != 'jumping':
                jumping = True
        if self.rect.colliderect(self.opponent.rect) and not jumping:
            if self.flip:
                dx = 4
            else:
                dx = -4

        # Make sure player stays on screen
        if self.rect.left + dx < 0:
            #dx = -self.rect.left
            dx = 10
        if self.rect.right + dx > SCREEN_WIDTH:
            # dx = SCREEN_WIDTH - self.rect.right
            dx = -10
        if self.rect.bottom + dy > FLOOR:
            self.rect.bottom = FLOOR
            self.vel_y = 0
            dy = 0


        self.rect.x += dx
        self.rect.y += dy

    def attack(self, *, lpunch_hbox, lpunch_kb, lpunch_st, lpunch_frames, lpunch_rect, lpunch_index, lpunch_dmg, mpunch_hbox, mpunch_kb, mpunch_st, mpunch_frames, mpunch_rect, mpunch_index, mpunch_dmg,
               hpunch_hbox, hpunch_kb, hpunch_st, hpunch_frames, hpunch_rect, hpunch_index, hpunch_dmg, lkick_hbox, lkick_kb, lkick_st, lkick_frames, lkick_rect, lkick_index, lkick_dmg,
               mkick_hbox, mkick_kb, mkick_st, mkick_frames, mkick_rect, mkick_index, mkick_dmg, hkick_hbox, hkick_kb, hkick_st, hkick_frames, hkick_rect, hkick_index, hkick_dmg,hit_frame_final_index):
        # Flip if on opposite sides
        if not self.controller:  # check if player 1
            if self.rect.centerx > self.opponent.rect.centerx:
                self.flip = True
                self.opponent.flip = False
            else:
                self.flip = False
                self.opponent.flip = True



        # TODO figure out how to delete hit box without blitting weird
        if not self.action or 'walk' in self.action[1] or 'crouch' in self.action[1]:  # Can only attack when idle, crouching, or walking
            keys = self.get_input(held=False)
            blit = "bot"
            action = False
            if self.flip:
                blit = "right"
            if keys[1][0]:
                self.frame_queue = lpunch_frames
                hbox_ = lpunch_hbox
                knockback_ = lpunch_kb
                dmg_ = lpunch_dmg
                rect = lpunch_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = lpunch_st
                end_attack_ = lpunch_index
                action = True
            elif keys[1][1]:
                self.frame_queue = mpunch_frames
                hbox_ = mpunch_hbox
                knockback_ = mpunch_kb
                dmg_ = mpunch_dmg
                rect = mpunch_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = mpunch_st
                end_attack_ = mpunch_index
                action = True
            elif keys[1][2]:
                self.frame_queue = hpunch_frames
                hbox_ = hpunch_hbox
                knockback_ = hpunch_kb
                dmg_ = hpunch_dmg
                rect = hpunch_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = hpunch_st
                end_attack_ = hpunch_index
                action = True
            elif keys[1][3]:
                self.frame_queue = lkick_frames
                hbox_ = lkick_hbox
                knockback_ = lkick_kb
                dmg_ = lkick_dmg
                rect = lkick_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = lkick_st
                end_attack_ = lkick_index
                action = True
            elif keys[1][4]:
                self.frame_queue = mkick_frames
                hbox_ = mkick_hbox
                knockback_ = mkick_kb
                dmg_ = mkick_dmg
                rect = mkick_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = mkick_st
                end_attack_ = mkick_index
                action = True
            elif keys[1][5]:
                self.frame_queue = hkick_frames
                hbox_ = hkick_hbox
                knockback_ = hkick_kb
                dmg_ = hkick_dmg
                rect = hkick_rect
                end_frame_ = hit_frame_final_index
                stuntime_ = hkick_st
                end_attack_ = hkick_index
                action = True

            def basic_attack():
                print('amogus')
                hbox = hbox_
                knockback = knockback_
                dmg = dmg_
                stuntime = stuntime_
                end_frame = end_frame_
                end_attack = end_attack_
                spawn_rect = self.rect.topright
                if self.flip:
                    spawn_rect = [self.rect.topleft[0] - hbox[0], self.rect.topleft[1]]
                    knockback *= -1

                if self.current_frame_index == end_attack:
                    punch = pygame.Rect(spawn_rect, hbox)
                    #pygame.draw.rect(disp, (255,0,0), punch)
                    if punch.colliderect(self.opponent.rect):
                        self.action[0] = lambda: None
                        self.opponent.hit(dmg, stuntime, knockback, end_frame)

            if action:
                self.action = [basic_attack, "basic_attack", blit, None, rect, None]


    def hit(self, dmg, stuntime, knockback, hit_frame_final_index):
        def stophit():
            if self.current_frame_index == hit_frame_final_index:
                self.ishit = False
                self.finish_action()
        def blockhit():
            if self.current_frame_index == hit_frame_final_index:
                self.finish_action()

        self.vel_x += knockback
        held_keys = self.get_input()
        move_away = held_keys[0][2]
        if self.flip:
            move_away = held_keys[0][3]
        if move_away:  # Block the attack
            self.ishit = False
            self.action = [blockhit, 'block', 'bot', None, None, None]
            self.queue_add_frames(add_delay(self.block_frames, 4), force=True)
            return

        self.health -= dmg
        if self.health < 0: # TODO die
            while True:
                pass
        self.finish_action()
        self.action = [stophit, 'hit', 'bot', None,None, None]
        self.queue_add_frames((add_delay(self.hit_frames, stuntime)), force=True)
        self.ishit = True

    def update(self, disp):
        # Flush input buffer
        if len(self.input_buffer) > 20:
            self.input_buffer = self.input_buffer[:10]
        if not self.frame_queue:
            frame = next(self.idle)
        else:
            try:
                frame = next(self.frame_queue)
            except StopIteration:
                frame = next(self.idle)
                self.finish_action()

        blit_from_top = False
        blit_from_center = False
        blit_from_right = False
        custom_rect = False
        offset = False
        if self.action:
            if self.action[2] == "top":
                blit_from_top = True
            elif self.action[2] == "center":
                blit_from_center = True
            elif self.action[2] == "right":
                blit_from_right = True
            # if isinstance(self.action[3], int):  # Horizontal offset
            #     offset = True
            if self.action[4]:
                custom_rect = self.action[4].get_bounding_rect()
            # if self.action[5]:
            #     self.action[0](self.action[5]())
            self.action[0]()

        if frame:
            x = self.rect.x
            y = self.rect.y
            bot = self.rect.bottom
            center = self.rect.center
            right = self.rect.right
            self.rect = frame.get_bounding_rect()
            if custom_rect:
                self.rect = custom_rect
            self.rect.y = y
            self.rect.x = x
            if blit_from_center:
                self.rect.center = center
            elif blit_from_right:
                self.rect.right = right
            elif not blit_from_top:
                # Blit from bottom
                self.rect.bottom = bot

            # if offset:
            #     blitcoord = list(frame.get_size())
            #     blitcoord[0] = self.rect.bottomright[0] - blitcoord[0]
            #     blitcoord[1] = self.rect.y

            self.current_frame_index = self.frames.index(frame)
            if self.flip:  # Flip image and right align surface
                frame = pygame.transform.flip(frame, True, False)
                blitcoordinate = [self.rect.bottomright[0] - frame.get_size()[0], self.rect.bottomright[1] - frame.get_size()[1]]
                disp.blit(frame, blitcoordinate)
            else:
                disp.blit(frame, self.rect)
            self.current_frame = frame
        else:
            if self.flip:
                blitcoordinate = [self.rect.bottomright[0] - self.current_frame.get_size()[0], self.rect.bottomright[1] - self.current_frame.get_size()[1]]
                disp.blit(self.current_frame, blitcoordinate)
            else:
                disp.blit(self.current_frame, self.rect)


    def finish_action(self):
        self.action = None
        self.frame_queue = []


class Ryu(Character):
    def __init__(self, flip, controller, coord, size, opponent):
        super().__init__(flip, controller,  size, opponent)
        spritesheet = pygame.image.load("./ryu_spritesheet.png").convert_alpha()
        self.frames = parse_spritesheet(spritesheet, [144, 130], 14, 15, size)
        self.rect = self.frames[27].get_bounding_rect()
        self.rect.bottomleft = coord
        self.idle = cycle(add_delay(self.frames[10:14], 10))
        self.hit_frames = self.frames[138:141]
        self.block_frames = self.frames[44:46]

    def move(self):
        super().move(jump_side_frames=eval(RYU_JUMP_SIDE), jump_frames=eval(RYU_JUMP_STRAIGHT), walk_right_frames=cycle(add_delay(self.frames[15:20], 5)),
                     walk_left_frames=cycle(add_delay(self.frames[21:27], 5)), crouching_frames=chain(iter((self.frames[34], None, self.frames[35])), cycle((None,))),
                     crouch_up_frames=iter((self.frames[34],None)))

    def attack(self, disp):
        super().attack(lpunch_hbox=RYU_LPUNCH_HBOX, lpunch_kb=RYU_LPUNCH_KB, lpunch_st=RYU_LPUNCH_ST, lpunch_frames=eval(RYU_LPUNCH),
                       lpunch_rect=self.frames[12], lpunch_index=47, lpunch_dmg=RYU_LPUNCH_DMG, hit_frame_final_index=140, mpunch_hbox=RYU_MPUNCH_HBOX, mpunch_kb=RYU_MPUNCH_KB, mpunch_st=RYU_MPUNCH_ST,
                       mpunch_frames=eval(RYU_MPUNCH), mpunch_rect=self.frames[12], mpunch_index=50, mpunch_dmg=RYU_MPUNCH_DMG, hpunch_hbox=RYU_HPUNCH_HBOX, hpunch_kb=RYU_HPUNCH_KB, hpunch_st=RYU_HPUNCH_KB,
                       hpunch_frames=eval(RYU_HPUNCH), hpunch_rect=self.frames[12], hpunch_index=52, hpunch_dmg=RYU_HPUNCH_DMG, lkick_hbox=RYU_LKICK_HBOX, lkick_kb=RYU_LKICK_KB, lkick_st=RYU_LKICK_ST,
                       lkick_frames=eval(RYU_LKICK), lkick_rect=self.frames[12], lkick_index=58,mkick_hbox=RYU_MKICK_HBOX, mkick_kb=RYU_MKICK_KB, mkick_st=RYU_MKICK_ST, mkick_frames=eval(RYU_MKICK),
                       mkick_rect=self.frames[12], mkick_index=63, mkick_dmg=RYU_MKICK_DMG, lkick_dmg=RYU_LKICK_DMG, hkick_hbox=RYU_HKICK_HBOX, hkick_kb=RYU_HKICK_KB, hkick_st=RYU_HKICK_ST, hkick_frames=eval(RYU_HKICK),
                       hkick_rect=self.frames[12], hkick_index=66, hkick_dmg=RYU_HKICK_DMG)



# class ChunLi(Character):
#     def __init__(self, flip, player, coord, size):
#         super().__init__(flip, player, size)
#         spritesheet = pygame.image.load("./chunli_spritesheet.png").convert_alpha()
#         self.frames = parse_spritesheet(spritesheet, [90, 138], 21, 10, [90*6, 138*6])
#         self.rect = self.frames[0].get_bounding_rect()
#         self.idle = cycle(add_delay(self.frames[:4], 9))
#     def move(self, keys):
#         super().move(keys)
