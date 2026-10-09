import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI(title="Slither-Web Game Engine")

# ==========================================
# 1. DATA STRUCTURES (The Snake)
# ==========================================
class Node:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def add_head(self, x: int, y: int):
        new_node = Node(x, y)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self.length += 1

    def remove_tail(self):
        if not self.tail:
            return None
        removed_node = self.tail
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.tail = self.tail.prev
            self.tail.next = None
        self.length -= 1
        return removed_node

# ==========================================
# 2. THE GAME ENGINE (The Brain)
# ==========================================
class GameEngine:
    def __init__(self):
        def set_direction(self, new_dir: str):
        # Prevent the snake from instantly reversing into itself
        if new_dir == "up" and self.direction["y"] == 0:
            self.direction = {"x": 0, "y": -1}
        elif new_dir == "down" and self.direction["y"] == 0:
            self.direction = {"x": 0, "y": 1}
        elif new_dir == "left" and self.direction["x"] == 0:
            self.direction = {"x": -1, "y": 0}
        elif new_dir == "right" and self.direction["x"] == 0:
            self.direction = {"x": 1, "y": 0}
        self.snake = DoublyLinkedList()
        self.snake.add_head(10, 10)
        self.snake.add_head(11, 10)
        self.snake.add_head(12, 10)
        self.direction = {"x": 1, "y": 0}

    def move_snake(self):
        if not self.snake.head:
            return

        new_x = self.snake.head.x + self.direction["x"]
        new_y = self.snake.head.y + self.direction["y"]

        # ----------------------------------------------------
        # WRAP-AROUND WALLS
        # The canvas is 600px wide, and blocks are 20px. 
        # This means our grid is exactly 30x30 blocks (0 to 29).
        # ----------------------------------------------------
        if new_x >= 30:
            new_x = 0
        elif new_x < 0:
            new_x = 29
            
        if new_y >= 30:
            new_y = 0
        elif new_y < 0:
            new_y = 29

        self.snake.add_head(new_x, new_y)
        self.snake.remove_tail()

    def get_state(self):
        body = []
        current = self.snake.head
        while current:
            body.append({"x": current.x, "y": current.y})
            current = current.next
        return {"snake": body}

engine = GameEngine()

# ==========================================
# 3. WEBSOCKET MANAGER (The Switchboard)
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Shout the message to every connected player's screen
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# ==========================================
# 4. SERVER ROUTES & THE HEARTBEAT
# ==========================================
@app.get("/")
async def root():
    return {"status": "Server is running", "message": "Welcome to Slither-Web"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Catch the shouted command from React
            data = await websocket.receive_text()
            parsed_data = json.loads(data)
            
            # If it contains a direction, update the engine's steering wheel
            if "direction" in parsed_data:
                engine.set_direction(parsed_data["direction"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# The Heartbeat: This runs in the background forever as soon as the server starts
@app.on_event("startup")
async def start_game_loop():
    asyncio.create_task(game_loop())

async def game_loop():
    while True:
        # 1. Move the snake mathematically
        engine.move_snake()
        # 2. Package up the new coordinates
        game_state = engine.get_state()
        # 3. Blast the coordinates through the tunnel
        await manager.broadcast(json.dumps(game_state))
        # 4. Wait a fraction of a second (15 frames per second)
        await asyncio.sleep(1 / 15)