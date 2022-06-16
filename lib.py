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
    def __init__(self, flip, controller, size):  # Controls = [movement, attack]
        self.size = size
        self.flip = flip
        self.controller = controller
        self.vel_y = 0
        self.vel_x = 0
        self.keys_down = None
        self.frame_queue = None
        self.current_frame = None
        self.current_frame_index = None
        self.action = None  # [function, name, blit, extra, bounding_rect , input]
        self.last_attack = pygame.time.get_ticks()

        self.health = 100
        self.ishit = False


    def queue_add_frames(self, frames, force=False):
        if not self.frame_queue or force:
            self.frame_queue = frames


    def keyboard_input(self):
        keyboard = [
            [K_COMMA, K_o, K_a, K_e],  # [K_w, K_s, K_a, K_d] # Up, down, left, right
            [K_g, K_c, K_r,      K_h, K_t, K_n]  # Low punch, med punch, high punch, low kick, med kick, high kick
        ]
        keys = pygame.key.get_pressed()
        return [[keys[j] for j in i]for i in keyboard]


    def controller_input(self):
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

        return controls

    def get_held_input(self):
        if self.controller:
            return self.controller_input()
        else:
            return self.keyboard_input()

    def move(self, *, jump_side_frames, jump_frames, walk_right_frames, walk_left_frames, crouching_frames, crouch_up_frames):
        dx = 0
        dy = 0
        def jumping():
            if self.rect.bottom >= FLOOR:
                self.rect.bottom = FLOOR
                self.finish_action()

        def walk_right():
            keys = self.get_held_input()
            if not keys[0][3] or self.keys_down:
                self.finish_action()

        def walk_left():
            keys = self.get_held_input()
            if self.keys_down:
                pass
            if not keys[0][2] or self.keys_down:
                self.finish_action()

        def crouching():
            keys = self.get_held_input()
            if not keys[0][1] or self.keys_down:
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

            keys = self.get_held_input()

            if any(x for y in DOWN for x in self.keys_down if x == y):  # Crouch
                dx = 0
                self.action = [crouching, "crouching", "bot", None,None, None]
                self.queue_add_frames(crouching_frames)

            elif keys[0][2]:  # Left
                dx = -SPEED
                self.action = [walk_left, "walk_left", "center", None,None, None]
                self.queue_add_frames(walk_left_frames)
                if keys[0][0]:  # Sideways jump has different animation
                    self.vel_x = -AIR_SPEED
                    sideways = "left"
                    self.queue_add_frames(jump_side_frames, force=True)

            elif keys[0][3]:  # Right
                dx = SPEED
                self.action = [walk_right, "walk_right", "center", None,None, None]
                self.queue_add_frames(walk_right_frames)
                if keys[0][0]:
                    self.vel_x = AIR_SPEED
                    sideways = "right"
                    self.queue_add_frames(jump_side_frames, force=True)

            if keys[0][2] and keys[0][3]:
                self.action = None
                self.frame_queue = None
                dx = 0

            elif keys[0][0]:  # Jump
                self.vel_y = JUMP_STR
                self.action = [jumping, "jumping", "top", sideways,None, None]
                self.queue_add_frames(jump_frames)

        dx += self.vel_x
        self.vel_y += GRAVITY
        dy += self.vel_y


        # Make sure player stays on screen
        if self.rect.left + dx < 0:
            #dx = -self.rect.left
            dx = 1
        if self.rect.right + dx > SCREEN_WIDTH:
            # dx = SCREEN_WIDTH - self.rect.right
            dx = -1
        if self.rect.bottom + dy > FLOOR:
            self.rect.bottom = FLOOR
            self.vel_y = 0
            dy = 0

        self.rect.x += dx
        self.rect.y += dy

    def update(self, disp):
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
    def __init__(self, flip, controller, coord, size):
        super().__init__(flip, controller,  size)
        spritesheet = pygame.image.load("./ryu_spritesheet.png").convert_alpha()
        self.frames = parse_spritesheet(spritesheet, [144, 130], 14, 15, size)
        self.rect = self.frames[27].get_bounding_rect()
        self.rect.bottomleft = coord
        self.idle = cycle(add_delay(self.frames[10:14], 10))

    def move(self):
        super().move(jump_side_frames=eval(RYU_JUMP_SIDE), jump_frames=eval(RYU_JUMP_STRAIGHT), walk_right_frames=cycle(add_delay(self.frames[15:20], 5)),
                     walk_left_frames=cycle(add_delay(self.frames[15:20], 5)), crouching_frames=chain(iter((self.frames[34], None, self.frames[35])), cycle((None,))),
                     crouch_up_frames=iter((self.frames[34],None)))

    def attack(self, opponent, disp):

        # Flip if on opposite sides
        if not self.controller:  # check if player 1
            if self.rect.centerx > opponent.rect.centerx:
                self.flip = True
                opponent.flip = False
            else:
                self.flip = False
                opponent.flip = True

        def lpunch():
            spawn_rect = self.rect.topright
            hbox = RYU_LPUNCH_HBOX
            knockback = 10
            if self.flip:
                spawn_rect = [self.rect.topleft[0] - hbox[0], self.rect.topleft[1]]
                knockback *= -1

            if self.current_frame_index == 47:
                punch = pygame.Rect(spawn_rect, hbox)
                #pygame.draw.rect(disp, (255,0,0), punch)
                if punch.colliderect(opponent.rect):
                    self.action[0] = lambda: None
                    opponent.hit(5, 3, knockback)

        # TODO figure out how to delete hit box without blitting weird
        if not self.action or 'walk' in self.action[1] or 'crouch' in self.action[1]:  # Can only attack when idle, crouching, or walking
            #keys = self.get_held_input()
            blit = "bot"
            custom_rect = self.frames[12]
            offset = None
            if self.flip:
                blit = "right"
                offset = None
            if lpunch_con in self.keys_down or lpunch_kbd in self.keys_down:
                self.action = [lpunch, "lpunch", blit, offset, custom_rect, None]
                self.frame_queue = eval(RYU_LPUNCH)

    def hit(self, dmg, stuntime, knockback):
        def stophit():
            if self.current_frame == self.frames[140]:
                self.ishit = False
                self.finish_action()

        self.health -= dmg
        if self.health < 0: # TODO die
            print('DEAD')
            pygame.quit()
            quit()
        self.finish_action()
        self.action = [stophit, 'hit', 'bot', None,None, None]
        self.frame_queue = add_delay(self.frames[138:141], stuntime)
        self.vel_x += knockback
        self.ishit = True


# class ChunLi(Character):
#     def __init__(self, flip, player, coord, size):
#         super().__init__(flip, player, size)
#         spritesheet = pygame.image.load("./chunli_spritesheet.png").convert_alpha()
#         self.frames = parse_spritesheet(spritesheet, [90, 138], 21, 10, [90*6, 138*6])
#         self.rect = self.frames[0].get_bounding_rect()
#         self.idle = cycle(add_delay(self.frames[:4], 9))
#     def move(self, keys):
#         super().move(keys)
