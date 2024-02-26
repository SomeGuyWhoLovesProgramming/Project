import pygame
import math

PI = math.pi

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

    def __mul__(self, scalar):
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
        collision_x = self.Position.X <= point.X and point.X <= self.Position.X + self.Size.X
        collision_y = self.Position.Y <= point.Y and point.Y <= self.Position.Y + self.Size.Y

        return collision_x and collision_y

    def reposition_hitbox(self, hitbox, response):  # assuming a collision has occurred
        v1, v2 = hitbox.Position + hitbox.Size - self.Position, hitbox.Position - self.Position - self.Size

        if abs(v1.X) < abs(v2.X):
            v3 = Vector(v1.X, 0) # left edge was closer, always positive
        else:
            v3 = Vector(v2.X, 0) # right edge was closer, always negative

        if abs(v1.Y) < abs(v2.Y):
            v3.Y = v1.Y # top edge was closer, always positive
        else:
            v3.Y = v2.Y # bottom edge was closer, always negative

        if abs(v3.X) < abs(v3.Y):
            if v3.X < 0:
                direction = 2 # closest edge was the left one
            else:
                direction = 0 # closest edge was the right one

            self.Position.X += v3.X # add difference
        else:
            if v3.Y < 0:
                direction = 1 # closest edge was the top one
            else:
                direction = 3 # closest edge was the bottom one

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

pygame.init()

width, height = 800, 600

screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
running = True

background_colour = (135, 206, 235)
ground_colour = (0, 128, 40)
colour = (0, 0, 0)

size = Vector(80, 80)
pos = Vector(width // 2, 0)
velocity = Vector(0, 0)

can_jump = False
jump_velocity = 100
fall_velocity = 100
movement_velocity = 100

player_hitbox = Hitbox(pos, size)
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

Button(Vector(width / 2, height - 40), Vector(100, 50), "Test", True)

counter = 0
while running:
    if player_hitbox.check_hitbox(ground_hitbox):
        player_hitbox.reposition_hitbox(ground_hitbox, rth_ground)

    if player_hitbox.check_hitbox(platform_hitbox):
        player_hitbox.reposition_hitbox(platform_hitbox, rth_platform)

    movement_vector = Vector(0, 0)
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

    dt = clock.tick(75) / 1000

    counter += 1

    colour = (math.floor(counter / 4) % 255, math.floor(counter / 2) % 255, math.floor(counter) % 255)
    velocity += Vector(0, 1) # in pygame, up is down and vice versa
    velocity += movement_vector
    player_hitbox.Position += velocity * dt

    screen.fill(background_colour)

    pygame.draw.rect(screen, colour, pygame.Rect(*player_hitbox.Position, *player_hitbox.Size)) # draw character
    pygame.draw.rect(screen, ground_colour, pygame.Rect(*ground_hitbox.Position, *ground_hitbox.Size)) # draw ground
    pygame.draw.rect(screen, ground_colour, pygame.Rect(*platform_hitbox.Position, *platform_hitbox.Size)) # draw platform

    for i in buttons:
        if i.Visible:
            pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(*i.Hitbox.Position, *i.Hitbox.Size))

    if mouse_x and mouse_y:
        for i in buttons:
            if i.Hitbox.check_hitbox_point(Vector(mouse_x, mouse_y)):
                print(f"clicked on {i.Name}")

    pygame.display.flip()

pygame.quit()