"""
SimulatorBridge — the single source of truth shared between the game thread
and the WebSocket server thread.

Data flows:
  GAME  → bridge.push_frame(led_table)    → WS server → browser (colors)
  BROWSER → bridge.push_input(row, col)   → game reads get_state_table() (press)
"""

import threading
import time
import json
from collections import deque
from typing import Optional, Set, Callable


class SimulatorBridge:
    """Singleton bridge between the Python game logic and the WS server."""

    _instance: Optional["SimulatorBridge"] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "SimulatorBridge":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.rows = 16
        self.cols = 26

        # Current LED color frame: list of (rows * cols) [R, G, B] entries, row-major
        self._frame: list = [[[0, 0, 0]] * self.cols for _ in range(self.rows)]
        self._frame_lock = threading.Lock()
        self._frame_dirty = False

        # Pending tile-press events from browser clicks
        # Each entry is (row, col, pressed: bool)
        self._input_queue: deque = deque(maxlen=128)
        self._input_lock = threading.Lock()

        # Callbacks registered by the WS server to broadcast frames
        self._broadcast_callbacks: list[Callable] = []
        self._callback_lock = threading.Lock()

        # Active led_table reference (SimulatorLedTable instance)
        self._led_table = None

        # FPS tracking
        self.frame_count = 0
        self.fps = 0.0
        self._fps_last_time = time.time()

    # ------------------------------------------------------------------ #
    #  Called by SimulatorLedTable (game side)                            #
    # ------------------------------------------------------------------ #

    def register_led_table(self, led_table) -> None:
        """Called when the game creates its LedTable instance."""
        self._led_table = led_table
        self.rows = led_table.rows
        self.cols = led_table.cols

    def push_frame(self, led_table_2d: list) -> None:
        """
        Game calls this after every color update.
        led_table_2d is a 2-D list [row][col] where each cell is a color:
          - tuple (R, G, B)  OR
          - list  [R, G, B]
        """
        with self._frame_lock:
            self._frame = led_table_2d
            self._frame_dirty = True

        # FPS tracking
        self.frame_count += 1
        now = time.time()
        elapsed = now - self._fps_last_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self._fps_last_time = now

        self._do_broadcast()

    def apply_pending_inputs(self, state_table: list) -> None:
        """
        Game calls this inside get_state_table().
        Drains the input queue and sets the matching cells to True.
        """
        with self._input_lock:
            while self._input_queue:
                row, col, pressed = self._input_queue.popleft()
                if 0 <= row < len(state_table) and 0 <= col < len(state_table[0]):
                    state_table[row][col] = pressed

    # ------------------------------------------------------------------ #
    #  Called by the WS server (browser side)                             #
    # ------------------------------------------------------------------ #

    def push_input(self, row: int, col: int, pressed: bool) -> None:
        """Browser click → queue a tile press/release event."""
        with self._input_lock:
            self._input_queue.append((row, col, pressed))

    def register_broadcast_callback(self, cb: Callable) -> None:
        with self._callback_lock:
            self._broadcast_callbacks.append(cb)

    def unregister_broadcast_callback(self, cb: Callable) -> None:
        with self._callback_lock:
            if cb in self._broadcast_callbacks:
                self._broadcast_callbacks.remove(cb)

    @staticmethod
    def _cell_to_rings(cell) -> list:
        """
        Convert a cell value to a list of 3 [R,G,B] rings.
        Accepts:
          - compound: [[R,G,B],[R,G,B],[R,G,B]]  (one per ring)
          - flat:     [R,G,B] or (R,G,B)          (same color for all rings)
        """
        _BLACK = [0, 0, 0]
        if not cell:
            return [_BLACK, _BLACK, _BLACK]
        if isinstance(cell[0], (list, tuple)):
            # Compound — extract up to 3 rings
            rings = []
            for k in range(3):
                if k < len(cell):
                    r = cell[k]
                    rings.append([int(r[0]), int(r[1]), int(r[2])])
                else:
                    rings.append(_BLACK)
            return rings
        # Flat (R,G,B)
        rgb = [int(cell[0]), int(cell[1]), int(cell[2])]
        return [rgb, list(rgb), list(rgb)]

    def get_frame_json(self) -> str:
        """
        Serialize the current LED frame to JSON for the browser.
        Each cell is sent as [[R0,G0,B0],[R1,G1,B1],[R2,G2,B2]]
        representing the 3 concentric rings of each hexagon tile.
        """
        with self._frame_lock:
            frame = self._frame

        rows = self.rows
        cols = self.cols
        flat = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                cell = frame[r][c] if r < len(frame) and c < len(frame[r]) else None
                row_data.append(self._cell_to_rings(cell))
            flat.append(row_data)

        return json.dumps({
            "type": "frame",
            "rows": rows,
            "cols": cols,
            "grid": flat,
            "fps": round(self.fps, 1),
        })

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _do_broadcast(self) -> None:
        with self._callback_lock:
            cbs = list(self._broadcast_callbacks)
        for cb in cbs:
            try:
                cb()
            except Exception:
                pass
