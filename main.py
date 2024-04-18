import math
import classes
from classes import *

pygame.init()

screen = pygame.display.set_mode((width, height))

classes.width = pygame.display.get_surface().get_width()
classes.height = pygame.display.get_surface().get_height()

classes.scale = Vector(classes.width, classes.height) // 300

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

idle_animation = Animation(character_ss, Vector(0, 0), Vector(56, 0), True, Vector(56, 56), 6, 0.25)
run_animation = Animation(character_ss, Vector(0, 112), Vector(56, 0), True, Vector(56, 56), 8, 0.25)
jump_animation = Animation(character_ss, Vector(0, 168), Vector(56,0), False, Vector(56, 56), 8, 0.15)
falling_animation = Animation(character_ss, Vector(0, 224), Vector(56, 0), False, Vector(56, 56), 8, 0.15)

sample_level = Level("Project/Assets/oak_woods_v1.0/oak_woods_tileset.png", 24, "SampleLevel", "C:/Users/charl/PycharmProjects/Project/Project/Assets/oak_woods_v1.0/background", Vector(320, 180))
player_sprite = Sprite(idle_animation.Frames[0], pos, Vector(22, 32), Vector(-18 * 2, -24 * 2), 2)

player_sprite.set_animation(idle_animation)

flipped = False
can_jump = False
jump_velocity = 100
fall_acceleration = 200
fall_vector = Vector(0, fall_acceleration)
movement_velocity = 100

desired_cam_pos = Vector(player_sprite.Hitbox.Position.X // level_width, 0) * level_width
start_cam_pos = desired_cam_pos
cam_pos = desired_cam_pos
t = 0

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
                case pygame.K_ESCAPE:
                    running = False

    player_sprite.Flipped = movement_vector.X < 0 if movement_vector.X != 0 else player_sprite.Flipped

    if abs(movement_vector.X) > 0:
        player_sprite.set_animation(run_animation)
    else:
        player_sprite.set_animation(idle_animation)

    player_sprite.play_animation()

    dt = clock.tick(75) / 1000

    for i in sprites:
        if i.Type == 0 or i.Type == 1:
            continue

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

    if desired_cam_pos != Vector(player_sprite.Hitbox.Position.X // level_width, 0) * level_width: # check if the desired position has moved
        t = 0
        start_cam_pos = cam_pos
        desired_cam_pos = Vector(player_sprite.Hitbox.Position.X // level_width, 0) * level_width

    t += dt

    if t > 1:
        t = 1

    cam_pos = start_cam_pos + (desired_cam_pos - start_cam_pos) * (3 * t**2 - 2 * t**3)

    for i in sprites:
        if i.Type == 0:
            continue

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