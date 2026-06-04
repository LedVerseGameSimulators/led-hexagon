"""
SimulatorLedTable — a drop-in replacement for the real LedTable (gui2/gui_led_table_editor.py).

The real LedTable is a tkinter Canvas widget that:
  • Draws the hex/rect LED grid on screen
  • Reads tile-press events from the physical COM ports

This class has the SAME interface but:
  • Skips all tkinter drawing (no display window needed)
  • Routes color output → SimulatorBridge → WebSocket → browser
  • Routes tile-press input ← SimulatorBridge ← WebSocket ← browser clicks

The game code never knows the difference.
"""

import threading
from typing import List, Optional
from simulator.bridge import SimulatorBridge


class SimulatorLedTable:
    """Virtual LED table that replaces the real tkinter-based LedTable."""

    def __init__(
        self,
        root,                       # tkinter root (ignored)
        wall_light_arr_len: int,
        led_row: int,
        led_col: int,
        table_display: bool = False,
    ):
        self.rows = led_row
        self.cols = led_col
        # Singular aliases used by game code (led_table.row / led_table.col)
        self.row = led_row
        self.col = led_col

        # ── Core floor LED state ──────────────────────────────────────────
        # led_table[row][col] = [R, G, B]  — what the game writes to
        self.led_table: List[List[List[int]]] = [
            [[0, 0, 0] for _ in range(led_col)]
            for _ in range(led_row)
        ]

        # state_table[row][col] = bool — True when that tile is being stepped on
        self._state_table: List[List[bool]] = [
            [False] * led_col for _ in range(led_row)
        ]
        # Secondary state array used by some game paths
        self._state_2array: List[List[bool]] = [
            [False] * led_col for _ in range(led_row)
        ]
        # Wall "has been trodden" tracking
        self._g_wall_has_been_tread_arr2: List[List[bool]] = [
            [False] * led_col for _ in range(led_row)
        ]

        # ── Wall / screen LED arrays ──────────────────────────────────────
        self._wall_light_arr: List[List[int]] = [
            [0, 0, 0] for _ in range(wall_light_arr_len)
        ]
        self._wall_light_state_array: List[bool] = [False] * wall_light_arr_len
        self._wall_screen_arr: List = []

        # ── Dynamic game attributes (set by game logic each round) ───────────
        # The game code writes these directly: led_table.goal_color = color
        self.goal_color  = None   # primary target tile color
        self.goal_color2 = None   # secondary target tile color (EditorGame2)
        self.safe_color  = None   # safe / non-scoring tile color

        # Mouse-click event state written by the GUI canvas; we stub with
        # a no-op default so reads never raise AttributeError.
        # Format: [[row, col], pressed_bool]
        self.led_coors_click      = [[0, 0], False]
        self.led_coors_click_wall = [[0, 0], False]

        # gui_ui.py does: `if self.led_table.canvas:` to decide whether to call
        # draw_canvas().  For the simulator there is no tkinter canvas, so we
        # set this to None so the code falls through to the score-update branch.
        self.canvas = None

        # ── Per-tile state arrays used by scoring/life-calculation code ──────
        # These are 2-D arrays indexed [row][col], mirroring the real hardware.
        def _bool2d():
            return [[False] * led_col for _ in range(led_row)]

        def _float2d():
            return [[0.0] * led_col for _ in range(led_row)]

        # Which tiles are currently "being stepped on" (same data as _state_table;
        # the game loop accesses it via both .table_state and get_state_table()).
        self.table_state = self._state_table          # shared reference

        # Last time each tile was triggered (used for debounce / trigger span).
        self.last_trigger_span = _float2d()

        # Scoring / colour-classification helpers written by life-calc code.
        self.red_table          = _bool2d()   # deduction tiles
        self.safe_table         = _bool2d()   # safe (no score change) tiles
        self.plus_table: List   = [[None] * led_col for _ in range(led_row)]
        self.deduct_table       = _bool2d()   # deduction flag
        self.other_color_table  = _bool2d()   # "other" colour tiles
        self.blue_table         = _bool2d()   # blue tiles (EditorGame2 / Play)
        self.green_table        = _bool2d()   # green tiles (Play)

        # Register with the global bridge
        bridge = SimulatorBridge.get()
        bridge.register_led_table(self)

    # ── State table (INPUT from tiles) ───────────────────────────────────

    def get_state_table(self) -> List[List[bool]]:
        """Called by the game loop each frame to check which tiles are pressed."""
        SimulatorBridge.get().apply_pending_inputs(self._state_table)
        return self._state_table

    def get_state_2array(self) -> List[List[bool]]:
        return self._state_2array

    def get_g_wall_has_been_tread_arr2(self) -> List[List[bool]]:
        return self._g_wall_has_been_tread_arr2

    # ── Wall accessors ───────────────────────────────────────────────────

    def get_wall_light_arr(self) -> List[List[int]]:
        return self._wall_light_arr

    def get_wall_light_state_array(self) -> List[bool]:
        return self._wall_light_state_array

    def get_wall_screen_arr(self) -> List:
        return self._wall_screen_arr

    # ── Color output (OUTPUT to tiles → browser) ─────────────────────────

    def draw_led_color(self) -> None:
        """Called by the game after updating led_table to push colors to hardware."""
        SimulatorBridge.get().push_frame(self.led_table)

    def draw_led_table(self) -> None:
        self.draw_led_color()

    def redraw_led_table_default(self, line=0, draw_canvas=True) -> None:
        """Push the CURRENT led_table colors to the browser simulator.

        In the real hardware the 'default redraw' re-renders whatever colors the
        game just wrote into led_table onto the physical LEDs / tkinter canvas.
        It does NOT clear them.  The draw_canvas flag controls whether the tkinter
        canvas overlay is also refreshed (irrelevant for simulator, always push).
        """
        self.draw_led_color()

    def clear_led_table(self) -> None:
        """Set all LEDs to black. Does NOT push to browser — the caller sends
        the final frame via draw_led_color() after setting all tile colours."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.led_table[r][c] = [0, 0, 0]

    def clear_table_color(self) -> None:
        self.redraw_led_table_default()

    def set_color_table_by_set_cell(self, start_member, color) -> None:
        """Set all cells in start_member to color. color is [R,G,B] or (R,G,B)."""
        c = list(color) if isinstance(color, (tuple, list)) else [0, 0, 0]
        for cell in start_member:
            try:
                r_idx, c_idx = int(cell[0]), int(cell[1])
                if 0 <= r_idx < self.rows and 0 <= c_idx < self.cols:
                    self.led_table[r_idx][c_idx] = c
            except (IndexError, TypeError, ValueError):
                pass

    def set_color_table(self, color_table) -> None:
        """Bulk-set the entire color table."""
        for r in range(min(self.rows, len(color_table))):
            for c in range(min(self.cols, len(color_table[r]))):
                cell = color_table[r][c]
                self.led_table[r][c] = list(cell) if isinstance(cell, (tuple, list)) else [0, 0, 0]
        self.draw_led_color()

    # ── tkinter-compatibility stubs ──────────────────────────────────────
    # The game code sometimes calls these on the led_table object.

    def pack(self, **kwargs) -> None:
        pass

    def grid(self, **kwargs) -> None:
        pass

    def update(self) -> None:
        pass

    def update_idletasks(self) -> None:
        pass

    def configure(self, **kwargs) -> None:
        pass

    def config(self, **kwargs) -> None:
        pass

    def destroy(self) -> None:
        pass

    def after(self, ms: int, func=None, *args):
        if func:
            t = threading.Timer(ms / 1000.0, func, args)
            t.daemon = True
            t.start()
        return None

    def after_cancel(self, after_id) -> None:
        pass

    def bind(self, sequence=None, func=None, add=None):
        pass

    def unbind(self, sequence, funcid=None) -> None:
        pass

    def winfo_width(self) -> int:
        return self.cols * 44

    def winfo_height(self) -> int:
        return self.rows * 38

    # Other methods referenced in the codebase
    def get_cur_select_cell_set(self):
        return set()

    def set_color_of_area_select(self, *args, **kwargs) -> None:
        pass

    def on_cur_select_table(self, *args, **kwargs) -> None:
        pass

    def get_led_tablem(self):
        return self.led_table

    def get_canvas_table_size(self):
        return (self.rows, self.cols)
