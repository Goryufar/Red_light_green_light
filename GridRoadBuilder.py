import pygame
import sys

pygame.init()
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 5
CELL_SIZE = WIDTH // GRID_SIZE

# Colors
GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
ROAD_COLOR = (80, 80, 80)
CAR_COLOR = (0, 200, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)

win = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Grid Road Editor with Cross Lines & Traffic")
font = pygame.font.SysFont('Arial', 18)
STRAIGHT_IMG = pygame.image.load("straight.png").convert_alpha()
TURN_LEFT_IMG = pygame.image.load("turn_left.png").convert_alpha()
TURN_RIGHT_IMG = pygame.image.load("turn_right.png").convert_alpha()
CROSS_STOP_IMG = pygame.image.load("cross_stop.png").convert_alpha()
CROSSROAD_IMG = pygame.image.load("crossroad.png").convert_alpha()
TRAFFIC_LIGHT_RED = pygame.image.load("traffic_red.png").convert_alpha()
TRAFFIC_LIGHT_GREEN = pygame.image.load("traffic_green.png").convert_alpha()
# Road types
ROAD_TYPES = ["empty", "straight", "turn_left", "turn_right", "cross_stop", "crossroad"]
DIRECTIONS = ["up", "right", "down", "left"]

# Grid cells
grid = [[{"type": "empty", "dir": "up"} for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

cursor_x, cursor_y = 0, 0

# Car setup
car = {"x": 0, "y": 0, "dir": "right", "speed": 2.5, "waiting": False}
simulate = False

def rotate_dir(direction, turn):
    i = DIRECTIONS.index(direction)
    if turn == "left":
        return DIRECTIONS[(i - 1) % 4]
    elif turn == "right":
        return DIRECTIONS[(i + 1) % 4]
    return direction

def draw_grid():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(win, GRAY, rect, 1)
            cell = grid[y][x]
            if cell["type"] != "empty":
                draw_road(x, y, cell["type"], cell["dir"])

def draw_road(x, y, road_type, direction):
    if road_type == "straight":
        img = STRAIGHT_IMG
    elif road_type == "turn_left":
        img = TURN_LEFT_IMG
    elif road_type == "turn_right":
        img = TURN_RIGHT_IMG
    elif road_type == "cross_stop":
        img = CROSS_STOP_IMG
    elif road_type == "crossroad":
        img = CROSSROAD_IMG
    else:
        return

    # rotate image according to direction
    dir_index = DIRECTIONS.index(direction)
    rot = dir_index * 90
    rotated = pygame.transform.rotate(img, -rot)
    win.blit(rotated, (x * CELL_SIZE, y * CELL_SIZE))

    # draw traffic light on cross_stop
    if road_type == "cross_stop":
        # simple red/green blinking
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            light_img = TRAFFIC_LIGHT_RED
        else:
            light_img = TRAFFIC_LIGHT_GREEN
        win.blit(light_img, (x * CELL_SIZE + CELL_SIZE//4, y * CELL_SIZE + CELL_SIZE//4))

def draw_cursor():
    rect = pygame.Rect(cursor_x * CELL_SIZE, cursor_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(win, (255, 255, 0), rect, 3)

def move_car():
    global car
    cx = int(car["x"] // CELL_SIZE)
    cy = int(car["y"] // CELL_SIZE)
    if cx < 0 or cy < 0 or cx >= GRID_SIZE or cy >= GRID_SIZE:
        return

    cell = grid[cy][cx]
    t = cell["type"]

    # handle traffic lights
    if t == "cross_stop":
        # simple red light simulation
        cycle = 60  # frames per green/red
        if (pygame.time.get_ticks() // 500) % 2 == 0:  # red half the time
            car["waiting"] = True
        else:
            car["waiting"] = False
    else:
        car["waiting"] = False

    # handle turns
    if t == "turn_left" and not car["waiting"]:
        car["dir"] = rotate_dir(car["dir"], "left")
    elif t == "turn_right" and not car["waiting"]:
        car["dir"] = rotate_dir(car["dir"], "right")
    # crossroad continues straight, nothing to do

    if not car["waiting"]:
        dx, dy = 0, 0
        if car["dir"] == "up": dy = -1
        elif car["dir"] == "down": dy = 1
        elif car["dir"] == "left": dx = -1
        elif car["dir"] == "right": dx = 1

        car["x"] += dx * car["speed"]
        car["y"] += dy * car["speed"]

def draw_car():
    pygame.draw.circle(win, CAR_COLOR, (int(car["x"]) + CELL_SIZE//2, int(car["y"]) + CELL_SIZE//2), 10)

# --------------------------
# Main loop
# --------------------------
running = True
road_index = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RIGHT:
                cursor_x = min(GRID_SIZE - 1, cursor_x + 1)
            elif event.key == pygame.K_LEFT:
                cursor_x = max(0, cursor_x - 1)
            elif event.key == pygame.K_DOWN:
                cursor_y = min(GRID_SIZE - 1, cursor_y + 1)
            elif event.key == pygame.K_UP:
                cursor_y = max(0, cursor_y - 1)
            elif event.key == pygame.K_SPACE:
                # cycle road type
                cell = grid[cursor_y][cursor_x]
                road_index = (ROAD_TYPES.index(cell["type"]) + 1) % len(ROAD_TYPES)
                cell["type"] = ROAD_TYPES[road_index]
            elif event.key == pygame.K_r:
                cell = grid[cursor_y][cursor_x]
                cell["dir"] = rotate_dir(cell["dir"], "right")
            elif event.key == pygame.K_RETURN:
                simulate = not simulate
                car["x"] = cursor_x * CELL_SIZE
                car["y"] = cursor_y * CELL_SIZE
                car["dir"] = grid[cursor_y][cursor_x]["dir"]

    if simulate:
        move_car()

    win.fill((30, 30, 30))
    draw_grid()
    if not simulate:
        draw_cursor()
    if simulate:
        draw_car()

    info = font.render("Arrows=Move  Space=Change road  R=Rotate  Enter=Simulate", True, WHITE)
    win.blit(info, (10, HEIGHT - 30))
    pygame.display.flip()
    pygame.time.Clock().tick(60)
