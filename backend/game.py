"""Slither-Web engine: pure game state and rules, no networking.

The snake body lives in a DoublyLinkedList (O(1) head/tail updates) with a
parallel set of occupied cells (O(1) collision checks). The state is sent to
the browser as a list of snakes so Phase 3 can add the A* rival without
changing the protocol.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Dict, Optional, Tuple

from config import (BOX_MAX, BOX_SPAWN_CHANCE, BOX_TTL, DIRS, FOOD_SCORE, FOOD_TARGET,
                    FREEZE_TICKS, GRID, HUNGER_MAX, MIN_LEN, OPPOSITE, STARVE_INTERVAL,
                    START_LEN)
from structures import DoublyLinkedList

Cell = Tuple[int, int]

BOX_EFFECTS = ["growth", "jackpot", "freeze", "snip"]
BOX_WEIGHTS = [3, 3, 2, 2]


class Snake:
    def __init__(self, sid: str, head: Cell, direction: str) -> None:
        self.id = sid
        self.body = DoublyLinkedList()   # head = front, tail = back
        self.cells: set = set()          # same cells, for O(1) membership
        self.queue: deque = deque(maxlen=3)
        self.score = 0
        self.reset(head, direction)

    def reset(self, head: Cell, direction: str, length: int = START_LEN) -> None:
        self.body.clear()
        self.cells.clear()
        self.queue.clear()
        dx, dy = DIRS[direction]
        for i in range(length - 1, -1, -1):   # build tail first so head ends up in front
            c = ((head[0] - dx * i) % GRID, (head[1] - dy * i) % GRID)
            self.body.push_front(c)
            self.cells.add(c)
        self.direction = direction
        self.alive = True
        self.grow_pending = 0
        self.freeze = 0
        self.refill()

    def refill(self) -> None:
        self.hunger = HUNGER_MAX
        self.starve_timer = 0

    @property
    def head(self) -> Cell:
        return self.body.head.value

    @property
    def tail(self) -> Cell:
        return self.body.tail.value

    def steer(self, direction: str) -> None:
        """Queue a turn; ignore repeats and 180-degree reversals."""
        last = self.queue[-1] if self.queue else self.direction
        if direction != last and direction != OPPOSITE[last]:
            self.queue.append(direction)

    def apply_input(self) -> None:
        if self.queue:
            self.direction = self.queue.popleft()

    def next_head(self) -> Cell:
        dx, dy = DIRS[self.direction]
        x, y = self.head
        return ((x + dx) % GRID, (y + dy) % GRID)

    def move(self, new_head: Cell, grow: bool) -> None:
        if not grow:                                  # drop the tail first so that
            self.cells.discard(self.body.pop_back())  # stepping onto it is legal
        self.body.push_front(new_head)
        self.cells.add(new_head)

    def shrink(self, n: int = 1) -> int:
        removed = 0
        while removed < n and len(self.body) > MIN_LEN:
            self.cells.discard(self.body.pop_back())
            removed += 1
        return removed

    @property
    def starving(self) -> bool:
        return self.alive and self.hunger == 0 and self.freeze == 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "dir": self.direction, "alive": self.alive,
            "score": self.score, "length": len(self.body),
            "hunger": self.hunger, "hungerMax": HUNGER_MAX,
            "starving": self.starving, "frozen": self.alive and self.freeze > 0,
            "body": [[x, y] for x, y in self.body],
        }


class Game:
    def __init__(self) -> None:
        self.best = 0
        self.food: set = set()
        self.boxes: Dict[Cell, int] = {}   # cell -> ticks left
        self.reset()

    def reset(self) -> None:
        """Fresh board on the start screen. Nothing moves until 'start'."""
        self.status = "ready"              # ready | playing | paused | gameover
        self.tick_count = 0
        self.over_reason = ""
        self.events: list = []
        self.food.clear()
        self.boxes.clear()
        self.player = Snake("player", (6, GRID // 2), "right")
        self.snakes = [self.player]
        while len(self.food) < FOOD_TARGET and self._spawn_food():
            pass

    # ---------- commands from the client ----------
    def handle_command(self, cmd: str) -> None:
        if cmd in DIRS:
            if self.status == "playing":
                self.player.steer(cmd)
        elif cmd == "pause":
            if self.status in ("playing", "paused"):
                self.status = "paused" if self.status == "playing" else "playing"
        elif cmd == "start":
            if self.status == "gameover":
                self.reset()
            if self.status == "ready":
                self.status = "playing"

    # ---------- one simulation step ----------
    def tick(self) -> None:
        self.events = []
        if self.status != "playing":
            return
        self.tick_count += 1

        s = self.player
        s.apply_input()
        nh = s.next_head()
        eats = nh in self.food
        grow = s.grow_pending + int(eats) > 0

        # a tail that is about to move away doesn't count as blocking
        if nh in s.cells and not (nh == s.tail and not grow):
            self._die("You ran into yourself")
            return

        s.move(nh, grow)
        s.grow_pending = max(s.grow_pending + int(eats) - 1, 0)
        if eats:
            self.food.discard(nh)
            s.score += FOOD_SCORE
            s.refill()
        if nh in self.boxes:
            del self.boxes[nh]
            self._open_box(s)
        if not eats and self._hunger_tick(s):
            self._die("You starved")
            return

        while len(self.food) < FOOD_TARGET and self._spawn_food():
            pass
        for cell in list(self.boxes):
            self.boxes[cell] -= 1
            if self.boxes[cell] <= 0:
                del self.boxes[cell]
        if len(self.boxes) < BOX_MAX and random.random() < BOX_SPAWN_CHANCE:
            self._spawn_box()

        self.best = max(self.best, s.score)

    # ---------- rules ----------
    def _hunger_tick(self, s: Snake) -> bool:
        """Advance hunger one tick. Returns True if the snake starves to death."""
        if s.freeze > 0:
            s.freeze -= 1
            return False
        if s.hunger > 0:
            s.hunger -= 1
            return False
        s.starve_timer += 1
        if s.starve_timer >= STARVE_INTERVAL:
            s.starve_timer = 0
            if s.shrink(1) == 0:
                return True
            self.events.append({"kind": "starve", "text": "Starving: lost a segment"})
        return False

    def _open_box(self, s: Snake) -> None:
        effect = random.choices(BOX_EFFECTS, weights=BOX_WEIGHTS)[0]
        if effect == "growth":
            s.grow_pending += 3
            text = "Growth surge +3"
        elif effect == "jackpot":
            s.score += 50
            text = "Jackpot +50"
        elif effect == "freeze":
            s.freeze = FREEZE_TICKS
            s.refill()
            text = "Iron stomach: hunger paused"
        else:
            s.shrink(2)
            text = "Tail snip -2"
        self.events.append({"kind": "box", "text": text})

    def _die(self, reason: str) -> None:
        self.player.alive = False
        self.status = "gameover"
        self.over_reason = reason
        self.best = max(self.best, self.player.score)
        self.events.append({"kind": "death", "text": reason})

    # ---------- spawning ----------
    def _random_free_cell(self) -> Optional[Cell]:
        taken = set(self.food) | set(self.boxes)
        for s in self.snakes:
            taken |= s.cells
        for _ in range(100):
            c = (random.randrange(GRID), random.randrange(GRID))
            if c not in taken:
                return c
        free = [(x, y) for x in range(GRID) for y in range(GRID) if (x, y) not in taken]
        return random.choice(free) if free else None

    def _spawn_food(self) -> bool:
        c = self._random_free_cell()
        if c is None:
            return False
        self.food.add(c)
        return True

    def _spawn_box(self) -> None:
        c = self._random_free_cell()
        if c is not None:
            self.boxes[c] = BOX_TTL

    # ---------- what the client sees ----------
    def snapshot(self) -> dict:
        return {
            "type": "state", "tick": self.tick_count, "grid": GRID,
            "status": self.status, "reason": self.over_reason, "best": self.best,
            "snakes": [s.to_dict() for s in self.snakes],
            "food": [[x, y] for x, y in self.food],
            "boxes": [[x, y, ttl] for (x, y), ttl in self.boxes.items()],
            "events": self.events,
        }
