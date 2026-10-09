"""All gameplay knobs in one place. Tune here, nowhere else."""

GRID = 30                  # 30 x 30 board, edges wrap around
FPS = 15                   # server ticks (and WebSocket frames) per second

START_LEN = 3
MIN_LEN = 2                # a snake can shrink down to this, then starvation kills it

# Hunger: counts down one per tick (120 ticks = 8 s). At zero the snake loses a
# segment every STARVE_INTERVAL ticks, and dies once it can't shrink any further.
HUNGER_MAX = 120
STARVE_INTERVAL = 15

FOOD_TARGET = 3            # food items kept on the board
FOOD_SCORE = 10

BOX_MAX = 2                # mystery boxes alive at once
BOX_SPAWN_CHANCE = 1 / 90  # per tick, while below BOX_MAX (about one per 6 s)
BOX_TTL = 150              # ticks before an uncollected box vanishes (10 s)
FREEZE_TICKS = 90          # "iron stomach" duration (6 s)

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
