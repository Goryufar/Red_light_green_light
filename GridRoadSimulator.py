import pygame, sys, json, random, time

# --- Config ---
TILE_SIZE = 100
GRID_SIZE = 5
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Road Grid Simulation")
font = pygame.font.SysFont("Arial", 20)

# --- Colors ---
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (50, 150, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (80, 80, 80)

# --- Load grid from editor ---
try:
    with open("grid_layout.json", "r") as f:
        grid = json.load(f)
except FileNotFoundError:
    print("⚠ No grid_layout.json found! Run the editor first.")
    sys.exit()

# --- Car class ---
class Car:
    def __init__(self, grid, x, y):
        self.grid = grid
        self.grid_x = x
        self.grid_y = y
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.speed = 2.0
        self.color = BLUE
        self.waiting = False

    def get_dir_vector(self):
        cell = self.grid[self.grid_y][self.grid_x]
        if cell["dir"] == "↑":
            return (0, -1)
        if cell["dir"] == "↓":
            return (0, 1)
        if cell["dir"] == "←":
            return (-1, 0)
        if cell["dir"] == "→":
            return (1, 0)
        return (0, 0)

    def move(self, traffic_lights):
        if self.waiting:
            return

        dir_x, dir_y = self.get_dir_vector()
        self.x += dir_x * self.speed
        self.y += dir_y * self.speed

        # When car passes center of tile, check next tile
        grid_x_new = int(self.x // TILE_SIZE)
        grid_y_new = int(self.y // TILE_SIZE)

        if (grid_x_new, grid_y_new) != (self.grid_x, self.grid_y):
            # check bounds
            if 0 <= grid_x_new < GRID_SIZE and 0 <= grid_y_new < GRID_SIZE:
                next_cell = self.grid[grid_y_new][grid_x_new]
                if next_cell["type"] == "road":
                    self.grid_x, self.grid_y = grid_x_new, grid_y_new
                elif next_cell["type"] == "light":
                    # stop if light is red
                    if traffic_lights[(grid_x_new, grid_y_new)] == "red":
                        self.waiting = True
                    else:
                        self.grid_x, self.grid_y = grid_x_new, grid_y_new
                else:
                    # no road, stop
                    self.speed = 0
            else:
                self.speed = 0  # out of bounds

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)

# --- Find possible spawn points (roads) ---
road_cells = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if grid[y][x]["type"] == "road"]
if not road_cells:
    print("⚠ No roads found in grid.")
    sys.exit()

# --- Setup traffic lights (toggle every few seconds) ---
traffic_lights = {}
for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        if grid[y][x]["type"] == "light":
            traffic_lights[(x, y)] = "green"

last_switch_time = time.time()

# --- Create car ---
car = Car(grid, *random.choice(road_cells))

# --- Main loop ---
clock = pygame.time.Clock()
while True:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Draw grid ---
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            cell = grid[y][x]
            if cell["type"] == "road":
                pygame.draw.rect(screen, GRAY, rect)
                if cell["dir"]:
                    text = font.render(cell["dir"], True, BLACK)
                    screen.blit(text, (x*TILE_SIZE + TILE_SIZE//2 - 8, y*TILE_SIZE + TILE_SIZE//2 - 10))
            elif cell["type"] == "light":
                pygame.draw.rect(screen, DARK_GRAY, rect)
                color = GREEN if traffic_lights[(x, y)] == "green" else RED
                pygame.draw.circle(screen, color, rect.center, 15)
            pygame.draw.rect(screen, BLACK, rect, 2)

    # --- Traffic light logic (toggle every 3 seconds) ---
    if time.time() - last_switch_time > 3:
        for key in traffic_lights:
            traffic_lights[key] = "red" if traffic_lights[key] == "green" else "green"
        last_switch_time = time.time()
        car.waiting = False  # let cars continue when light switches

    # --- Car movement ---
    car.move(traffic_lights)
    car.draw(screen)

    pygame.display.flip()
    clock.tick(60)
