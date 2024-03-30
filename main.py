import pygame
import math

class Vector:
    def __init__(self, x, y):
        self.X = x
        self.Y = y
        self._index = -1

    def __add__(self, vec):
        return Vector(self.X + vec.X, self.Y + vec.Y)

    def __sub__(self, vec):
        return Vector(self.X - vec.X, self.Y - vec.Y)

    def __isub__(self, vec):
        return Vector(self.X - vec.X, self.Y - vec.Y)

    def __iadd__(self, vec):
        return self.__add__(vec)

    def __mul__(self, scalar: int):
        return Vector(self.X * scalar, self.Y * scalar)

    def __str__(self): # for debugging purposes
        return f"({self.X}, {self.Y})"

    def __iter__(self):
        return self

    def __next__(self):
        self._index += 1

        if self._index > 1:
            self._index = -1
            raise StopIteration

        match self._index:
            case 0:
                return self.X
            case 1:
                return self.Y

class Hitbox:
    def __init__(self, pos, size):
        self.Position = pos
        self.Size = size

    def check_hitbox(self, hitbox):
        collision_x = self.Position.X + self.Size.X >= hitbox.Position.X and hitbox.Position.X + hitbox.Size.X >= self.Position.X
        collision_y = self.Position.Y + self.Size.Y >= hitbox.Position.Y and hitbox.Position.Y + hitbox.Size.Y >= self.Position.Y

        return collision_x and collision_y

    def check_hitbox_point(self, point):
        collision_x = self.Position.X <= point.X <= self.Position.X + self.Size.X
        collision_y = self.Position.Y <= point.Y <= self.Position.Y + self.Size.Y

        return collision_x and collision_y

    def reposition_hitbox(self, hitbox, response):  # assuming a collision has occurred
        v1, v2 = hitbox.Position + hitbox.Size - self.Position, hitbox.Position - self.Position - self.Size

        # v1.X if left edge was closer, v2.X if right edge was closer
        v3 = Vector(v1.X, 0) if abs(v1.X) < abs(v2.X) else Vector(v2.X, 0)

        # v1.Y if top edge was closer, v2.Y if bottom edge was closer
        v3.Y = v1.Y if abs(v1.Y) < abs(v2.Y) else v2.Y

        if abs(v3.X) < abs(v3.Y):
            direction = 2 if v3.X < 0 else 0 # assign direction based on edge

            self.Position.X += v3.X # add difference
        else:
            direction = 1 if v3.Y < 0 else 3 # assign direction based on edge

            self.Position.Y += v3.Y # add difference

        if response:
            response(direction)

buttons = []

class Button:
    def __init__(self, pos, size, name, visible):
        self.Hitbox = Hitbox(pos, size)
        self.Name = name
        self.Visible = visible

        buttons.append(self)

sprites = []

class Sprite:
    def __init__(self, image, pos, size, offset):
        self.Image = image
        self.Flipped = False
        self.UnflippedImage = image
        self.FlippedImage = pygame.transform.flip(image, False, True)
        self.Hitbox = Hitbox(pos, size)
        self.Offset = offset
        self.Animation = None

        sprites.append(self)

    def set_animation(self, animation):
        self.Animation = animation

    def play_animation(self):
        if self.Animation:
            self.Animation.IsPlaying = True

    def stop_animation(self):
        if self.Animation:
            self.Animation.IsPlaying = False

    def reset_animation(self):
        if self.Animation:
            self.Animation.FrameIndex = 0
            self.Animation.TimeSinceLastFrame = 0

class SpriteSheet:
    def __init__(self, sheet_path):
        self.Sheet = pygame.image.load(sheet_path).convert_alpha()

    def load_image(self, image_offset, image_size, scale):
        image = pygame.Surface((image_size.X, image_size.Y)).convert_alpha()
        image.blit(self.Sheet, (0, 0), (*image_offset, *image_size))
        image = pygame.transform.scale(image, (image_size.X * scale.X, image_size.Y * scale.Y))
        image.set_colorkey((0, 0, 0))

        return image

class Animation:
    def __init__(self, sheet, initial_offset, offset, loops, size, scale, number, threshold):
        self.Sheet = sheet
        self.IsPlaying = False
        self.Loops = loops
        self.FrameIndex = 0
        self.TimeSinceLastFrame = 0
        self.Threshold = threshold
        self.Frames = []
        self.FlippedFrames = []

        for i in range(number):
            image = self.Sheet.load_image(initial_offset + offset * i, size, scale)
            flipped_image = pygame.transform.flip(image, True, False).convert_alpha()
            self.Frames.append(image)
            self.FlippedFrames.append(flipped_image)

class Level:
    def __init__(self, level_sheet, block_size, scale, level_name):
        self.LevelSheet = SpriteSheet(level_sheet)
        self.Blocks = []

        with open(f"Project/Levels/{level_name}") as level_file:
            filtered_level = level_file.read().split(",")

            for i in range(len(filtered_level)):
                id = int(filtered_level[i])

                if id == -1:
                    continue

                image_x = (block_size * id) % width
                image_y = (block_size * id) // width

                image_pos = Vector(image_x, image_y)
                image_size = Vector(block_size, block_size)

                image = self.LevelSheet.load_image(image_pos, image_size, scale)

                x = (block_size * i) % width
                y = ((block_size * i) // width) * block_size

                block_pos = Vector(x, y)

                sprites.append(Sprite(image, block_pos, scale * block_size, Vector(0, 0)))

pygame.init()

width, height = 600, 600

screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
running = True

background_colour = (135, 206, 235)
ground_colour = (0, 128, 40)
colour = (0, 0, 0)

pos = Vector(width // 2, 0)
velocity = Vector(0, 0)
movement_vector = Vector(0, 0)

level_width = 400

file_path = "Project/Assets/oak_woods_v1.0/character/char_blue.png"
character_ss = SpriteSheet(file_path)
scale = Vector(2, 2)

idle_animation = Animation(character_ss, Vector(0, 0), Vector(56, 0), True, Vector(56, 56), scale, 6, 0.25)
run_animation = Animation(character_ss, Vector(0, 112), Vector(56, 0), True, Vector(56, 56), scale, 8, 0.25)
jump_animation = Animation(character_ss, Vector(0, 168), Vector(56,0), False, Vector(56, 56), scale, 8, 0.15)
falling_animation = Animation(character_ss, Vector(0, 224), Vector(56, 0), False, Vector(56, 56), scale, 8, 0.15)

sample_level = Level("Project/Assets/oak_woods_v1.0/oak_woods_tileset.png", 24, scale, "SampleLevel")
player_sprite = Sprite(idle_animation.Frames[0], pos, Vector(22 * scale.X, 32 * scale.Y), Vector(-18 * 2, -24 * 2))

player_sprite.set_animation(idle_animation)

flipped = False
can_jump = False
cam_pos = Vector(-width / 2, -height / 2)
jump_velocity = 100
fall_acceleration = 200
fall_vector = Vector(0, fall_acceleration)
movement_velocity = 100

ground_hitbox = Hitbox(Vector(0, height - 20), Vector(width, 20))
platform_hitbox = Hitbox(Vector(width // 2 - 100, 375), Vector(200, 100))

# 0: right
# 1: top
# 2: left
# 3: bottom

def rth_ground(direction):
    global velocity, can_jump

    velocity = Vector(velocity.X, 0)

    if direction == 1:
        can_jump = True

def rth_platform(direction):
    global velocity, can_jump

    if direction == 1:
        velocity = Vector(velocity.X, 0)
        can_jump = True
    elif direction == 3:
        velocity = Vector(velocity.X, -velocity.Y) # bounce

counter = 0
while running:
    mouse_x, mouse_y = None, None

    for event in pygame.event.get():
        multiplier = 0
        change_of_key = False

        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.KEYDOWN:
                multiplier = 1
                change_of_key = True
            case pygame.KEYUP:
                multiplier = -1
                change_of_key = True
            case pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

        if change_of_key:
            match event.key:
                case pygame.K_w:
                    if can_jump:
                        can_jump = False
                        velocity += Vector(0, -jump_velocity) * multiplier
                case pygame.K_a:
                    movement_vector += Vector(-movement_velocity, 0) * multiplier
                case pygame.K_d:
                    movement_vector += Vector(movement_velocity, 0) * multiplier

    player_sprite.Flipped = movement_vector.X < 0 if movement_vector.X != 0 else player_sprite.Flipped

    if abs(movement_vector.X) > 0:
        player_sprite.set_animation(run_animation)
    else:
        player_sprite.set_animation(idle_animation)

    player_sprite.play_animation()

    dt = clock.tick(75) / 1000

    for i in sprites:
        if i.Animation and i.Animation.IsPlaying:
            i.Animation.TimeSinceLastFrame += dt

            if i.Animation.TimeSinceLastFrame >= i.Animation.Threshold:
                i.Animation.TimeSinceLastFrame = 0
                i.Animation.FrameIndex += 1

                frames_len = len(i.Animation.Frames)

                if i.Animation.FrameIndex == frames_len and not i.Animation.Loops:
                    i.stop_animation()
                    i.Animation.FrameIndex -= 1
                else:
                    i.Animation.FrameIndex %= frames_len

            if i.Flipped:
                i.Image = i.Animation.FlippedFrames[i.Animation.FrameIndex]
            else:
                i.Image = i.Animation.Frames[i.Animation.FrameIndex]
        else:
            if i.Flipped:
                i.Image = i.FlippedImage
            else:
                i.Image = i.UnflippedImage


    if not can_jump:
        ratio_clamped = min(abs(velocity.Y) / jump_velocity * 5, 5)

        if velocity.Y < 0: # down is up
            if player_sprite.Flipped:
                player_sprite.Image = jump_animation.FlippedFrames[math.floor(5 - ratio_clamped)]
            else:
                player_sprite.Image = jump_animation.Frames[math.floor(5 - ratio_clamped)]
        elif velocity.Y > 0:
            if player_sprite.Flipped:
                player_sprite.Image = falling_animation.FlippedFrames[math.floor(ratio_clamped)]
            else:
                player_sprite.Image = falling_animation.Frames[math.floor(ratio_clamped)]

    counter += 1

    velocity += Vector(0, fall_acceleration * dt) # in pygame, up is down and vice versa
    velocity += movement_vector
    player_sprite.Hitbox.Position += velocity * dt
    velocity -= movement_vector

    screen.fill(background_colour)

    cam_pos = Vector(player_sprite.Hitbox.Position.X // level_width, 0) * level_width

    for i in sprites:
        image_pos = i.Hitbox.Position + i.Offset - cam_pos

        screen.blit(i.Image, (image_pos.X, image_pos.Y))

        if player_sprite != i and player_sprite.Hitbox.check_hitbox(i.Hitbox):
            if image_pos.Y == 576:
                player_sprite.Hitbox.reposition_hitbox(i.Hitbox, rth_ground)
            else:
                player_sprite.Hitbox.reposition_hitbox(i.Hitbox, rth_platform)

    for i in buttons:
        if i.Visible:
            pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(*i.Hitbox.Position, *i.Hitbox.Size))

    if mouse_x and mouse_y:
        for i in buttons:
            if i.Hitbox.check_hitbox_point(Vector(mouse_x, mouse_y)):
                print(f"clicked on {i.Name}")

    pygame.display.flip()

pygame.quit()