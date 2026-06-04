"""
WebSocket + HTTP server for the LED simulator.

Runs in its own thread with a dedicated asyncio event loop so it doesn't
block the game's tkinter main loop.

API
───
GET  /                → index.html  (hex grid UI)
GET  /leaderboard     → leaderboard.html
GET  /api/leaderboard → JSON leaderboard data
GET  /status          → JSON health check
WS   /ws              → bidirectional

  Server → Client messages:
    {"type": "frame", "rows": 16, "cols": 26, "grid": [[r,g,b]...], "fps": 12.3}
    {"type": "status", "message": "..."}

  Client → Server messages:
    {"type": "press",   "row": 3, "col": 7}   — tile stepped on
    {"type": "release", "row": 3, "col": 7}   — tile released
    {"type": "ping"}
"""

import asyncio
import json
import os
import threading
from typing import Set

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from simulator.bridge import SimulatorBridge


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
HOST = "127.0.0.1"
PORT = 8765


class ConnectionManager:
    """Tracks active WebSocket connections."""

    def __init__(self):
        self.active: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.active.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self.active.discard(ws)

    async def broadcast(self, message: str):
        async with self._lock:
            dead = set()
            for ws in self.active:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.add(ws)
            self.active -= dead


def _get_leaderboard_data(limit: int = 200) -> list:
    """Read leaderboard rows from local_data.db (runs in any thread)."""
    import sqlite3 as _sqlite3
    db_path = "./data/local_data.db"
    try:
        conn = _sqlite3.connect(db_path)
        conn.row_factory = _sqlite3.Row
        cur = conn.cursor()
        # Ensure table exists
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS game_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                played_at       TEXT    NOT NULL,
                game_name       TEXT    NOT NULL,
                level           TEXT,
                player_count    INTEGER,
                players         TEXT,
                duration_min    REAL,
                time_played_sec REAL,
                score           REAL,
                score_p1        REAL,
                score_p2        REAL,
                lives_start     INTEGER,
                lives_left      INTEGER
            );
        """)
        cur.execute(
            """SELECT id, played_at, game_name, level, player_count, players,
                      duration_min, time_played_sec, score, score_p1, score_p2,
                      lives_start, lives_left
               FROM game_results
               ORDER BY score DESC, played_at DESC
               LIMIT ?""", (limit,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []


def create_app(manager: ConnectionManager) -> "FastAPI":
    app = FastAPI(title="LED Hex Simulator")

    @app.get("/")
    async def index():
        path = os.path.join(STATIC_DIR, "index.html")
        return FileResponse(path)

    @app.get("/leaderboard")
    async def leaderboard_page():
        path = os.path.join(STATIC_DIR, "leaderboard.html")
        return FileResponse(path)

    @app.get("/api/leaderboard")
    async def leaderboard_api(limit: int = 200):
        import asyncio
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _get_leaderboard_data, limit)
        return JSONResponse({"rows": rows, "total": len(rows)})

    @app.get("/status")
    async def status():
        bridge = SimulatorBridge.get()
        return JSONResponse({
            "status": "ok",
            "clients": len(manager.active),
            "fps": round(bridge.fps, 1),
            "rows": bridge.rows,
            "cols": bridge.cols,
        })

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        bridge = SimulatorBridge.get()
        await manager.connect(ws)

        # Send current frame immediately on connect
        await ws.send_text(bridge.get_frame_json())

        try:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "press":
                    bridge.push_input(int(msg["row"]), int(msg["col"]), True)

                elif msg_type == "release":
                    bridge.push_input(int(msg["row"]), int(msg["col"]), False)

                elif msg_type == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))

        except WebSocketDisconnect:
            pass
        finally:
            await manager.disconnect(ws)

    return app


class SimulatorServer:
    """Runs the FastAPI server in a daemon thread."""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._manager: ConnectionManager | None = None

    def start(self) -> None:
        if not _FASTAPI_AVAILABLE:
            print("[Simulator] WARNING: fastapi/uvicorn not installed. Web UI disabled.")
            print("[Simulator]   Run: uv pip install fastapi uvicorn[standard]")
            return

        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._manager = ConnectionManager()
            app = create_app(self._manager)

            # Register broadcast callback with the bridge
            bridge = SimulatorBridge.get()

            def on_frame():
                """Called by the game thread when new colors are ready."""
                if self._manager and self._loop and not self._loop.is_closed():
                    msg = bridge.get_frame_json()
                    asyncio.run_coroutine_threadsafe(
                        self._manager.broadcast(msg), self._loop
                    )

            bridge.register_broadcast_callback(on_frame)

            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                log_level="warning",
                loop="asyncio",
            )
            server = uvicorn.Server(config)
            self._loop.run_until_complete(server.serve())

        self._thread = threading.Thread(target=_run, daemon=True, name="SimulatorWS")
        self._thread.start()

        print(f"\n{'='*55}")
        print(f"  LED Hex Simulator  →  http://{self.host}:{self.port}")
        print(f"{'='*55}\n")

    def stop(self) -> None:
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
