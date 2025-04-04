import pygame
from settings import *
from itertools import cycle, chain
from pygame.locals import *


def draw_hpbar(disp, player1, player2):
    # Health bar dimensions
    bar_height = 15
    bar_width = 300
    bar_y = 50  # Lowered by 100px
    border_width = 2
    
    # Player 1 health bar - moved 400px from left edge
    p1_x = 250
    p1_health = max(0, player1.health / TOTAL_HEALTH * bar_width)
    
    # Player 2 health bar - moved 400px from right edge
    p2_x = disp.get_width() - bar_width - 250
    p2_health = max(0, player2.health / TOTAL_HEALTH * bar_width)
    
    # Draw health bar borders
    pygame.draw.rect(disp, (255, 255, 255), pygame.Rect(p1_x - border_width, bar_y - border_width, bar_width + border_width*2, bar_height + border_width*2))
    pygame.draw.rect(disp, (255, 255, 255), pygame.Rect(p2_x - border_width, bar_y - border_width, bar_width + border_width*2, bar_height + border_width*2))
    
    # Draw health bar backgrounds
    pygame.draw.rect(disp, (0, 0, 0), pygame.Rect(p1_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(disp, (0, 0, 0), pygame.Rect(p2_x, bar_y, bar_width, bar_height))
    
    # Draw health bars
    pygame.draw.rect(disp, (255, 0, 0), pygame.Rect(p1_x, bar_y, p1_health, bar_height))
    pygame.draw.rect(disp, (255, 0, 0), pygame.Rect(p2_x, bar_y, p2_health, bar_height))
    
    # Draw player names
    font = pygame.font.Font(None, 20)
    p1_name = font.render("P1", True, (255, 255, 255))
    p2_name = font.render("P2", True, (255, 255, 255))
    
    # Position names above health bars
    disp.blit(p1_name, (p1_x, bar_y - 20))
    disp.blit(p2_name, (p2_x, bar_y - 20))


# Delay specifies how many frames to delay between each new frame
def add_delay(frames, delay):
    # Creates a list with the right number of delays + the number of frames. Then slots the frames in between the delays
    result = [None for i in range(delay*len(frames) + len(frames))]
    result[::delay + 1] = frames
    return iter(result)


# Return sum of nested list
def nested_sum(array):
    return sum(sum(i) if isinstance(i, list) else i for i in array)


# Convert spritesheet to list of sprites
def parse_spritesheet(spritesheet, cellsize, columns, rows, scale):
    frames = []
    for y in range(rows):
        for x in range(columns):
            location = (x * cellsize[0], y * cellsize[1])
            sprite = pygame.transform.scale(spritesheet.subsurface(pygame.Rect(location, cellsize)), scale)
            # Must trim sprites to get rid of padding
            trimmed_sprite = pygame.Surface(sprite.get_bounding_rect().size, pygame.SRCALPHA)  # SRCALPHA makes background transparent
            trimmed_sprite.blit(sprite, (0,0))
            frames.append(trimmed_sprite)
    return frames

# In SF3, all characters have the same basic attacks, air attacks, crouch attacks, etc. Only the special moves differ. This class allows us create new characters
# much more easily, as only the animations are different between characters
class Character(pygame.sprite.Sprite):
    def __init__(self, flip, controller, size, opponent, disp):
        self.size = size
        self.flip = flip
        self.controller = controller
        self.vel_y = 0
        self.vel_x = 0
        self.opponent = opponent
        self.disp = disp

        self.input_buffer = [None]
        self.frame_queue = None
        self.current_frame = None
        self.current_frame_index = None
        self.action = None  # [function, name, blit, extra, bounding_rect, args]
        self.last_attack = pygame.time.get_ticks()

        self.health = TOTAL_HEALTH
        self.ishit = False

        self.player = 0
        if controller:
            self.player = 1
        self.channel = pygame.mixer.Channel(self.player)

    # Animations are stored in a queue that gets evaluated every game loop
    def queue_add_frames(self, frames, force=False):
        if not self.frame_queue or force:
            self.frame_queue = frames

    # Some actions do not want to be reactivated if the key is held down, so we can compare the current input to the previous input to see if any keys are held down
    def keyboard_input(self, held=True):
        keys = pygame.key.get_pressed()
        # Use different key bindings based on which player this is
        if self.player == 0:  # Player 1
            inputs = [[keys[j] for j in i]for i in keyboard_binds]
        else:  # Player 2
            inputs = [[keys[j] for j in i]for i in keyboard_binds_p2]
            
        if not held:
            if self.input_buffer[-1] == inputs:
                return DEFAULT_INPUTS
        self.input_buffer.append(inputs)
        return inputs

    def controller_input(self, held=True):
        # By default we assume that there is no input
        controls = DEFAULT_INPUTS
        # Movement
        # Axis 1 - left joystick, up/down
        # AXis 2 - left joystick, left/right
        if self.controller.get_axis(1) < -TOLERANCE:
            controls[0][0] = True
        if self.controller.get_axis(1) > TOLERANCE:
            controls[0][1] = True
        if self.controller.get_axis(0) < -TOLERANCE:
            controls[0][2] = True
        if self.controller.get_axis(0) > TOLERANCE:
            controls[0][3] = True

        # Attack
        for count, i in enumerate(controller_binds):
            controls[1][count] = self.controller.get_button(i)

        # Compare input to previous input to get rid of held buttons
        if not held:
            if self.input_buffer[-1] == controls:
                return DEFAULT_INPUTS
        self.input_buffer.append(controls)
        return controls

    # This function allows us to play the game without a controller, although the inputs will control both characters
    def get_input(self, held=True):
        if self.controller:
            return self.controller_input(held)
        else:
            return self.keyboard_input(held)

    def move(self, *, jump_side_frames, jump_frames, walk_right_frames, walk_left_frames, crouching_frames, crouch_up_frames, jump_sfx):
        dx = 0
        dy = 0

        # These functions will be called every game loop
        def jumping():
            # Jump ends when the character reaches the floor
            if self.rect.bottom >= FLOOR:
                self.rect.bottom = FLOOR
                self.finish_action()

        def walk_right():
            # Walking ends if cancelled with another key, or if input is ceased
            held_keys = self.get_input()
            keys = self.get_input(held=False)
            if not held_keys[0][3] or any(any(i) for i in keys):
                self.finish_action()

        def walk_left():
            # Walking ends if cancelled with another key, or if input is ceased
            held_keys = self.get_input()
            keys = self.get_input(held=False)
            if not held_keys[0][2] or any(any(i) for i in keys):
                self.finish_action()

        def crouching():
            # Crouching ends if cancelled with another key, or if input is ceased
            held_keys = self.get_input()
            if not held_keys[0][1] or any((held_keys[0][0], held_keys[0][2], held_keys[0][3])):
                self.finish_action()

                # A different animation is displayed once the player lets go of the crouch key
                def crouch_up():
                    self.finish_action()

                self.action = [crouch_up, "crouch_up", "bot", None, None, None]
                self.queue_add_frames(crouch_up_frames)

        # If not walking, players will decelerate
        if not self.action or self.action[1] == "walk_left" or self.action[1] == "walk_right":
            self.vel_x -= XGRAVITY
            # Make sure that players don't have negative speed
            if not self.ishit or self.vel_x < 0:
                self.vel_x = 0

            # Init variable for jumping sideways
            sideways = None

            keys = self.get_input(held=False)
            held_keys = self.get_input()


            # Python arguments are immutable references, making new variables so they can be changed
            walk_left_frames_ = walk_left_frames
            walk_right_frames_ = walk_right_frames
            jump_side_frames_ = jump_side_frames
            if self.flip:  # swap walk animations if players are flipped
                walk_left_frames_, walk_right_frames_ = walk_right_frames_, walk_left_frames_
                jump_side_frames_ = reversed(list(jump_side_frames_))


            if held_keys[0][2]:  # Left
                dx = -SPEED
                self.action = [walk_left, "walk_left", "center", None, None, None]
                self.queue_add_frames(walk_left_frames_)
                if held_keys[0][0] and self.rect.bottom == FLOOR:  # Sideways jump has different animation
                    self.vel_x = -AIR_SPEED
                    self.vel_y = JUMP_STR
                    self.channel.play(jump_sfx)
                    self.queue_add_frames(reversed(list(jump_side_frames_)), force=True)
                    self.action = [jumping, "jumping", "top", "left",None, None]

            elif held_keys[0][3]:  # Right
                dx = SPEED
                self.action = [walk_right, "walk_right", "center", None,None, None]
                self.queue_add_frames(walk_right_frames_)
                if held_keys[0][0] and self.rect.bottom == FLOOR:
                    self.vel_x = AIR_SPEED
                    self.vel_y = JUMP_STR
                    self.channel.play(jump_sfx)
                    self.queue_add_frames(jump_side_frames_, force=True)
                    self.action = [jumping, "jumping", "top", "right", None, None]

            elif held_keys[0][0] and self.rect.bottom == FLOOR:  # Jump
                self.vel_y = JUMP_STR
                self.action = [jumping, "jumping", "top", sideways,None, None]
                self.channel.play(jump_sfx)
                self.queue_add_frames(jump_frames)

            elif keys[0][1]:  # Crouch
                dx = 0
                self.action = [crouching, "crouching", "bot", None, None, None]
                self.queue_add_frames(crouching_frames)

            # If players hold down both left and right they will cancel each other out
            if held_keys[0][2] and held_keys[0][3]:
                self.action = None
                self.frame_queue = None
                dx = 0

        dx += self.vel_x
        self.vel_y += GRAVITY
        dy += self.vel_y

        # Player can't go inside of another player unless jumping
        jumping = False
        if self.action:
            if self.action[1] == 'jumping':
                jumping = True
        if self.rect.colliderect(self.opponent.rect) and not jumping:
            if self.flip:
                dx = 4
            else:
                dx = -4

        # Make sure player stays on screen
        if self.rect.left + dx < 0:
            dx = 10
        if self.rect.right + dx > SCREEN_WIDTH:
            dx = -10
        if self.rect.bottom + dy > FLOOR:
            self.rect.bottom = FLOOR
            self.vel_y = 0
            dy = 0

        # Move players
        self.rect.x += dx
        self.rect.y += dy

    def attack(self, keys, *, lpunch_hbox, lpunch_kb, lpunch_st, lpunch_frames, lpunch_rect, lpunch_index, lpunch_dmg, lpunch_sfx, mpunch_hbox, mpunch_kb, mpunch_st, mpunch_frames, mpunch_rect, mpunch_index, mpunch_dmg, mpunch_sfx,
               hpunch_hbox, hpunch_kb, hpunch_st, hpunch_frames, hpunch_rect, hpunch_index, hpunch_dmg, hpunch_sfx, lkick_hbox, lkick_kb, lkick_st, lkick_frames, lkick_rect, lkick_index, lkick_dmg, lkick_sfx,
               mkick_hbox, mkick_kb, mkick_st, mkick_frames, mkick_rect, mkick_index, mkick_dmg, mkick_sfx, hkick_hbox, hkick_kb, hkick_st, hkick_frames, hkick_rect, hkick_index, hkick_dmg, hkick_sfx,

               crouch_punch_hbox, crouch_punch_kb, crouch_punch_st, crouch_punch_frames, crouch_punch_rect, crouch_punch_index, crouch_punch_dmg, crouch_punch_sfx, crouch_kick_hbox, crouch_kick_kb,
               crouch_kick_st, crouch_kick_frames, crouch_kick_rect, crouch_kick_index, crouch_kick_dmg, crouch_kick_sfx,

               air_punch_hbox, air_punch_kb, air_punch_st, air_punch_frames, air_punch_rect, air_punch_index, air_punch_dmg, air_punch_sfx, air_kick_hbox, air_kick_kb,
               air_kick_st, air_kick_frames, air_kick_rect, air_kick_index, air_kick_dmg, air_kick_sfx,
               hit_frame_final_index):

        if not self.action or 'walk' in self.action[1] or 'crouch' in self.action[1] or 'jumping' in self.action[1]:  # Can only attack when idle, crouching, walking, or jumping
            blit = "bot"  # Make sure that the bottom of the players sprite doesn't move
            action = False
            if self.flip:
                # Make sure that the right of the sprite does not move. If this setting is removed the sprite's hand/foot will stay in place while the rest of their body moves back
                blit = "right"
            end_frame_ = hit_frame_final_index  # When to end the hit animation
            inaction = False
            air = False
            if self.action:
                inaction = True

            # Jumping attacks
            if self.rect.bottom < FLOOR:
                if keys[1][0] or keys[1][1] or keys[1][2]:  # Air punch
                    # Change the animation, hitbox, etc for this move
                    self.frame_queue = air_punch_frames
                    hbox_ = air_punch_hbox
                    knockback_ = air_punch_kb
                    dmg_ = air_punch_dmg
                    rect = air_punch_rect
                    stuntime_ = air_punch_st
                    end_attack_ = air_punch_index
                    self.channel.play(air_punch_sfx)
                    action = True
                    air = True
                elif keys[1][3] or keys[1][4] or keys[1][5]:  # Air kick
                    self.frame_queue = air_kick_frames
                    hbox_ = air_kick_hbox
                    knockback_ = air_kick_kb
                    dmg_ = air_kick_dmg
                    rect = air_kick_rect
                    stuntime_ = air_kick_st
                    end_attack_ = air_kick_index
                    self.channel.play(air_kick_sfx)
                    action = True
                    air = True

            # Crouching attacks
            elif inaction and self.action[1] == 'crouching':
                if keys[1][0] or keys[1][1] or keys [1][2]:
                    self.frame_queue = crouch_punch_frames
                    hbox_ = crouch_punch_hbox
                    knockback_ = crouch_punch_kb
                    dmg_ = crouch_punch_dmg
                    rect = crouch_punch_rect
                    stuntime_ = crouch_punch_st
                    end_attack_ = crouch_punch_index
                    self.channel.play(crouch_punch_sfx)
                    action = True
                elif keys[1][3] or keys[1][4] or keys[1][5]:
                    self.frame_queue = crouch_kick_frames
                    hbox_ = crouch_kick_hbox
                    knockback_ = crouch_kick_kb
                    dmg_ = crouch_kick_dmg
                    rect = crouch_kick_rect
                    stuntime_ = crouch_kick_st
                    end_attack_ = crouch_kick_index
                    self.channel.play(crouch_kick_sfx)
                    action = True

            # Standing attacks
            elif keys[1][0]:
                self.frame_queue = lpunch_frames
                hbox_ = lpunch_hbox
                knockback_ = lpunch_kb
                dmg_ = lpunch_dmg
                rect = lpunch_rect
                stuntime_ = lpunch_st
                end_attack_ = lpunch_index
                self.channel.play(lpunch_sfx)
                action = True
            elif keys[1][1]:
                self.frame_queue = mpunch_frames
                hbox_ = mpunch_hbox
                knockback_ = mpunch_kb
                dmg_ = mpunch_dmg
                rect = mpunch_rect
                stuntime_ = mpunch_st
                end_attack_ = mpunch_index
                self.channel.play(mpunch_sfx)
                action = True
            elif keys[1][2]:
                self.frame_queue = hpunch_frames
                hbox_ = hpunch_hbox
                knockback_ = hpunch_kb
                dmg_ = hpunch_dmg
                rect = hpunch_rect
                stuntime_ = hpunch_st
                end_attack_ = hpunch_index
                self.channel.play(hpunch_sfx)
                action = True
            elif keys[1][3]:
                self.frame_queue = lkick_frames
                hbox_ = lkick_hbox
                knockback_ = lkick_kb
                dmg_ = lkick_dmg
                rect = lkick_rect
                stuntime_ = lkick_st
                end_attack_ = lkick_index
                self.channel.play(lkick_sfx)
                action = True
            elif keys[1][4]:
                self.frame_queue = mkick_frames
                hbox_ = mkick_hbox
                knockback_ = mkick_kb
                dmg_ = mkick_dmg
                rect = mkick_rect
                stuntime_ = mkick_st
                end_attack_ = mkick_index
                self.channel.play(mkick_sfx)
                action = True
            elif keys[1][5]:
                self.frame_queue = hkick_frames
                hbox_ = hkick_hbox
                knockback_ = hkick_kb
                dmg_ = hkick_dmg
                rect = hkick_rect
                stuntime_ = hkick_st
                end_attack_ = hkick_index
                self.channel.play(hkick_sfx)
                action = True

            def basic_attack():
                hbox = hbox_
                knockback = knockback_
                dmg = dmg_
                stuntime = stuntime_
                end_frame = end_frame_
                end_attack = end_attack_
                spawn_rect = self.rect.topright
                # Cancel air attack if player touches the floor
                if air:
                    if self.rect.bottom >= FLOOR:
                        self.finish_action()

                # Players are knocked back when hit, this makes sure that the player doesn't get sucked in when hit
                if self.flip:
                    spawn_rect = [self.rect.topleft[0] - hbox[0], self.rect.topleft[1]]
                    knockback *= -1

                # Player can only do damage at a certain part of the attack animation
                if self.current_frame_index == end_attack:
                    punch = pygame.Rect(spawn_rect, hbox)
                    # pygame.draw.rect(self.disp, (255,0,0), punch)
                    if punch.colliderect(self.opponent.rect):   # Detect if attack hits opponent
                        if self.action:  # Sometimes self.action is none if attack is suddenly cancelled
                            self.action[0] = lambda: None
                        self.opponent.hit(dmg, stuntime, knockback, end_frame)  # Deal damage to opponent

            if action:  # If the player attacks
                self.action = [basic_attack, "basic_attack", blit, None, rect, None]

    def hit(self, dmg, stuntime, knockback, hit_frame_final_index):
        def stophit():
            # When to end the hit animation
            if self.current_frame_index == hit_frame_final_index:
                self.ishit = False
                self.finish_action()
        def blockhit():
            # When to end the block animation
            if self.current_frame_index == hit_frame_final_index:
                self.finish_action()

        self.vel_x += knockback
        held_keys = self.get_input()

        # Players can block attacks if they move away from the attacker
        move_away = held_keys[0][2]
        if self.flip:
            move_away = held_keys[0][3]

        blockable_action = False   # Players can only block while jumping, walking, standing, or crouching
        if self.action:
            if self.action[1] == 'jumping' or self.action[1] == 'walk_left' or self.action[1] == 'walk_right' or self.action[1] == 'crouching':
                blockable_action = True
        # Block the attack
        if move_away and blockable_action or move_away and not self.action:
            self.ishit = False
            self.action = [blockhit, 'block', 'bot', None, None, None]
            self.queue_add_frames(chain(add_delay(self.block_frames, 4), iter([None for i in range(stuntime)])), force=True)
            return

        # If player doesn't block the attack
        self.health -= dmg
        # Set health to 0 if it goes below 0
        if self.health < 0:
            self.health = 0

        # Play hit animation
        self.finish_action()
        self.action = [stophit, 'hit', 'bot', None,None, None]
        self.queue_add_frames((add_delay(self.hit_frames, stuntime)), force=True)
        self.ishit = True

    def update(self):
        # Flip players if on opposite sides
        if not self.controller:  # check if player 1
            if self.rect.centerx > self.opponent.rect.centerx:
                self.flip = True
                self.opponent.flip = False
            else:
                self.flip = False
                self.opponent.flip = True

        # Reset input buffer
        if len(self.input_buffer) > 10:
            self.input_buffer = self.input_buffer[:10]

        # Get next frame of the animation, if there is no frame go back to idling
        if not self.frame_queue:
            frame = next(self.idle)
        else:
            try:
                frame = next(self.frame_queue)
            except StopIteration:
                frame = next(self.idle)
                self.finish_action()

        # Blit settings
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
            # Manually define horizontal offset of animation (unused)
            # if isinstance(self.action[3], int):  # Horizontal offset
            #     offset = True
            if self.action[4]:
                custom_rect = self.action[4].get_bounding_rect()
            # Call the action function with an argument (unused)
            # if self.action[5]:
            #     self.action[0](self.action[5])
            self.action[0]()

        # If there is a new frame in the animation
        if frame:
            # Save coordinates
            x = self.rect.x
            y = self.rect.y
            bot = self.rect.bottom
            center = self.rect.center
            right = self.rect.right

            self.rect = frame.get_bounding_rect()   # Changes the hitbox based on the current sprite

            if custom_rect:  # Some actions do not want to affect the hitbox
                self.rect = custom_rect

            self.rect.y = y  # Put the new rectangle in the same spot
            self.rect.x = x
            # Change the location of the rectangle depending on which spot we want to stay in place
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

            # Index is used to know when animations have finished
            self.current_frame_index = self.frames.index(frame)
            if self.flip:  # Flip image and right align surface
                frame = pygame.transform.flip(frame, True, False)
                blitcoordinate = [self.rect.bottomright[0] - frame.get_size()[0], self.rect.bottomright[1] - frame.get_size()[1]]
                self.disp.blit(frame, blitcoordinate)
            else:
                self.disp.blit(frame, self.rect)
            self.current_frame = frame
        # If no new frame, display previous frame
        else:
            if self.flip:
                blitcoordinate = [self.rect.bottomright[0] - self.current_frame.get_size()[0], self.rect.bottomright[1] - self.current_frame.get_size()[1]]
                self.disp.blit(self.current_frame, blitcoordinate)
            else:
                self.disp.blit(self.current_frame, self.rect)

    # Clear action and frame queues
    def finish_action(self):
        self.action = None
        self.frame_queue = []

# Inherits from Character
class Ryu(Character):
    def __init__(self, flip, controller, coord, size, opponent, disp):
        super().__init__(flip, controller, size, opponent, disp)
        self.rect = pygame.Rect(coord, size)
        self.frames = parse_spritesheet(pygame.image.load("./ryu_spritesheet.png").convert_alpha(), [144, 130], 14, 15, size)
        self.health = TOTAL_HEALTH
        self.vel_x = 0
        self.vel_y = 0
        self.ishit = False
        self.action = None
        self.frame_queue = None
        self.input_buffer = [None]

        # Some animations are defined here instead of passing as arguments through multiple functions
        self.idle = cycle(add_delay(self.frames[10:14], 10))
        self.hit_frames = self.frames[138:141]
        self.block_frames = self.frames[44:46]

        # Keep track of special moves
        self.specials = {}
        self.special_func = []

    def reset(self):
        """Reset the player's state to initial conditions"""
        self.health = TOTAL_HEALTH
        self.vel_x = 0
        self.vel_y = 0
        self.ishit = False
        self.action = None
        self.frame_queue = None
        self.input_buffer = [None]
        # Reset position based on which player it is
        if self.flip:
            self.rect.x = 1600
        else:
            self.rect.x = 0
        self.rect.y = FLOOR - self.rect.height

    # Inherits from move, specifying animations
    def move(self):
        super().move(jump_side_frames=eval(RYU_JUMP_SIDE), jump_frames=eval(RYU_JUMP_STRAIGHT), walk_right_frames=cycle(add_delay(self.frames[15:20], 5)),
                     walk_left_frames=cycle(add_delay(self.frames[21:27], 5)), crouching_frames=chain(iter((self.frames[34], None, self.frames[35])), cycle((None,))),
                     crouch_up_frames=iter((self.frames[34],None)), jump_sfx=RYU_JUMP_SFX)

    # Implements special attacks(hadouken) while specifying animations for basic ones
    def attack(self):
        def hadouken():
            # Spawn a projectile at the end of the animation
            if self.current_frame_index == 97:
                # Projectile goes away from player
                rect_ = self.frames[178].get_bounding_rect()
                dir = 'left'
                rect_.topright = self.rect.topright
                if self.flip:
                    dir = 'right'
                    rect_.topright = self.rect.topleft

                animation = cycle(add_delay(self.frames[171:179], 1))   # Projectile animation
                self.action[0] = lambda: None   # We don't need to check anything about the player

                # Calculations for the projectile
                def hadouken_proj():
                    global rect
                    rect = rect_  # Use the same rectangle as spawned from the player
                    frame = next(animation)
                    # Projectile must fly away from player
                    if dir == 'right':
                        rect.x -= RYU_HADOUKEN_SPEED
                    else:
                        rect.x += RYU_HADOUKEN_SPEED
                    # Flip projectile if player is flipped
                    if frame:
                        if self.flip:
                            frame = pygame.transform.flip(frame, True, False)

                        # Because the frames of the animation are different sizes, we must change the hitbox and center it every time
                        center = rect.center
                        rect = frame.get_bounding_rect()
                        rect.center = center

                        self.disp.blit(frame, rect)
                        self.specials['hadouken_prev_frame'] = frame
                    else:   # Display prev frame if no new frame
                        self.disp.blit(self.specials['hadouken_prev_frame'], rect)

                    # Hit opponent if they touch the projectile
                    if rect.colliderect(self.opponent.rect):
                        explosion_anim = iter(self.frames[179:185])
                        self.opponent.hit(RYU_HADOUKEN_DMG, RYU_HADOUKEN_ST, RYU_HADOUKEN_KB, 140)

                        # Projectile explodes if it contacts player
                        def hadouken_explosion():
                            # No calculations are necessary, just need to play the animation until it ends
                            try:
                                self.disp.blit(next(explosion_anim), rect)
                            except StopIteration:
                                self.special_func.remove(hadouken_explosion)

                        # Self.special_func is run every game loop
                        self.special_func.append(hadouken_explosion)
                        self.special_func.remove(hadouken_proj)

                    # Despawn projectile if it goes outside of playable area
                    if self.rect.x < 0 or self.rect.x > 1920:
                        self.special_func.remove(hadouken_proj)

                self.special_func.append(hadouken_proj)

        # Run action calculations
        for i in self.special_func:
            i()

        # Special moves are complex multi stage inputs
        # Hadouken input is down, down + right, right + punch
        keys = self.get_input()
        time = pygame.time.get_ticks()  # Create a time limit for doing a special move

        # If player is flipped the input is also reversed so that it is in the same direction as the projectile
        input_towards_center = keys[0][3]
        if self.flip:
            input_towards_center = keys[0][2]

        # The input must pass multiple stages in order to perform the move
        # Stage three
        if self.specials.get('hadouken_progress') == 2:
            if input_towards_center and any((keys[1][0], keys[1][1], keys[1][2])) and nested_sum(keys) == 2 and time < self.specials['hadouken_time'] + RYU_HADOUKEN_LEEWAY:    # Cannot perform hadouken if over time limit, or pressing any other buttons
                self.action = [hadouken, "hadouken", 'bot', None, None, None]
                self.queue_add_frames(chain(add_delay(self.frames[94:99], 5), iter([None for i in range(5)])), force=True)
                self.channel.play(RYU_HADOUKEN_SFX)
                return

        # Stage two
        if self.specials.get('hadouken_progress') == 1:
            if keys[0][1] and input_towards_center and nested_sum(keys) == 2:
                self.specials['hadouken_progress'] = 2

        # Stage one
        if keys[0][1] and nested_sum(keys) == 1:
            self.specials['hadouken_progress'] = 1
            self.specials['hadouken_time'] = time

        # Animation and attack data
        super().attack(keys, lpunch_hbox=RYU_LPUNCH_HBOX, lpunch_kb=RYU_LPUNCH_KB, lpunch_st=RYU_LPUNCH_ST, lpunch_frames=eval(RYU_LPUNCH),
                       lpunch_rect=self.frames[12], lpunch_index=47, lpunch_dmg=RYU_LPUNCH_DMG, lpunch_sfx=RYU_LIGHT_SFX, hit_frame_final_index=140, mpunch_hbox=RYU_MPUNCH_HBOX, mpunch_kb=RYU_MPUNCH_KB, mpunch_st=RYU_MPUNCH_ST,
                       mpunch_frames=eval(RYU_MPUNCH), mpunch_rect=self.frames[12], mpunch_index=50, mpunch_dmg=RYU_MPUNCH_DMG, mpunch_sfx=RYU_MEDIUM_SFX, hpunch_hbox=RYU_HPUNCH_HBOX, hpunch_kb=RYU_HPUNCH_KB, hpunch_st=RYU_HPUNCH_KB,
                       hpunch_frames=eval(RYU_HPUNCH), hpunch_rect=self.frames[12], hpunch_index=52, hpunch_dmg=RYU_HPUNCH_DMG, hpunch_sfx=RYU_HEAVY_SFX, lkick_hbox=RYU_LKICK_HBOX, lkick_kb=RYU_LKICK_KB, lkick_st=RYU_LKICK_ST,
                       lkick_frames=eval(RYU_LKICK), lkick_rect=self.frames[57], lkick_index=58, lkick_dmg=RYU_LKICK_DMG, lkick_sfx=RYU_LIGHT_SFX, mkick_hbox=RYU_MKICK_HBOX, mkick_kb=RYU_MKICK_KB, mkick_st=RYU_MKICK_ST, mkick_frames=eval(RYU_MKICK),
                       mkick_rect=self.frames[12], mkick_index=63, mkick_dmg=RYU_MKICK_DMG, mkick_sfx=RYU_MEDIUM_SFX,  hkick_hbox=RYU_HKICK_HBOX, hkick_kb=RYU_HKICK_KB, hkick_st=RYU_HKICK_ST, hkick_frames=eval(RYU_HKICK),
                       hkick_rect=self.frames[12], hkick_index=66, hkick_dmg=RYU_HKICK_DMG, hkick_sfx=RYU_HEAVY_SFX,

                       crouch_punch_hbox=RYU_CROUCH_PUNCH_HBOX, crouch_punch_kb=RYU_CROUCH_PUNCH_KB, crouch_punch_st=RYU_CROUCH_PUNCH_ST, crouch_punch_frames=eval(RYU_CROUCH_PUNCH),
                       crouch_punch_rect=self.frames[35], crouch_punch_index=80, crouch_punch_dmg=RYU_CROUCH_PUNCH_DMG, crouch_punch_sfx=RYU_MEDIUM_SFX,
                       crouch_kick_hbox=RYU_CROUCH_KICK_HBOX, crouch_kick_kb=RYU_CROUCH_KICK_KB, crouch_kick_st=RYU_CROUCH_KICK_ST,
                       crouch_kick_frames=eval(RYU_CROUCH_KICK), crouch_kick_rect=self.frames[35], crouch_kick_index=82, crouch_kick_dmg=RYU_CROUCH_KICK_DMG, crouch_kick_sfx=RYU_HEAVY_SFX,

                       air_punch_hbox=RYU_AIR_PUNCH_HBOX, air_punch_kb=RYU_AIR_PUNCH_KB, air_punch_st=RYU_AIR_PUNCH_KB, air_punch_frames=eval(RYU_AIR_PUNCH), air_punch_rect=self.frames[74],
                       air_punch_index=77, air_punch_dmg=RYU_AIR_PUNCH_DMG, air_punch_sfx=RYU_LIGHT_SFX, air_kick_hbox=RYU_AIR_KICK_HBOX, air_kick_kb=RYU_AIR_KICK_KB,
                       air_kick_st=RYU_AIR_KICK_ST, air_kick_frames=eval(RYU_AIR_KICK), air_kick_rect=self.frames[70], air_kick_index=72, air_kick_dmg=RYU_AIR_KICK_DMG, air_kick_sfx=RYU_HEAVY_SFX)

    # Extends character.hit, and plays hit sound
    def hit(self, dmg, stuntime, knockback, hit_frame_final_index):
        super().hit(dmg, stuntime, knockback, hit_frame_final_index)
        self.channel.play(RYU_HURT_SFX)






# Prototype character for chun li, sprite was too low quality
# class ChunLi(Character):
#     def __init__(self, flip, player, coord, size):
#         super().__init__(flip, player, size)
#         spritesheet = pygame.image.load("./chunli_spritesheet.png").convert_alpha()
#         self.frames = parse_spritesheet(spritesheet, [90, 138], 21, 10, [90*6, 138*6])
#         self.rect = self.frames[0].get_bounding_rect()
#         self.idle = cycle(add_delay(self.frames[:4], 9))
#     def move(self, keys):
#         super().move(keys)
