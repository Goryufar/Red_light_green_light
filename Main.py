import pygame
import time
import random
import math
import json
#I LOVE MY UFAR
# ---------------------------
# Configuration
# ---------------------------
random.seed(42)  # reproducible
SIMULATION_SECONDS = 600        # overall allowed run time (not strict)
STAGE_DURATION = 30             # seconds per stage
SIMULATION_FPS = 60
CAR_SIZE = 40
SAFE_DISTANCE = 30
WIDTH, HEIGHT = 800, 800

# limits for green durations (in seconds)
MIN_GREEN = 2
MAX_GREEN = 12

# score weights
COLLISION_PENALTY = 10
AVG_QUEUE_WEIGHT = 0.2

# schedule generation
SCHEDULE_DURATION = 120  # seconds for schedule
SCHEDULE_MIN_GAP = 1
SCHEDULE_MAX_GAP = 2

# ---------------------------
# Pygame init
# ---------------------------
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossroad — Stage Learning (save/load)")
font = pygame.font.SysFont('Arial', 20)

# Colors
RED = (255, 0, 0)
GREEN = (0, 200, 0)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
CAR_COLORS = [(0, 150, 255), (255, 200, 0), (0, 200, 100), (200, 0, 200)]
ROAD_COLOR = (50, 50, 50)

clock = pygame.time.Clock()

# ---------------------------
# Create deterministic schedule
# ---------------------------
def make_schedule(seed=42):
    rnd = random.Random(seed)
    schedule = []
    t = 0.0
    while t < SCHEDULE_DURATION:
        direction = rnd.choice(["NS", "EW"])
        speed = rnd.randint(2, 5)
        color = rnd.choice(CAR_COLORS)
        schedule.append({"time": t, "dir": direction, "speed": speed, "color": color})
        t += rnd.randint(SCHEDULE_MIN_GAP, SCHEDULE_MAX_GAP)
    return schedule

base_schedule = make_schedule(seed=42)

# ---------------------------
# Persistence helpers
# ---------------------------
def save_learning(state, filename="learning.json"):
    try:
        with open(filename, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print("Error saving learning:", e)

def load_learning(filename="learning.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"stage": 1, "ns_duration": 5, "ew_duration": 5, "best_score": -1e9}
    except Exception as e:
        print("Error loading learning:", e)
        return {"stage": 1, "ns_duration": 5, "ew_duration": 5, "best_score": -1e9}

# ---------------------------
# Load previous learning state if available
# ---------------------------
learned_state = load_learning()
best_candidate = {
    "ns_green": int(learned_state.get("ns_duration", 5)),
    "ew_green": int(learned_state.get("ew_duration", 5))
}
best_score = learned_state.get("best_score", -1e9)
stage_number = int(learned_state.get("stage", 1))

print(f"Loaded learning: stage={stage_number}, best={best_candidate}, best_score={best_score}")

# ---------------------------
# Utility / spawn functions
# ---------------------------
def spawn_car_ns(speed, color):
    return {"x": WIDTH//2 - CAR_SIZE//2, "y": -CAR_SIZE, "speed": speed, "color": color}

def spawn_car_ew(speed, color):
    return {"x": -CAR_SIZE, "y": HEIGHT//2 - CAR_SIZE//2, "speed": speed, "color": color}

# ---------------------------
# Reset simulation environment (for starting a stage or after collision)
# ---------------------------
def reset_environment():
    env = {}
    env["cars_ns"] = []
    env["cars_ew"] = []
    env["schedule_index"] = 0
    env["start_time"] = time.time()
    env["cars_passed_ns"] = 0
    env["cars_passed_ew"] = 0
    env["collision_count"] = 0
    env["queue_sum"] = 0.0
    env["queue_samples"] = 0
    return env

# ---------------------------
# Stage controller (simple evolutionary tuner)
# ---------------------------
# If you want to start exploring from the saved best, use best_candidate,
# otherwise randomize initial candidate.
current_candidate = {
    "ns_green": random.randint(3, 7),
    "ew_green": random.randint(3, 7)
}

def mutate(candidate):
    ns = candidate["ns_green"] + random.randint(-2, 2)
    ew = candidate["ew_green"] + random.randint(-2, 2)
    ns = max(MIN_GREEN, min(MAX_GREEN, ns))
    ew = max(MIN_GREEN, min(MAX_GREEN, ew))
    return {"ns_green": ns, "ew_green": ew}

def light_state_for(candidate, elapsed):
    cycle = candidate["ns_green"] + candidate["ew_green"]
    if cycle <= 0:
        return "NS"
    t = elapsed % cycle
    if t < candidate["ns_green"]:
        return "NS"
    else:
        return "EW"

def compute_score(env):
    passed = env["cars_passed_ns"] + env["cars_passed_ew"]
    collisions = env["collision_count"]
    avg_queue = (env["queue_sum"] / env["queue_samples"]) if env["queue_samples"] > 0 else 0.0
    score = passed - COLLISION_PENALTY * collisions - AVG_QUEUE_WEIGHT * avg_queue
    return score, passed, collisions, avg_queue

# init environment & stage trackers
env = reset_environment()
stage_candidate = current_candidate.copy()
stage_start_time = time.time()

stage_elapsed = 0.0
stop_line_ns = HEIGHT//2 - 50
stop_line_ew = WIDTH//2 - 50

running = True
TOTAL_START = time.time()

# main loop
while running:
    now = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # stage elapsed
    stage_elapsed = now - stage_start_time
    current_green = light_state_for(stage_candidate, stage_elapsed)
    light_ns_color = GREEN if current_green == "NS" else RED
    light_ew_color = GREEN if current_green == "EW" else RED

    # spawn cars from deterministic schedule
    sim_time = now - env["start_time"]
    while env["schedule_index"] < len(base_schedule) and sim_time >= base_schedule[env["schedule_index"]]["time"]:
        item = base_schedule[env["schedule_index"]]
        if item["dir"] == "NS":
            env["cars_ns"].append(spawn_car_ns(item["speed"], item["color"]))
        else:
            env["cars_ew"].append(spawn_car_ew(item["speed"], item["color"]))
        env["schedule_index"] += 1

    # compute instantaneous queues
    q_ns = sum(1 for c in env["cars_ns"] if c["y"] + CAR_SIZE >= stop_line_ns - 50)
    q_ew = sum(1 for c in env["cars_ew"] if c["x"] + CAR_SIZE >= stop_line_ew - 50)
    env["queue_sum"] += (q_ns + q_ew)
    env["queue_samples"] += 1

    # Update vertical cars
    collision_happened = False
    for i, car in enumerate(env["cars_ns"]):
        car_front = car["y"] + CAR_SIZE
        can_move = True

        if current_green != "NS" and car_front < stop_line_ns and car_front + car["speed"] >= stop_line_ns:
            can_move = False
        if i > 0 and car["y"] + CAR_SIZE + SAFE_DISTANCE >= env["cars_ns"][i-1]["y"]:
            can_move = False

        conflict = False
        for h_car in env["cars_ew"]:
            if (car["y"] < h_car["y"] + CAR_SIZE and car_front > h_car["y"]) and \
               (car["x"] < h_car["x"] + CAR_SIZE and car["x"] + CAR_SIZE > h_car["x"]):
                conflict = True
                break
        if conflict and i == 0:
            if random.random() < 0.5:
                can_move = False

        if can_move:
            car["y"] += car["speed"]

    # Update horizontal cars
    for i, car in enumerate(env["cars_ew"]):
        car_front = car["x"] + CAR_SIZE
        can_move = True

        if current_green != "EW" and car_front < stop_line_ew and car_front + car["speed"] >= stop_line_ew:
            can_move = False
        if i > 0 and car["x"] + CAR_SIZE + SAFE_DISTANCE >= env["cars_ew"][i-1]["x"]:
            can_move = False

        conflict = False
        for v_car in env["cars_ns"]:
            if (car["x"] < v_car["x"] + CAR_SIZE and car_front > v_car["x"]) and \
               (car["y"] < v_car["y"] + CAR_SIZE and car["y"] + CAR_SIZE > v_car["y"]):
                conflict = True
                break
        if conflict and i == 0:
            if random.random() < 0.5:
                can_move = False

        if can_move:
            car["x"] += car["speed"]

    # Collision detection
    allcars = env["cars_ns"] + env["cars_ew"]
    for i1, c1 in enumerate(allcars):
        r1 = pygame.Rect(c1["x"], c1["y"], CAR_SIZE, CAR_SIZE)
        for i2, c2 in enumerate(allcars):
            if i1 == i2:
                continue
            r2 = pygame.Rect(c2["x"], c2["y"], CAR_SIZE, CAR_SIZE)
            if r1.colliderect(r2):
                env["collision_count"] += 1
                collision_happened = True
                break
        if collision_happened:
            break

    # Count passed cars
    before_ns = len(env["cars_ns"])
    before_ew = len(env["cars_ew"])
    env["cars_ns"] = [c for c in env["cars_ns"] if c["y"] <= HEIGHT]
    env["cars_ew"] = [c for c in env["cars_ew"] if c["x"] <= WIDTH]
    env["cars_passed_ns"] += before_ns - len(env["cars_ns"])
    env["cars_passed_ew"] += before_ew - len(env["cars_ew"])

    stage_ended_early = collision_happened

    # If stage ends (time or collision), evaluate and save
    if stage_elapsed >= STAGE_DURATION or stage_ended_early:
        score, passed, collisions, avg_queue = compute_score(env)
        print(f"Stage {stage_number} candidate {stage_candidate} => score={score:.2f}, passed={passed}, collisions={collisions}, avg_queue={avg_queue:.2f}")

        improved = False
        if score > best_score:
            best_score = score
            best_candidate = stage_candidate.copy()
            improved = True

        # Save learning state (always save so progress persists)
        learned_state_to_save = {
            "stage": stage_number + 1,
            "ns_duration": best_candidate["ns_green"],
            "ew_duration": best_candidate["ew_green"],
            "best_score": best_score
        }
        save_learning(learned_state_to_save)

        # Prepare next candidate
        if improved:
            next_candidate = mutate(best_candidate)
        else:
            next_candidate = mutate(stage_candidate)

        # Reset environment and stage
        env = reset_environment()
        stage_number += 1
        stage_candidate = next_candidate
        stage_start_time = time.time()

    # ---------- Drawing ----------
    win.fill(GRAY)
    pygame.draw.rect(win, ROAD_COLOR, (WIDTH//2 - 60, 0, 120, HEIGHT))
    pygame.draw.rect(win, ROAD_COLOR, (0, HEIGHT//2 - 60, WIDTH, 120))
    pygame.draw.line(win, WHITE, (WIDTH//2 - 60, stop_line_ns), (WIDTH//2 + 60, stop_line_ns), 5)
    pygame.draw.line(win, WHITE, (stop_line_ew, HEIGHT//2 - 60), (stop_line_ew, HEIGHT//2 + 60), 5)

    for c in env["cars_ns"]:
        pygame.draw.rect(win, c["color"], (c["x"], c["y"], CAR_SIZE, CAR_SIZE))
    for c in env["cars_ew"]:
        pygame.draw.rect(win, c["color"], (c["x"], c["y"], CAR_SIZE, CAR_SIZE))

    pygame.draw.circle(win, light_ns_color, (WIDTH//2 + 80, HEIGHT//2 - 100), 12)
    pygame.draw.circle(win, light_ew_color, (WIDTH//2 - 100, HEIGHT//2 + 80), 12)

    elapsed_stage = time.time() - stage_start_time
    time_left = max(0.0, STAGE_DURATION - elapsed_stage)
    score_preview, passed_preview, coll_preview, avgq_preview = compute_score(env)

    ui_lines = [
        f"Stage: {stage_number}",
        f"Candidate NS/EW: {stage_candidate['ns_green']}s / {stage_candidate['ew_green']}s",
        f"Best NS/EW: {best_candidate['ns_green']}s / {best_candidate['ew_green']}s",
        f"Stage time left: {time_left:.1f}s",
        f"Stage score so far: {score_preview:.2f}  passed:{env['cars_passed_ns']+env['cars_passed_ew']} coll:{env['collision_count']}",
        f"Avg queue (so far): {((env['queue_sum']/env['queue_samples']) if env['queue_samples'] else 0.0):.2f}",
        f"Schedule index: {env['schedule_index']}/{len(base_schedule)}",
        f"Loaded best score: {best_score:.2f}"
    ]
    y = 8
    for line in ui_lines:
        surf = font.render(line, True, WHITE)
        win.blit(surf, (8, y))
        y += 22

    pygame.display.update()
    clock.tick(SIMULATION_FPS)

pygame.quit()
