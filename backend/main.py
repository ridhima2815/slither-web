"""FastAPI entry point: one WebSocket per player, each with its own Game and 15 FPS loop.

Run:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import json
import logging
import time

from contextlib import suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

from config import FPS
from game import Game

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slither")

COMMANDS = {"up", "down", "left", "right", "pause", "start"}
FRAME = 1.0 / FPS

app = FastAPI(title="Slither-Web")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict:
    return {"ok": True, "fps": FPS}


async def receiver(ws: WebSocket, game: Game) -> None:
    """Read plain-text commands from the browser. Unknown messages are ignored."""
    while True:
        cmd = (await ws.receive_text()).strip().lower()
        if cmd in COMMANDS:
            game.handle_command(cmd)


async def game_loop(ws: WebSocket, game: Game) -> None:
    """Tick the game and push a JSON snapshot at a steady FPS (drift-corrected)."""
    next_tick = time.perf_counter()
    while True:
        game.tick()
        await ws.send_text(json.dumps(game.snapshot(), separators=(",", ":")))
        next_tick += FRAME
        delay = next_tick - time.perf_counter()
        if delay > 0:
            await asyncio.sleep(delay)
        else:                                  # fell behind: resync instead of bursting
            next_tick = time.perf_counter()
            await asyncio.sleep(0)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    game = Game()
    log.info("client connected")

    tasks = {asyncio.create_task(receiver(ws, game)), asyncio.create_task(game_loop(ws, game))}
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in done:                          # whichever task ended first tells us why
            if not t.cancelled() and t.exception() and not isinstance(t.exception(), WebSocketDisconnect):
                log.info("session ended: %r", t.exception())
    finally:
        for t in tasks:                         # always stop both tasks, no leaks
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if ws.client_state == WebSocketState.CONNECTED:
            with suppress(Exception):
                await ws.close()
        log.info("client disconnected")
