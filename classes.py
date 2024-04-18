import pygame
import os

level_width, level_height = 600, 600
width, height = 600, 600

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

    def __mul__(self, scalar_or_vector):
        if type(scalar_or_vector) is Vector: # for convenience
            return Vector(self.X * scalar_or_vector.X, self.Y * scalar_or_vector.Y)
        else:
            return Vector(self.X * scalar_or_vector, self.Y * scalar_or_vector)

    def __floordiv__(self, scalar):
        return Vector(self.X // scalar, self.Y // scalar)

    def __eq__(self, vec):
        return self.X == vec.X and self.Y == vec.Y

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

scale = Vector(2, 2)

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
backgrounds = []

# -- type id
# 0 = background
# 1 = level
# 2 = entities

class Sprite:
    def __init__(self, image, pos, size, offset, type):
        self.Image = image
        self.Flipped = False
        self.UnflippedImage = image
        self.FlippedImage = pygame.transform.flip(image, False, True)
        self.Hitbox = Hitbox(pos, size * scale)
        self.Offset = offset
        self.Animation = None
        self.Type = type

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

    def load_image(self, image_offset, image_size):
        image = pygame.Surface((image_size.X, image_size.Y)).convert_alpha()
        image.blit(self.Sheet, (0, 0), (*image_offset, *(image_size * scale)))
        image = pygame.transform.scale(image, (image_size.X * scale.X, image_size.Y * scale.Y))
        image.set_colorkey((0, 0, 0))

        return image

class Animation:
    def __init__(self, sheet, initial_offset, offset, loops, size, number, threshold):
        self.Sheet = sheet
        self.IsPlaying = False
        self.Loops = loops
        self.FrameIndex = 0
        self.TimeSinceLastFrame = 0
        self.Threshold = threshold
        self.Frames = []
        self.FlippedFrames = []

        for i in range(number):
            image = self.Sheet.load_image(initial_offset + offset * i, size)
            flipped_image = pygame.transform.flip(image, True, False).convert_alpha()
            self.Frames.append(image)
            self.FlippedFrames.append(flipped_image)

class Level:
    def __init__(self, level_sheet, block_size, level_name, background_directory, background_size):
        self.LevelSheet = SpriteSheet(level_sheet)
        self.Blocks = []
        self.Background = []

        for i in os.listdir(background_directory):
            background_file = os.path.join(background_directory, i)

            if os.path.isfile(background_file):
                background_image = pygame.image.load(background_file).convert_alpha()

                background_sprite = Sprite(background_image, Vector(width // 2, height // 2), background_size, Vector(0, 0), 0)
                backgrounds.append(background_sprite)

        with open(f"Project/Levels/{level_name}") as level_file:
            filtered_level = [] # level_file.read().split("")
            raw_content = level_file.read()
            content = ""

            for i in raw_content:
                if i != "\n":
                    content += i

            for i in range(0, len(content), 4):
                count = int(content[i:i + 3])
                digit = content[i + 3]

                filtered_level += [digit] * count

            for i in range(len(filtered_level)):
                id = int(filtered_level[i]) - 1

                if id == -1:
                    continue

                image_x = (block_size * id) % level_width
                image_y = (block_size * id) // level_width

                image_pos = Vector(image_x, image_y)
                image_size = Vector(block_size, block_size)

                image = self.LevelSheet.load_image(image_pos, image_size)

                x = (block_size * i) % level_width
                y = ((block_size * i) // level_width) * block_size

                block_pos = Vector(x, y)

                sprites.append(Sprite(image, block_pos, scale * block_size, Vector(0, 0), 1))