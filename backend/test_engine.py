"""Headless sanity tests for the engine. Run:  python test_engine.py"""
import random

from config import DIRS, GRID
from game import Game
from structures import DoublyLinkedList


def quiet(g):
    """Stop random spawns so a test is deterministic."""
    g._spawn_food = lambda: False
    g._spawn_box = lambda: None
    g.food.clear()
    g.boxes.clear()
    return g


def check_invariants(g):
    s = g.player
    body = list(s.body)
    assert len(body) == len(s.body) == len(s.cells) == len(set(body)), "list/set out of sync"
    assert set(body) == s.cells
    for a, b in zip(body, body[1:]):
        step = ((a[0] - b[0]) % GRID, (a[1] - b[1]) % GRID)
        assert step in {(1, 0), (GRID - 1, 0), (0, 1), (0, GRID - 1)}, "body not contiguous"
    assert not (g.food & s.cells)


def test_linked_list():
    d = DoublyLinkedList()
    for i in range(5):
        d.push_front(i)
    assert list(d) == [4, 3, 2, 1, 0] and len(d) == 5
    assert d.pop_back() == 0 and d.pop_back() == 1
    assert list(d) == [4, 3, 2] and d.tail.value == 2
    d.clear()
    assert len(d) == 0 and d.head is None


def test_start_flow():
    g = quiet(Game())
    assert g.status == "ready"
    head = g.player.head
    g.handle_command("up")                      # ignored on the start screen
    g.tick()
    assert g.tick_count == 0 and g.player.head == head
    g.handle_command("start")
    g.tick()
    assert g.status == "playing" and g.player.head == (head[0] + 1, head[1])


def test_wrap_around():
    g = quiet(Game())
    g.handle_command("start")
    for _ in range(24):                         # start x=6, so 24 steps right wraps to x=0
        g.tick()
    assert g.player.head == (0, GRID // 2)


def test_self_collision_and_restart():
    g = quiet(Game())
    g.handle_command("start")
    g.player.grow_pending = 2
    for d in ("up", "left", "down"):            # curl back into the body
        g.handle_command(d)
    for _ in range(3):
        g.tick()
    assert g.status == "gameover" and g.over_reason == "You ran into yourself"
    g.handle_command("start")
    assert g.status == "playing" and len(g.player.body) == 3 and g.player.score == 0


def test_turn_queue_and_no_reverse():
    g = quiet(Game())
    g.handle_command("start")
    g.handle_command("left")                    # reversal: ignored
    g.handle_command("up")
    g.handle_command("left")                    # both turns before the next tick
    g.tick()
    g.tick()
    assert g.player.direction == "left"
    assert g.player.head == (5, GRID // 2 - 1)   # up from x=6, then left


def test_eating_and_growth():
    g = quiet(Game())
    g.handle_command("start")
    g.food.add((7, GRID // 2))
    g.tick()
    assert g.player.score == 10 and len(g.player.body) == 4 and not g.food


def test_hunger():
    g = quiet(Game())
    s = g.player
    s.hunger = 0
    for _ in range(15):
        died = g._hunger_tick(s)
    assert len(s.body) == 2 and not died        # shrank 3 -> 2
    for _ in range(15):
        died = g._hunger_tick(s)
    assert died                                 # nothing left to lose


def test_boxes():
    random.seed(3)
    g = quiet(Game())
    for _ in range(40):
        g._open_box(g.player)
        check_invariants(g)


def test_fuzz(games=40, ticks=1500):
    random.seed(7)
    for _ in range(games):
        g = Game()
        for _ in range(ticks):
            r = random.random()
            if r < 0.15:
                g.handle_command(random.choice(list(DIRS)))
            elif r < 0.17:
                g.handle_command("pause")
            g.handle_command("start") if g.status in ("ready", "gameover") else None
            g.tick()
            check_invariants(g)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
