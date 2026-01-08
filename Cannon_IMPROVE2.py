# Import modules
import pygame
import sys
import random

# Initialize pygame
pygame.init()

# Define colors
BLACK = 0, 0, 0
WHITE = 255, 255, 255
BLUE = 0, 0, 255
RED = 255, 0, 0
GREEN = 0, 255, 0  # ADDED: New color for second player

# Define a frame rate
frames_per_second = 60

# Initialize real world parameters
g = 9.8   # Gravitational acceleration (m/s**2)
mass = 1  # Mass of projectile (kg)

# Set parameters for time
speedup = 8    # in order to reduce waiting time for impact we speed up by increasing the timestep
t = 0.0        # time in seconds
dt = (1 / frames_per_second)*speedup  # time increment in seconds

width = 2000.0   # Position of wall to the right and width of the coordinate system
height = 1000.0  # Height of the coordinate system
x_grid = 100 # the interval of x-axis grid of the coordinate system
y_grid = 100  # the interval of y-axis grid of the coordinate system

scale_real_to_screen = 0.5 # scale from the real-world to the screen-coordinate system

# define max rounds, and round count 
round_count = 0 
round_max = 5 

# The wind velocity 
wind_vx = 0 

# Target hit counter
targets_hit = 0


def convert(real_world_x, real_world_y, scale=scale_real_to_screen, real_world_height=height):
    ''' conversion from real-world coordinates to pixel-coordinates '''
    return int(real_world_x*scale), int((real_world_height-real_world_y)*scale-1)


cannon_width, cannon_height = 20, 16
cannon1 = {"x": 200,
           "y": 0+cannon_height,
           "vx": 84.85,  # ≈ 120 m/s angle 45
           "vy": 84.85,  # ≈ 120 m/s angle 45
           "width": cannon_width,
           "height": cannon_height,
           "color": BLUE,
           'ball_radius': 2  # radius in meters
            }

# CHANGE 1: ADDED SECOND PLAYER
cannon2 = {
    "x": width - 200,  # Place on right side
    "y": 0 + cannon_height,
    "vx": -84.85,  # Aim left
    "vy": 84.85,
    "width": cannon_width,
    "height": cannon_height,
    "color": GREEN,
    'ball_radius': 2
}

# list of players - now with two players
players = [cannon1, cannon2]
current_player = 0  # Track whose turn it is

def calc_init_ball_pos(cannon):
    ''' Finds the center of the cannon '''
    return cannon['x'] + cannon['width']/2, cannon['y'] - cannon['height']/2

def draw_cannon(surface, cannon):
    ''' Draw the cannon (the barrel will be the length of the initial velocity of the ball '''
    rect = (
        convert(cannon['x'], cannon['y']),
        (cannon['width']*scale_real_to_screen, cannon['height']*scale_real_to_screen)
    )
    pygame.draw.rect(surface, cannon['color'], rect)
    cannon_center = calc_init_ball_pos(cannon)
    line_from = convert(cannon_center[0], cannon_center[1])
    line_to = convert(cannon_center[0]+cannon['vx']*scale_real_to_screen, cannon_center[1]+cannon['vy']*scale_real_to_screen)
    line_width = 2
    pygame.draw.line(surface, cannon['color'], line_from, line_to, line_width)

def is_inside_field(real_world_x, real_world_y, field_width=width):
    ''' Return true if input is within world '''
    # Note: there is no ceiling
    return 0 < real_world_x < field_width and real_world_y > 0

# Create PyGame screen:
# 1. specify screen size
screen_width, screen_height = int(width*scale_real_to_screen), int(height*scale_real_to_screen)
# 2. define screen
screen = pygame.display.set_mode((screen_width, screen_height))
# 3. set caption
pygame.display.set_caption("My Pygame Skeleton")

# Update pygames clock use the framerate
clock = pygame.time.Clock()


def draw_grid(surface, color, real_x_grid, real_y_grid, real_width=width, real_height=height):
    ''' Draw real-world grid on screen '''
    # vertical lines
    for i in range(int(real_width / real_x_grid)):
        pygame.draw.line(surface, color, convert(i * real_x_grid, 0),  convert(i * real_x_grid, real_height))
    # horisontal lines
    for i in range(int(real_height / y_grid)):
        pygame.draw.line(surface, color, convert(0 , i * real_y_grid ), convert(real_width, i * real_y_grid))

# CHANGE 2: ADDED TARGETS TO HIT
targets = [
    {"x": 500, "y": 100, "width": 30, "height": 30, "color": RED},
    {"x": 1500, "y": 200, "width": 30, "height": 30, "color": RED}
]

def draw_targets(surface):
    for target in targets:
        center_x, center_y = convert(target["x"], target["y"])
        width_pix = target["width"] * scale_real_to_screen
        height_pix = target["height"] * scale_real_to_screen
        rect = (center_x - width_pix/2, center_y - height_pix/2, width_pix, height_pix)
        pygame.draw.rect(surface, target["color"], rect)

def check_target_hit(ball_x, ball_y, ball_radius):
    for target in targets:
        if (abs(ball_x - target["x"]) < target["width"]/2 + ball_radius and
            abs(ball_y - target["y"]) < target["height"]/2 + ball_radius):
            return target
    return None

# Initialize game loop variables
running = True
shooting = True
show_grid = True
turn = 0

# Initialize projectile values (see also function below)
x, y = calc_init_ball_pos(players[turn])
vx = players[turn]['vx']  # x velocity in meters per second
vy = players[turn]['vy']  # y velocity in meters per second
ball_color = players[turn]['color']
ball_radius = players[turn]['ball_radius']
wind_vx = random.randint(-15, 15)

def change_player():
    ''' initialize the global variables of the projectile to be those of the players cannon '''
    global players, turn, x, y, vx, vy, ball_color, ball_radius, wind_vx, current_player
    current_player = (current_player + 1) % len(players)  # CHANGE: Switch between players
    turn = current_player
    x, y = calc_init_ball_pos(players[turn])
    vx, vy = players[turn]['vx'], players[turn]['vy']
    ball_color = players[turn]['color']
    ball_radius = players[turn]['ball_radius']
    wind_vx = random.randint(-15,15)    # New wind speed for each loop

def draw_wind_arrow(surface, wind_speed, color): 
    center_x = screen_width // 2
    center_y = 30
    arrow_length = wind_speed * 5  # Scale for visibility
    
    # Draw arrow line (length shows wind strength)
    end_x = center_x + arrow_length
    pygame.draw.line(surface, color, (center_x, center_y), (end_x, center_y), 5)
    
    # Add arrowhead for right wind (>)
    if wind_speed > 0:
        pygame.draw.polygon(surface, color, [
            (end_x, center_y),
            (end_x - 15, center_y - 10),
            (end_x - 15, center_y + 10)
        ])
    # Add arrowhead for left wind (<)  
    elif wind_speed < 0:
        pygame.draw.polygon(surface, color, [
            (end_x, center_y),
            (end_x + 15, center_y - 10),
            (end_x + 15, center_y + 10)
        ])

def pixel_to_real(pixel_x, pixel_y):
    ''' Convert screen mouse position to game world position '''
    real_x = pixel_x / scale_real_to_screen
    real_y = height - (pixel_y / scale_real_to_screen)
    return real_x, real_y


# Game loop:
while running:

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            show_grid = not show_grid
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: # Event of spacebar sets shooting = True  
            shooting = True

  # If we're NOT shooting, let player aim with mouse
    if not shooting:
        # Get where mouse is
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_real_x, mouse_real_y = pixel_to_real(mouse_x, mouse_y)
        
        # Get cannon center position
        cannon_x, cannon_y = calc_init_ball_pos(players[turn])
        
        # Calculate direction from cannon to mouse
        dx = mouse_real_x - cannon_x
        dy = mouse_real_y - cannon_y
        
        # Update cannon to point at mouse
        players[turn]['vx'] = dx
        players[turn]['vy'] = dy
        vx = dx  # Also update current projectile velocity
        vy = dy


    # Check whether the ball is outside the field
    if not is_inside_field(x,y):
            
        change_player() # if there is only one player, the ball will restart at that players center
        shooting = False    # doesn't shoot more than once, when outside the field until space bar pressed

        round_count +=1                 # Adds 1 for each iteration
        if round_count >= round_max:    # condition for exiting when round = max round
            pygame.quit()               # quits from pygame
            sys.exit()                  # quits from the program itself

    # Game logic
    #   draw a background using screen.fill()
    screen.fill(BLACK)

    # draw grid
    if show_grid:
        draw_grid(screen, RED, x_grid, y_grid, width, height)

    # CHANGE: DRAW TARGETS
    draw_targets(screen)
    
    # Draw the wind arrow 
    draw_wind_arrow(screen, wind_vx, players[turn]['color'])

    # CHANGE: DRAW BOTH PLAYERS' CANNONS
    for player in players:
        draw_cannon(screen, player)

    # convert the real-world coordinates to pixel-coordinates
    x_pix, y_pix = convert(x, y)
    ball_radius_pix = round(scale_real_to_screen * ball_radius)

    # draw ball using the pixel coordinates
    pygame.draw.circle(screen, ball_color, (x_pix,y_pix), ball_radius_pix)

    # print time passed, position and velocity
    # print(f"time: {t}, pos: ({x,y}), vel: ({vx,vy}, pixel pos:({x_pix},{y_pix}))")

    if shooting:
        # update time passed, the projectile 's real-world acceleration, velocity,
        # position for the next time_step using the Leap-Frog algorithm

        # Drag 
        D = 0.1     # Random value

        # Apply force of gravitational acceleration, drag and wind
        Fx = -D * (vx - wind_vx)  # Wind affects relative velocity
        Fy = -mass*g-D*vy      # Vertical forces: gravity + drag (both downward)

        # Compute acceleration
        ax = Fx/mass
        ay = Fy/mass

        # Update velocities from acceleration
        vx = vx + ax*dt
        vy = vy + ay*dt

        # Update positions from velocities
        x = x + vx * dt
        y = y + vy * dt

        # CHANGE 3: CHECK FOR TARGET HITS
        hit_target = check_target_hit(x, y, ball_radius)
        if hit_target:
            targets.remove(hit_target)
            targets_hit += 1
            print(f"Target hit! Total hits: {targets_hit}")
            shooting = False
            change_player()

    # Redraw the screen
    pygame.display.flip()


    # Limit the framerate (must be called in each iteration)
    clock.tick(frames_per_second)

# Close after the game loop
pygame.quit()
sys.exit()