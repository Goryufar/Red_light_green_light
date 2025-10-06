import pygame
import time
import random

# Initialize
pygame.init()
random.seed(42)  # reproducible car spawns

# Screen setup
WIDTH, HEIGHT = 800, 800
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossroad Traffic Light Simulation with AI Timing")

# Fonts for UI
font = pygame.font.SysFont('Arial', 24)

# Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
BLUE = (0, 150, 255)
WHITE = (255, 255, 255)
CAR_COLORS = [(0, 150, 255), (255, 200, 0), (0, 200, 100), (200, 0, 200)]

# Car setup
car_size = 40
cars_ns = []
cars_ew = []

# Traffic light setup
light_radius = 20
light_ns = RED
light_ew = GREEN
last_switch = time.time()
switch_interval = 5  # initial default interval

# Stop line positions
stop_line_ns = HEIGHT//2 - 50
stop_line_ew = WIDTH//2 - 50

# Functions to spawn cars
def spawn_car_ns():
    x = WIDTH//2 - car_size//2
    y = -car_size
    speed = random.randint(2, 5)
    acceleration = 0.05
    color = random.choice(CAR_COLORS)
    cars_ns.append({
        "x": x, "y": y, "speed": speed, "current_speed": 0,
        "acceleration": acceleration, "color": color
    })

def spawn_car_ew():
    x = -car_size
    y = HEIGHT//2 - car_size//2
    speed = random.randint(2, 5)
    acceleration = 0.05
    color = random.choice(CAR_COLORS)
    cars_ew.append({
        "x": x, "y": y, "speed": speed, "current_speed": 0,
        "acceleration": acceleration, "color": color
    })

# --- Metrics for AI traffic light ---
def calculate_queues():
    queue_ns = sum(1 for car in cars_ns if car["y"] + car_size >= stop_line_ns - 50 and light_ns == RED)
    queue_ew = sum(1 for car in cars_ew if car["x"] + car_size >= stop_line_ew - 50 and light_ew == RED)
    return queue_ns, queue_ew

# Game loop
running = True
clock = pygame.time.Clock()
spawn_timer_ns = 0
spawn_timer_ew = 0
SAFE_DISTANCE = 30

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- AI Traffic Light Control ---
    current_time = time.time()
    queue_ns, queue_ew = calculate_queues()
    time_left_ns = max(0, switch_interval - (current_time - last_switch))
    time_left_ew = time_left_ns  # simplified since one switches when other switches

    if current_time - last_switch > switch_interval:
        # Decide which light should turn green based on queue sizes
        if queue_ns >= queue_ew:
            light_ns = GREEN
            light_ew = RED
            switch_interval = min(max(queue_ns * 0.5, 3), 10)
        else:
            light_ns = RED
            light_ew = GREEN
            switch_interval = min(max(queue_ew * 0.5, 3), 10)
        last_switch = current_time
        time_left_ns = switch_interval
        time_left_ew = switch_interval

    # --- Spawn Cars ---
    spawn_timer_ns += 1
    spawn_timer_ew += 1
    if spawn_timer_ns > 20:
        spawn_car_ns()
        spawn_timer_ns = 0
    if spawn_timer_ew > 20:
        spawn_car_ew()
        spawn_timer_ew = 0

    # --- Update Vertical Cars ---
    for i, car in enumerate(cars_ns):
        car_front = car["y"] + car_size
        can_move = True

        if light_ns == RED and car_front < stop_line_ns and car_front + car["speed"] >= stop_line_ns:
            can_move = False

        if i > 0 and car["y"] + car_size + SAFE_DISTANCE >= cars_ns[i - 1]["y"]:
            can_move = False

        conflict_cars = []
        for h_car in cars_ew:
            if (car["y"] < h_car["y"] + car_size and car_front > h_car["y"]) and \
                    (car["x"] < h_car["x"] + car_size and car["x"] + car_size > h_car["x"]):
                conflict_cars.append(h_car)

        if conflict_cars and i == 0:
            if random.random() < 0.5:
                can_move = False

        if can_move:
            car["y"] += car["speed"]

    # --- Update Horizontal Cars ---
    for i, car in enumerate(cars_ew):
        car_front = car["x"] + car_size
        can_move = True

        if light_ew == RED and car_front < stop_line_ew and car_front + car["speed"] >= stop_line_ew:
            can_move = False

        if i > 0 and car["x"] + car_size + SAFE_DISTANCE >= cars_ew[i - 1]["x"]:
            can_move = False

        conflict_cars = []
        for v_car in cars_ns:
            if (car["x"] < v_car["x"] + car_size and car_front > v_car["x"]) and \
                    (car["y"] < v_car["y"] + car_size and car["y"] + car_size > v_car["y"]):
                conflict_cars.append(v_car)

        if conflict_cars and i == 0:
            if random.random() < 0.5:
                can_move = False

        if can_move:
            car["x"] += car["speed"]

    # Remove cars outside screen
    cars_ns = [c for c in cars_ns if c["y"] <= HEIGHT]
    cars_ew = [c for c in cars_ew if c["x"] <= WIDTH]

    # --- Drawing ---
    win.fill(GRAY)
    pygame.draw.rect(win, (50, 50, 50), (WIDTH//2 - 60, 0, 120, HEIGHT))  # vertical
    pygame.draw.rect(win, (50, 50, 50), (0, HEIGHT//2 - 60, WIDTH, 120))  # horizontal
    pygame.draw.line(win, WHITE, (WIDTH//2 - 60, stop_line_ns), (WIDTH//2 + 60, stop_line_ns), 5)
    pygame.draw.line(win, WHITE, (stop_line_ew, HEIGHT//2 - 60), (stop_line_ew, HEIGHT//2 + 60), 5)

    for car in cars_ns:
        pygame.draw.rect(win, car["color"], (car["x"], car["y"], car_size, car_size))
    for car in cars_ew:
        pygame.draw.rect(win, car["color"], (car["x"], car["y"], car_size, car_size))

    pygame.draw.circle(win, light_ns, (WIDTH//2 + 80, HEIGHT//2 - 100), light_radius)
    pygame.draw.circle(win, light_ew, (WIDTH//2 - 100, HEIGHT//2 + 80), light_radius)

    # --- Draw UI ---
    ui_ns = font.render(f"NS Queue: {queue_ns} | Green Time Left: {time_left_ns:.1f}s", True, WHITE)
    ui_ew = font.render(f"EW Queue: {queue_ew} | Green Time Left: {time_left_ew:.1f}s", True, WHITE)
    win.blit(ui_ns, (10, 10))
    win.blit(ui_ew, (10, 40))

    pygame.display.update()
    clock.tick(100)

pygame.quit()
