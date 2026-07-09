from pathlib import Path
"""
WebSocket bridge: headless API game state → simulator UI
Connects to http://localhost:8000 API, broadcasts game state via WebSocket
"""

import asyncio
import json
import os
import threading
import time
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx

app = FastAPI()

# Serve static simulator files
SIMULATOR_STATIC = str(Path(__file__).resolve().parent / "games" / "simulator" / "static")
app.mount("/static", StaticFiles(directory=SIMULATOR_STATIC), name="static")

HOST = "127.0.0.1"
_DEFAULT_API_PORT = 8004
_DEFAULT_WS_PORT = 8767
API_PORT = int(os.getenv("API_PORT", _DEFAULT_API_PORT))
PORT = int(os.getenv("WS_BRIDGE_PORT", _DEFAULT_WS_PORT))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://localhost:{API_PORT}")

class GameBridge:
    """Bridge between API and WebSocket clients"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.lock = asyncio.Lock()
        self.current_game_id = None
        self.game_state = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.active_connections.add(ws)
        print(f"[OK] Client connected. Total: {len(self.active_connections)}")

    async def disconnect(self, ws: WebSocket):
        async with self.lock:
            self.active_connections.discard(ws)
        print(f"[OK] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast_state(self, game_state: dict):
        """Send game state to all connected clients in simulator format"""
        if not self.active_connections:
            return

        # Use real LED display from game state, or fallback to empty grid.
        # Each cell = 3 ring colors [[R,G,B],[R,G,B],[R,G,B]] (outer,mid,inner).
        led_display = game_state.get("led_display", [])
        rows = int(game_state.get("grid_rows") or 16)
        cols = int(game_state.get("grid_cols") or 26)
        expected = rows * cols

        def _empty_tile():
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        def _cell_to_rings(cell):
            if (isinstance(cell, (list, tuple)) and len(cell) >= 3
                    and isinstance(cell[0], (list, tuple))):
                return [list(cell[0]), list(cell[1]), list(cell[2])]
            if isinstance(cell, (list, tuple)) and len(cell) >= 3:
                rgb = list(cell[:3])
                return [rgb, rgb, rgb]
            return _empty_tile()

        if led_display and len(led_display) == expected:
            grid = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    row.append(_cell_to_rings(led_display[i * cols + j]))
                grid.append(row)
        else:
            grid = [[_empty_tile() for _ in range(cols)] for _ in range(rows)]

        msg = json.dumps({
            "type": "frame",
            "rows": rows,
            "cols": cols,
            "grid": grid,
            "pressed": game_state.get("pressed_tiles", []),
            "fps": 60,
            "game_id": self.current_game_id
        })

        async with self.lock:
            conns = list(self.active_connections)

        async def _send(ws):
            try:
                await ws.send_text(msg)
                return None
            except Exception as e:
                print(f"[ERR] Send error: {e}")
                return ws

        results = await asyncio.gather(*(_send(ws) for ws in conns), return_exceptions=False)
        dead = {ws for ws in results if ws is not None}
        if dead:
            async with self.lock:
                self.active_connections -= dead

    async def broadcast_blank(self, rows: int, cols: int):
        if not self.active_connections:
            return
        empty = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        msg = json.dumps({
            "type": "frame",
            "rows": rows,
            "cols": cols,
            "grid": [[empty for _ in range(cols)] for _ in range(rows)],
            "pressed": [],
            "fps": 30,
            "game_id": None,
        })
        async with self.lock:
            conns = list(self.active_connections)

        async def _send_blank(ws):
            try:
                await ws.send_text(msg)
                return None
            except Exception:
                return ws

        results = await asyncio.gather(*(_send_blank(ws) for ws in conns), return_exceptions=False)
        dead = {ws for ws in results if ws is not None}
        if dead:
            async with self.lock:
                self.active_connections -= dead

bridge = GameBridge()

@app.get("/")
async def index():
    """Serve simulator UI"""
    return FileResponse(f"{SIMULATOR_STATIC}/index.html")

@app.get("/status")
async def status():
    """Health check"""
    return {
        "status": "ok",
        "game_id": bridge.current_game_id,
        "game_state": bridge.game_state,
        "connected_clients": len(bridge.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for simulator UI"""
    client_game_id = ws.query_params.get("game_id")
    await bridge.connect(ws)
    async with httpx.AsyncClient() as client:
        try:
            while True:
                # Client sends tile commands: {type:'press'|'release', row, col}
                msg = await ws.receive_text()
                try:
                    data = json.loads(msg)
                    if data.get("type") in ("press", "release"):
                        # Forward to API game-input endpoint
                        await client.post(
                            f"{API_BASE_URL}/game-input",
                            json={
                                "row": data.get("row"),
                                "col": data.get("col"),
                                "type": data["type"],
                            },
                            timeout=2,
                        )
                except Exception as e:
                    print(f"[ERR] Input forward error: {e}")
        except WebSocketDisconnect:
            await bridge.disconnect(ws)

async def poll_game_state():
    """Poll API for game state and broadcast to clients"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Get active game state from API
                resp = await client.get(f"{API_BASE_URL}/active-game", timeout=5)
                data = resp.json()

                if data.get("success"):
                    bridge.current_game_id = data["game_id"]
                    bridge.game_state = data["state"]
                    await bridge.broadcast_state(bridge.game_state)
                else:
                    bridge.current_game_id = None
                    bridge.game_state = {}
                    await bridge.broadcast_blank(16, 26)

                await asyncio.sleep(0.033)

            except Exception as e:
                print(f"[ERR] Poll error: {e}")
                await asyncio.sleep(1)

@app.on_event("startup")
async def _start_poller():
    """Run poller in uvicorn's own event loop (same loop as websockets).
    Avoids cross-loop 'bound to a different event loop' errors."""
    asyncio.create_task(poll_game_state())

if __name__ == "__main__":
    print(f"WS Bridge: {HOST}:{PORT}")
    print(f"API: {API_BASE_URL}")
    print(f"Web UI: http://{HOST}:{PORT}")

    # Start WebSocket server (poller launches via startup event)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
