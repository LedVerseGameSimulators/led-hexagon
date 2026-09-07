"""
Game Manager - Manages running Play instances and game state
"""
import uuid
import threading
import time
import asyncio
import os
import math
import json
import shelve as _shelve
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from .config import (
    GAME_TIMEOUT_SECONDS,
    MAX_CONCURRENT_GAMES,
    GAMES_ROOT,
    GAME_GROUP_LEVEL_DIR,
)
from .audio_manager import AudioManager

EFFECTS_DIR = Path(
    os.environ.get("HEX_EFFECTS_DIR", str(GAMES_ROOT / "source" / "effects"))
)

USE_SERIAL_HD = os.environ.get("USE_SERIAL_HD", "0") == "1"
if USE_SERIAL_HD:
    import sys as _sys
    _games_dir = str(GAMES_ROOT)
    if _games_dir not in _sys.path:
        _sys.path.insert(0, _games_dir)

# Mock external hardware/GUI/media deps so game_play imports work headless.
# Hardware (serial/led) is only mocked in sim mode; real modules load when
# USE_SERIAL_HD=True. Mirrors the setup in the other 4 games.
import sys
from unittest.mock import MagicMock

mocks = {
    # GUI/Display
    'tkinter': MagicMock(),
    'tkinter.messagebox': MagicMock(),
    'tkinter.font': MagicMock(),
    'gui': MagicMock(),
    'gui.app_gui': MagicMock(),
    'gui.gui_debugging': MagicMock(),
    'gui.gui_setting': MagicMock(),
    'gui.language': MagicMock(),
    'gui2': MagicMock(),
    'gui2.gui_led_table_editor': MagicMock(),
    'gui2.gui_led_canvas2': MagicMock(),
    'gui2.gui_table_editor': MagicMock(),
    'gui2.ui_player_setting': MagicMock(),
    'gui2.ui_table': MagicMock(),
    'gui2.gui_util': MagicMock(),
    'ui_design': MagicMock(),
    # Hardware: only mock in sim mode; real modules used when USE_SERIAL_HD=True
    **({} if USE_SERIAL_HD else {
        'serial': MagicMock(),
        'serial.tools': MagicMock(),
        'serial.tools.list_ports': MagicMock(),
        'led': MagicMock(),
        'led.led_control': MagicMock(),
        'led.communication': MagicMock(),
        'led.position_convert': MagicMock(),
        'led.led_serial_thread': MagicMock(),
        'led.led_control_c': MagicMock(),
    }),
    'net': MagicMock(),
    'socket': MagicMock(),
    # Audio/Video — do NOT mock pygame/audio_play (venue BGM/SFX need real mixer)
    'moviepy': MagicMock(),
    'moviepy.editor': MagicMock(),
    'cv2': MagicMock(),
    # Input
    'pynput': MagicMock(),
    'pynput.keyboard': MagicMock(),
    'pynput.mouse': MagicMock(),
    # Encryption
    'encryption': MagicMock(),
    'encryption.yanqian': MagicMock(),
    'rsa': MagicMock(),
    'Crypto': MagicMock(),
    'Crypto.Hash': MagicMock(),
    'Crypto.Cipher': MagicMock(),
    'Crypto.PublicKey': MagicMock(),
    'Crypto.Signature': MagicMock(),
    # Database
    'mysql': MagicMock(),
    'mysql.connector': MagicMock(),
    # Image processing
    'numpy': MagicMock(),
    'PIL': MagicMock(),
    'PIL.Image': MagicMock(),
    'PIL.ImageTk': MagicMock(),
}
for _mod_name, _mock in mocks.items():
    sys.modules[_mod_name] = _mock

# Will import after config is set
# from game_play.Play import Play

# Real game settings live in the decompiled project's shelve DBs.
_CLONE_ROOT = str(GAMES_ROOT)
_LED_PARAM = f"{_CLONE_ROOT}/setting/led_parameter"
_DEBUG_PARAM = f"{_CLONE_ROOT}/setting/debug_parameter"

# Sensible fallbacks if the shelve can't be read.
_SETTINGS_DEFAULTS = {
    "game_time_sec": 300.0,    # game_time_sw (min) * 60
    "life_value": 20,          # life_value_sw  (starting HP)
    "leval_span": 0.9,         # leval_span_sw  (speed span)
    "tread_red_time": 0.01,    # debug: secs on red before life loss
    "life_value_count_time": 1.2,  # debug: min secs between life losses
}

_settings_cache = None


def load_real_settings() -> dict:
    """Read game settings from the decompiled project's shelve DBs once.
    Returns a parsed dict; falls back to defaults on any error."""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    s = dict(_SETTINGS_DEFAULTS)
    # led_parameter: game length, HP, speed span
    try:
        db = _shelve.open(_LED_PARAM, flag="r")
        try:
            gt = db.get("game_time_sw")
            if gt is not None:
                s["game_time_sec"] = float(gt) * 60.0   # stored in minutes
            lv = db.get("life_value_sw")
            if lv is not None:
                s["life_value"] = int(float(lv))
            ls = db.get("leval_span_sw")
            if ls is not None:
                s["leval_span"] = float(ls)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not read led_parameter: {e}; using defaults")
    # debug_parameter: red-penalty timing
    try:
        db = _shelve.open(_DEBUG_PARAM, flag="r")
        try:
            trt = db.get("tread_red_time")
            if trt is not None:
                s["tread_red_time"] = float(trt)
            lct = db.get("life_value_count_time")
            if lct is not None:
                s["life_value_count_time"] = float(lct)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not read debug_parameter: {e}; using defaults")
    _settings_cache = s
    logger.info(f"Loaded real settings: {s}")
    return s

_HW_DEFAULT_ROWS = 16
_HW_DEFAULT_COLS = 26
_hw_led_control = None
_hw_layout_type = 0
_HW_DRAW_INTERVAL = float(os.environ.get("HW_DRAW_INTERVAL", "0.045"))
_hw_serial_lock = threading.Lock()


def _normalize_rgb(cell):
    """Ensure [R,G,B] ints. Used only for flat-RGB games; hexagon uses 3-ring format."""
    if isinstance(cell, (list, tuple)):
        if len(cell) >= 3 and isinstance(cell[0], (int, float)):
            return [int(cell[0]), int(cell[1]), int(cell[2])]
        if len(cell) == 1:
            return _normalize_rgb(cell[0])
    return [0, 0, 0]


def _hw_init():
    global _hw_led_control, _hw_layout_type
    if _hw_led_control is not None:
        return _hw_led_control
    try:
        import shelve as _s
        from led import led_control as _lc
        # led_control.draw_screen_by_com is gated on Setting.USE_SERIAL_HD —
        # force it on when this process was started with USE_SERIAL_HD=1.
        from model.setting import Setting as _Setting
        _Setting.USE_SERIAL_HD = True
        db = _s.open(str(GAMES_ROOT / 'setting' / 'led_parameter'), flag='r')
        list_com_info = db.get('list_com_info', [])
        layout_type   = int(db.get('led_layout_type', 0))
        no_use        = db.get('floor_layout_coors_no_use', [])
        rows          = int(float(db.get('value_high', _HW_DEFAULT_ROWS)))
        cols          = int(float(db.get('value_width', _HW_DEFAULT_COLS)))
        db.close()
        _lc.init_layout(layout_type, rows, cols, no_use)
        errors = _lc.init_com(list_com_info)
        if errors:
            logger.warning(f"HW init COM errors (non-fatal): {errors}")
        logger.info(f"Hardware ready: {len(list_com_info)} port(s), {rows}×{cols}, layout={layout_type}")
        _hw_led_control = _lc
        _hw_layout_type = layout_type
    except Exception as e:
        logger.error(f"Hardware init failed: {e}")
    return _hw_led_control


def _hw_read_sensors(layout_type, state_table):
    """Read floor sensors (fast). Caller must hold _hw_serial_lock."""
    if _hw_led_control is None:
        return
    _hw_led_control.update_screen_state_by_com(layout_type, state_table, state_table)


def _read_hardware_snapshot(led_table, read_sensors):
    """Read into an isolated snapshot; failures return an all-released grid."""
    snapshot = [
        [False] * led_table.led_col for _ in range(led_table.led_row)
    ]
    try:
        read_sensors(snapshot)
    except Exception as error:
        logger.warning(f"HW read failed: {error}")
        snapshot = [
            [False] * led_table.led_col for _ in range(led_table.led_row)
        ]
    return snapshot


def _hw_blank_floor(led_table):
    """Send one all-black frame (all 3 rings) to the physical floor.

    Call on every game end/stop path (session-end, stop_game, clear_all) so
    the hardware doesn't stay stuck lit with the last frame drawn before the
    session ended — the per-frame draw call only runs inside the active
    level loop, so nothing else ever blanks the floor once that loop stops.
    Uses the SAME draw_screen_by_com call as normal gameplay frames, just
    with an all-[0,0,0] grid on all 3 rings (outer/mid/inner) per hex tile.
    No-op in sim mode / if hardware was never initialized.
    """
    if not (USE_SERIAL_HD and _hw_led_control is not None):
        return
    if led_table is None:
        return
    try:
        rows = getattr(led_table, "led_row", _HW_DEFAULT_ROWS)
        cols = getattr(led_table, "led_col", _HW_DEFAULT_COLS)
        blank_cell = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # 3 rings, all off
        blank_grid = [[blank_cell for _ in range(cols)] for _ in range(rows)]
        with _hw_serial_lock:
            _hw_led_control.draw_screen_by_com(_hw_layout_type, blank_grid)
        logger.info("HW: blank frame sent to floor (session end/stop)")
    except Exception as e:
        logger.warning(f"HW blank failed: {e}")


def _normalize_rings(cell):
    """Normalize a led_table cell to 3 ring colors [[r,g,b],[r,g,b],[r,g,b]]
    (outer, mid, inner). Cell is normally a 3-ring list, but tolerate a flat
    (r,g,b) (broadcast to all rings)."""
    try:
        if isinstance(cell, (list, tuple)) and len(cell) > 0:
            if isinstance(cell[0], (list, tuple)):
                rings = [[int(c[0]), int(c[1]), int(c[2])] for c in cell[:3]]
                while len(rings) < 3:
                    rings.append(rings[-1])
                return rings
            # flat (r,g,b) -> all rings same
            rgb = [int(cell[0]), int(cell[1]), int(cell[2])]
            return [rgb, rgb, rgb]
    except Exception:
        pass
    return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def _cell_is_lit(cell):
    """True if any ring of the cell has a non-zero channel."""
    for ring in _normalize_rings(cell):
        if ring[0] or ring[1] or ring[2]:
            return True
    return False


def _cell_is_red(cell):
    """True if any ring is RED-dominant ((254,0,0)-like). Red = penalty tile."""
    for r, g, b in _normalize_rings(cell):
        if r >= 200 and g < 80 and b < 80:
            return True
    return False


def _group_main_color(color):
    """A group's representative color = its middle ring (ring[1]); ring[0] is a
    constant green marker. Returns an (r,g,b) tuple."""
    rings = _normalize_rings(color)
    return tuple(rings[1])


def _rgb_is_deduct(rgb):
    """DEDUCT_COLOR (254,0,48): consume + penalty (distinct from plain red)."""
    return rgb[0] >= 200 and rgb[1] < 80 and 30 <= rgb[2] <= 90


def _rgb_is_red(rgb):
    """Plain RED (254,0,0): hazard, stays, repeats. Excludes DEDUCT (b~48)."""
    return rgb[0] >= 200 and rgb[1] < 80 and rgb[2] < 30


# Memory-mode camouflage / already-checked empties (3 rings each).
_TEAL_HIDDEN = [[0, 62, 62], [0, 62, 62], [0, 62, 62]]
_CHECKED_TEAL = [[0, 40, 40], [0, 40, 40], [0, 40, 40]]  # darker: "I already tried this"


def _rings_is_camouflage_teal(rings):
    """True if all three rings match memory camouflage teal."""
    for ring in _normalize_rings(rings):
        if list(ring) != _TEAL_HIDDEN[0]:
            return False
    return True


# Level-progression tiers (dirs under source/, easy->hard). Category is
# locked by the START level's file type: .led = 1-player, .ledb = 2-player.
# A 1P session marathons only the 1P tiers and never crosses into 2P.
# Note: games/Extra/*.led (17-26) is separate dev/test scaffolding, not part
# of the real tier progression -- intentionally not included here.
_TIERS_1P = ["-", "--"]      # pro -> advanced (.led)
_TIERS_2P = ["---"]          # DK 2P (.ledb)
# Group mode: same dash-folder names as 1P, rooted at games/source_group/
_TIERS_GROUP = list(_TIERS_1P)


def _level_sort_key(p):
    stem = os.path.basename(p).rsplit(".", 1)[0]
    return (0, int(stem)) if stem.isdigit() else (1, stem.lower())


def _build_level_sequence(start_level):
    """Ordered list of level FILE PATHS forming the marathon.

    Category is locked by the START level's file type. A start level found in
    a 1P (.led) tier yields a 1P-only chain (its tier onward through
    _TIERS_1P); a start level in a 2P (.ledb) tier yields a 2P-only chain.
    Never mixes."""
    import glob as _glob
    src = str(GAMES_ROOT)
    sl = str(start_level or "").strip()

    def _chain(dirs, ext):
        return [(d, sorted(_glob.glob(os.path.join(src, "source", d, f"*.{ext}")),
                           key=_level_sort_key)) for d in dirs]

    chain_1p = _chain(_TIERS_1P, "led")
    chain_2p = _chain(_TIERS_2P, "ledb")

    def _find(chain):
        for ti, (_d, files) in enumerate(chain):
            for fi, f in enumerate(files):
                stem = os.path.basename(f).rsplit(".", 1)[0]
                if stem == sl or stem.startswith(sl):
                    return ti, fi
        return None

    loc = _find(chain_1p)
    chain = chain_1p
    if loc is None:
        loc = _find(chain_2p)
        chain = chain_2p
    if loc is None:                       # unknown start -> begin at 1P tier 0
        chain, loc = chain_1p, (0, 0)
        if not chain or not chain[0][1]:
            return []

    ti, fi = loc
    seq = list(chain[ti][1][fi:])         # remaining levels in the start tier
    for j in range(ti + 1, len(chain)):   # then all later SAME-category tiers
        seq.extend(chain[j][1])
    return seq


def _build_group_level_sequence(start_level=None):
    """Marathon paths from games/source_group/ (Group mode only, .led).

    Same progression rules as 1P tiers, but a separate admin-curated tree.
    If start_level is missing/unknown, begin at the first file of the first
    non-empty group tier.
    """
    import glob as _glob
    root = str(GAME_GROUP_LEVEL_DIR)
    sl = str(start_level or "").strip()
    if sl.lower() in ("", "auto", "none"):
        sl = ""

    chain = [
        (d, sorted(_glob.glob(os.path.join(root, d, "*.led")), key=_level_sort_key))
        for d in _TIERS_GROUP
    ]
    # Drop empty tiers so admins can leave a middle folder empty
    chain = [(d, files) for d, files in chain if files]
    if not chain:
        return []

    loc = None
    if sl:
        for ti, (_d, files) in enumerate(chain):
            for fi, f in enumerate(files):
                stem = os.path.basename(f).rsplit(".", 1)[0]
                if stem == sl or stem.startswith(sl):
                    loc = (ti, fi)
                    break
            if loc is not None:
                break
    if loc is None:
        loc = (0, 0)

    ti, fi = loc
    seq = list(chain[ti][1][fi:])
    for j in range(ti + 1, len(chain)):
        seq.extend(chain[j][1])
    return seq


def _load_level_file(path):
    """Load one .led/.ledb: unzip, find the main gameplay shelve (dict_group
    + para_key_game), return (dict_group, game_obj) as in-memory objects.
    (None, None) on failure. Same shape as the other 4 games' loader, so the
    marathon session loop can call it repeatedly -- including a fresh reload
    on every level-restart attempt, since scoring mutates dict_group's groups
    in-place."""
    import zipfile, tempfile, shelve
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path, 'r') as z:
                z.extractall(tmpdir)
            for root, _, files in os.walk(tmpdir):
                if not any(
                    f.startswith("game_file") and f.split(".", 1)[-1] in ("dat", "db")
                    for f in files
                ):
                    continue
                gf = os.path.join(root, "game_file")
                if not (
                    os.path.exists(gf + ".dat")
                    or os.path.exists(gf + ".db")
                ):
                    continue
                try:
                    db = shelve.open(gf)
                    go = db.get("para_key_game")
                    dg = db.get("dict_group")
                    db.close()
                    if go is not None and dg is not None:
                        return dg, go
                except Exception:
                    continue
            return None, None
    except Exception as e:
        logger.warning(f"Could not load level file {path}: {e}")
        return None, None


def _effects_path(name: str) -> Path:
    return EFFECTS_DIR / name


def _effect_board_time(dict_group) -> float:
    try:
        return max(
            (float(getattr(g, "end_time_sec", 0.0)) for g in dict_group.values()),
            default=0.05,
        )
    except Exception:
        return 0.05


_COUNTDOWN_STEP_SEC = 0.8


def _phase_step_from_pass(total_pass: float) -> Optional[int]:
    """Map countdown.led timeline to UI sync steps (3→2→1, ~0.8 s each). No GO."""
    if total_pass < _COUNTDOWN_STEP_SEC:
        return 3
    if total_pass < 2 * _COUNTDOWN_STEP_SEC:
        return 2
    if total_pass < 3 * _COUNTDOWN_STEP_SEC:
        return 1
    return None


def _phase_remaining_ms(total_pass: float, step: Optional[int]) -> Optional[int]:
    if step is None:
        return None
    beat_start = (3 - step) * _COUNTDOWN_STEP_SEC
    return int(max(0.0, (_COUNTDOWN_STEP_SEC - (total_pass - beat_start)) * 1000))


def _set_phase(game, phase: str, accepting_input: bool) -> None:
    game.phase = phase
    game.accepting_input = accepting_input
    kwargs = dict(phase=phase, accepting_input=accepting_input)
    if phase != "countdown":
        kwargs["phase_step"] = None
        kwargs["countdown_step"] = None
        kwargs["phase_remaining_ms"] = None
    game.update_state(**kwargs)


class HeadlessGameGUI:
    """Mock GUI parent for Play.running_new() - provides LED update callback"""

    def __init__(self, led_table):
        self.led_table = led_table

    def update_draw_led_table_idle_game(self, dict_group, total_pass=0, time_pass=0):
        """Called by Play.running_new() to update LED display"""
        try:
            if dict_group:
                for key, value in dict_group.items():
                    group = value
                    set_cell = group.start_member
                    start_time = group.start_time_sec
                    end_time = group.end_time_sec
                    if set_cell is not None and total_pass > start_time and total_pass < end_time:
                        color = getattr(group, 'color', (0, 254, 0))
                        if hasattr(self.led_table, 'set_color_table_by_set_cell'):
                            self.led_table.set_color_table_by_set_cell(set_cell, color)
        except Exception as e:
            logger.debug(f"LED update error: {e}")

    def clear_last_wall_display(self):
        """Clear display for next frame"""
        pass


class GameInstance:
    """Single running game instance"""

    def __init__(self, game_id: str, card_id: str, level: int, difficulty: str,
                 mode: str = None):
        self.game_id = game_id
        self.card_id = card_id
        self.level = level
        self.difficulty = difficulty
        self.mode = (mode or "").strip().lower() or None  # "group" or None
        self.created_at = time.time()
        self.play = None  # Play object
        self.led_table = None  # LedTable instance (for press input)
        self.dict_group = None  # level groups (for consume-on-hit)
        self.flashes = {}  # cell -> wall-clock start time (display-only hit flash)
        self.score = 0  # accumulated score from presses on lit tiles
        self.scored_active = set()  # goal cells already scored this appearance
        # Per-frame cell classification (rebuilt each frame from dict_group):
        self.goal_cells = set()    # floor cells matching P1 goal color (scoreable)
        self.goal2_cells = set()   # floor cells matching P2 goal color (2-player)
        self.red_cells = set()     # in-time red hazard cells (penalty, stays)
        self.deduct_cells = set()  # DEDUCT_COLOR cells (penalty + consume)
        self.goal_color = None     # P1 goal color (from goal_led indicator)
        self.goal2_color = None    # P2 goal color (from goal2_led indicator)
        self.score2 = 0            # P2 score (0 in single-player)
        self.scored_active2 = set()# P2 scored cells this appearance
        self.multiplayer = False   # True when level has goal2_led
        self.zone = None          # (row_from,row_to,col_from,col_to) active area
        # 2P respawn: consumed goal tiles reappear after delay (only for .ledb multiplayer)
        self.pending_respawn = []  # [[group, (i,j), reappear_wall_time], ...]
        self.respawn_delay = 8.0   # seconds; tunable
        # Same-color 2P (e.g. DK03 cyan==cyan): alternate P1→P2→P1→P2 per cell.
        # Cells in this set score P2 next; others score P1.
        self.p2_next_cells = set()
        self.input_lock = threading.Lock()  # guards state_table writes
        self._sim_pressed = set()  # simulator clicks (not wiped by HW sensor read)
        self._suppress_until_release = set()  # baseline-held cells blocked until release
        self.phase = "idle"
        self.accepting_input = False
        self.running = False

        # Real settings (game length + HP). Loaded from led_parameter.
        _s = load_real_settings()
        self.game_time_sec = _s["game_time_sec"]   # session limit (300s)

        # Runtime override pushed from the central RFID server (Settings page):
        _override_path = GAMES_ROOT / "setting" / "runtime_overrides.json"
        if _override_path.exists():
            try:
                with open(_override_path) as _f:
                    _overrides = json.load(_f)
                if _overrides.get("session_minutes"):
                    self.game_time_sec = float(_overrides["session_minutes"]) * 60.0
                if _overrides.get("default_difficulty") and not getattr(self, "difficulty", None):
                    self.difficulty = _overrides["default_difficulty"]
            except Exception as _e:
                logger.warning(f"Could not read runtime overrides: {_e}")

        _test_sess = os.environ.get("HEX_TEST_SESSION_SEC")
        if _test_sess:
            self.game_time_sec = float(_test_sess)

        self.board_time_sec = 1e9                   # board length (max group end); set on load
        self.result = None                          # 0 lose / 1 complete / 2 timeout
        self.max_life = _s["life_value"]           # 20 HP
        self.life = self.max_life
        _test_life = os.environ.get("HEX_TEST_LIFE")
        if _test_life:
            self.max_life = int(_test_life)
            self.life = self.max_life
        self.last_life_loss_time = 0.0
        self._life_count_time = _s["life_value_count_time"]
        self._audio = None

        # ── MEMORY MODE (YC/advanced-tier only) ─────────────────────────
        # Scoreable targets flash briefly then hide; a dedicated hint tile
        # (the level's WALL_LIGHT indicator cell) can be pressed to pay a
        # score penalty and re-reveal the remaining targets. None of this
        # timing is in the level data -- it's fixed game behavior, set here
        # as constants. _memory_mode itself IS data-driven (set per-level in
        # _setup_level, true only for "--" tier files).
        self._memory_mode = False
        self.hint_cells = set()        # current frame's hint-tile position(s)
        self._reveal_duration = 5.0    # seconds a reveal stays visible, and also
                                        # the hint tile's per-player phase length
        self._hint_score_cost = 5      # score paid per hint press (no life loss)
        self._reveal_until = 0.0       # total_pass threshold; P1 targets hidden after this
        self._reveal2_until = 0.0      # same, for P2 targets (2P memory levels)
        self._hint_pressed = set()     # edge-trigger guard: fire once per press,
                                        # not once per frame while held (mirrors
                                        # scored_active's pattern for goal/deduct)
        # Per-life reveal after a press (memory mode): keep true color on screen
        # instead of blanking. Cleared on respawn / wave jump / fresh active life.
        self.revealed_colors = {}      # (i,j) -> 3-ring color to paint
        self.revealed_live_red = set() # post-hit deduct cells: keep hurting
        # Full 3-ring colors from the latest classification frame (for reveal paint)
        self._goal_color_full = None
        self._goal2_color_full = None
        self._deduct_color_full = None

        # ── SESSION (5-min marathon) state ──────────────────────────────
        # Score + lives persist across levels; session ends on life<=0 or
        # timer<=0. Player picks a starting level; we marathon to series end.
        self.session_start = None      # wall-clock when first level begins
        self.level_sequence = []       # ordered list of level FILE PATHS
        self.current_level_id = None   # e.g. "01" (for frontend display)
        self.levels_cleared = 0        # how many levels finished this session
        self._session_over = False     # True -> stop the session loop
        self._level_cleared = False    # True -> advance to next level
        self._restart_level = False    # True -> replay same level (life=0, time left)
        self._end_reason = None        # why the session loop exited: timeout/None(=cleared)

        self.current_state = {
            "score": 0,
            "time_elapsed": 0.0,
            "time_left": self.game_time_sec,
            "life": self.max_life,
            "max_life": self.max_life,
            "display_lives": 5,   # always 5 hearts at full HP, whatever max_life is
            "display_max": 5,
            "score2": 0,
            "multiplayer": False,
            "player_pos": [0, 0],
            "led_display": [],
            "game_over": False,
            "game_over_reason": "",
            "result": None,
            "current_level": None,
            "levels_cleared": 0,
            "started_at": "",
            "phase": "idle",
            "accepting_input": False,
            "phase_step": None,
            "countdown_step": None,
            "phase_remaining_ms": None,
            "backend_audio_active": False,
        }
        self.thread = None

    def reset_for_level(self):
        """Clear PER-LEVEL board state before loading the next level.
        Score, score2, life, session timer all PERSIST (not reset)."""
        self.flashes = {}
        self.scored_active = set()
        self.scored_active2 = set()
        self.pending_respawn = []
        self.p2_next_cells = set()
        self.goal_cells = set()
        self.goal2_cells = set()
        self.red_cells = set()
        self.deduct_cells = set()
        self.goal_color = None
        self.goal2_color = None
        self.last_life_loss_time = 0.0
        self._level_cleared = False
        self._restart_level = False
        self._memory_mode = False      # re-set correctly in _setup_level per level
        self.hint_cells = set()
        self._reveal_until = self._reveal_duration   # fresh level -> initial 5s reveal
        self._reveal2_until = self._reveal_duration  # same, for P2 (2P memory levels)
        self._hint_pressed = set()
        self.revealed_colors = {}
        self.revealed_live_red = set()
        self._goal_color_full = None
        self._goal2_color_full = None
        self._deduct_color_full = None

    def _cell_pressed(self, row: int, col: int) -> bool:
        if self.led_table is None:
            return False
        return bool(self.led_table.state_table[row][col]) or (row, col) in self._sim_pressed

    def _refresh_suppress_until_release(self) -> None:
        for row, col in list(self._suppress_until_release):
            if not self._cell_pressed(row, col):
                self._suppress_until_release.discard((row, col))

    def _capture_baseline_suppress(self) -> set:
        held = set()
        if self.led_table is None:
            return held
        for row in range(self.led_table.led_row):
            for col in range(self.led_table.led_col):
                if self._cell_pressed(row, col):
                    held.add((row, col))
        return held

    def begin_level_transition(self):
        """Fail closed while level geometry and classification are changing."""
        with self.input_lock:
            self.accepting_input = False
            if self.led_table is not None:
                for row in self.led_table.state_table:
                    for col_index in range(len(row)):
                        row[col_index] = 0
            self._sim_pressed.clear()
            self._suppress_until_release.clear()
            self._hint_pressed.clear()
            self.goal_cells = set()
            self.goal2_cells = set()
            self.red_cells = set()
            self.deduct_cells = set()
            self.hint_cells = set()
            self.scored_active = set()
            self.scored_active2 = set()
            self.current_state["accepting_input"] = False

    def finish_level_transition(self):
        """Enable input only after the prepared level is installed."""
        with self.input_lock:
            if not (self.running and not self.current_state.get("game_over")):
                return
            if USE_SERIAL_HD and _hw_led_control is not None and self.led_table is not None:
                with _hw_serial_lock:
                    snapshot = _read_hardware_snapshot(
                        self.led_table,
                        lambda state: _hw_read_sensors(_hw_layout_type, state),
                    )
                for row_index, source_row in enumerate(snapshot):
                    target_row = self.led_table.state_table[row_index]
                    for col_index, pressed in enumerate(source_row):
                        target_row[col_index] = 1 if pressed else 0
            self._suppress_until_release = self._capture_baseline_suppress()
            self.accepting_input = True
            self.phase = "playing"
            self.current_state["accepting_input"] = True
            self.current_state["phase"] = "playing"
            self.current_state["phase_step"] = None
            self.current_state["countdown_step"] = None
            self.current_state["phase_remaining_ms"] = None

    def process_frame_input(
        self,
        *,
        goal_cells,
        goal2_cells,
        red_cells,
        deduct_cells,
        hint_cells=None,
        hardware_state=None,
    ):
        """Atomically publish frame input/classification and score pressed cells."""
        with self.input_lock:
            if not self.accepting_input:
                return False

            self.goal_cells = set(goal_cells)
            self.goal2_cells = set(goal2_cells)
            self.red_cells = set(red_cells)
            self.deduct_cells = set(deduct_cells)
            if hint_cells is not None:
                self.hint_cells = set(hint_cells)

            if hardware_state is not None:
                if len(hardware_state) != self.led_table.led_row or any(
                    len(row) != self.led_table.led_col for row in hardware_state
                ):
                    raise ValueError("hardware state dimensions do not match LED table")
                for row_index, source_row in enumerate(hardware_state):
                    target_row = self.led_table.state_table[row_index]
                    for col_index, pressed in enumerate(source_row):
                        target_row[col_index] = 1 if pressed else 0

            self._refresh_suppress_until_release()

            if self.multiplayer:
                self.process_respawns()
            active_consumables = goal_cells | goal2_cells | deduct_cells
            self.scored_active &= active_consumables
            self.scored_active2 &= goal2_cells
            for row in range(self.led_table.led_row):
                for col in range(self.led_table.led_col):
                    if not self._cell_pressed(row, col):
                        continue
                    if (row, col) in self._suppress_until_release:
                        continue
                    self.try_score_cell(row, col)
            return True

    def mark_session_failed(self, reason, error):
        """Record a terminal session error and prevent success resolution."""
        self.begin_level_transition()
        self._session_over = True
        self._end_reason = reason
        self.update_state(
            game_over=True,
            game_over_reason=reason,
            result=0,
            accepting_input=False,
        )

    def refill_life_for_restart(self):
        """Refill and publish HP immediately while the replay is prepared."""
        self.begin_level_transition()
        self.life = self.max_life
        self.last_life_loss_time = 0.0
        self.update_state(
            life=self.life,
            display_lives=5,
            current_level=self.current_level_id,
            accepting_input=False,
        )

    def _clear_cell_reveal(self, cell):
        """Drop per-life reveal marks for one coordinate."""
        self.revealed_colors.pop(cell, None)
        self.revealed_live_red.discard(cell)

    def _clear_all_reveals(self):
        """Drop all per-life reveal marks (wave jump / level reset safety)."""
        self.revealed_colors.clear()
        self.revealed_live_red.clear()

    def _mark_revealed(self, i, j, color_full, checked_empty=False):
        """Keep this cell painted for the rest of its current life (memory mode)."""
        rings = _normalize_rings(color_full if color_full is not None else [0, 0, 0])
        if checked_empty and _rings_is_camouflage_teal(rings):
            rings = [c[:] for c in _CHECKED_TEAL]
        self.revealed_colors[(i, j)] = rings

    def _apply_hazard_penalty(self):
        """Moving-red-style penalty: both scores in 2P + shared HP, rate-limited."""
        now = time.time()
        if now - self.last_life_loss_time < self._life_count_time:
            return False
        self.score -= 1
        if self.score < 0:
            self.score = 0
        if self.multiplayer:
            self.score2 -= 1
            if self.score2 < 0:
                self.score2 = 0
        self.life -= 1
        self.last_life_loss_time = now
        audio = getattr(self, "_audio", None)
        if audio is not None:
            audio.play_hurt_sfx()
        return True

    def _current_level_time(self) -> float:
        """Level timeline for consume/scoring (Play.total_pass)."""
        if self.play is not None:
            return float(getattr(self.play, "total_pass", 0.0))
        return 0.0

    def is_expired(self) -> bool:
        """Check if game timed out"""
        elapsed = time.time() - self.created_at
        return elapsed > GAME_TIMEOUT_SECONDS

    def get_state(self) -> dict:
        """Get current game state"""
        return self.current_state

    def update_state(self, **kwargs):
        """Update game state"""
        self.current_state.update(kwargs)

    def try_score_cell(self, i, j, total_pass=None):
        """Type-aware scoring for a press on cell (i,j):
          - hint tile (memory mode) -> -5 score (NO life loss), re-reveals
            remaining targets for _reveal_duration seconds
          - red hazard cell  -> -1 point + -1 HP (HP rate-limited; both scores in 2P)
          - memory live deduct (after first hit) -> same hazard penalty, stays revealed
          - DEDUCT tile -> penalty + consume; memory: reveal + keep hurting
          - goal_led target -> +1 point + consume; memory: stay revealed (no blank)
          - blank/decor (memory) -> reveal true/checked color, no score
        goal/red membership is classified per frame in the callback."""
        if not self.accepting_input:
            return
        if total_pass is None:
            total_pass = self._current_level_time()
        # Memory-mode hint tile: distinct from goal/red/deduct, checked first.
        # Edge-triggered like goal/deduct cells -- fires once per press, not
        # once per frame while held (the scoring loop calls try_score_cell
        # every frame for every currently-pressed cell; without this guard,
        # holding the hint tile would drain score every frame and
        # continuously re-arm the reveal window for as long as it's held).
        if self._memory_mode and (i, j) in self.hint_cells:
            if (i, j) not in self._hint_pressed:
                self._hint_pressed.add((i, j))
                # Single shared button, no per-player input channel exists on
                # this floor -- attribution instead comes from which color the
                # tile is CURRENTLY showing when the press lands. It alternates
                # every _reveal_duration seconds: 2P levels cycle P1-color ->
                # P2-color -> ...; 1P levels cycle color -> black (off, so a
                # press then is simply a no-op -- the button isn't "showing"
                # for anyone at that moment).
                phase = int(total_pass // self._reveal_duration) % 2
                if not self.multiplayer:
                    if phase == 0:
                        self.score -= self._hint_score_cost
                        if self.score < 0:
                            self.score = 0
                        self._reveal_until = total_pass + self._reveal_duration
                elif phase == 0:
                    self.score -= self._hint_score_cost
                    if self.score < 0:
                        self.score = 0
                    self._reveal_until = total_pass + self._reveal_duration
                else:
                    self.score2 -= self._hint_score_cost
                    if self.score2 < 0:
                        self.score2 = 0
                    self._reveal2_until = total_pass + self._reveal_duration
            return
        # Memory: post-hit deduct keeps hurting (moving-red style) while pressed.
        if self._memory_mode and (i, j) in self.revealed_live_red:
            self._apply_hazard_penalty()
            return
        # Red hazard: penalty + HP loss (gated). Not edge-limited by
        # scored_active (standing on red keeps hurting, rate-limited by time).
        if (i, j) in self.red_cells:
            self._apply_hazard_penalty()
            return
        # DEDUCT tile: penalty then consume (edge-triggered).
        # Memory: fair 2P (both scores) like moving red, then stay revealed and
        # keep hurting via revealed_live_red. Non-memory: P1 score only, blank.
        if (i, j) in self.deduct_cells and (i, j) not in self.scored_active:
            self.scored_active.add((i, j))
            if self._memory_mode:
                self._apply_hazard_penalty()
                self.revealed_live_red.add((i, j))
                deduct_paint = self._deduct_color_full or [
                    [254, 0, 48], [254, 0, 48], [254, 0, 48]
                ]
                self._mark_revealed(i, j, deduct_paint)
                self._consume_cell(i, j, total_pass)
            else:
                self.score -= 1
                if self.score < 0:
                    self.score = 0
                self.life -= 1
                self._consume_cell(i, j, total_pass)
            return
        in_p1 = (i, j) in self.goal_cells
        in_p2 = (i, j) in self.goal2_cells
        same_color = in_p1 and in_p2   # DK03-style: both players same color

        if same_color:
            # Alternate P1→P2→P1→P2 per cell so both players score fairly.
            if (i, j) in self.p2_next_cells:
                if (i, j) not in self.scored_active2:
                    self.scored_active2.add((i, j))
                    self.score2 += 1
                    self.p2_next_cells.discard((i, j))
                    self._consume_cell(i, j, total_pass)
                    if self._memory_mode:
                        self._mark_revealed(i, j, self._goal2_color_full or self._goal_color_full)
            else:
                if (i, j) not in self.scored_active:
                    self.scored_active.add((i, j))
                    self.score += 1
                    self.p2_next_cells.add((i, j))  # next time → P2
                    self._consume_cell(i, j, total_pass)
                    if self._memory_mode:
                        self._mark_revealed(i, j, self._goal_color_full)
            return

        # P1 goal: score + consume
        if in_p1 and (i, j) not in self.scored_active:
            self.scored_active.add((i, j))
            self.score += 1
            audio = getattr(self, "_audio", None)
            if audio is not None:
                audio.play_score_sfx()
            self._consume_cell(i, j, total_pass)
            if self._memory_mode:
                self._mark_revealed(i, j, self._goal_color_full)
            return
        # P2 goal: separate score + consume
        if in_p2 and (i, j) not in self.scored_active2:
            self.scored_active2.add((i, j))
            self.score2 += 1
            self._consume_cell(i, j, total_pass)
            if self._memory_mode:
                self._mark_revealed(i, j, self._goal2_color_full)
            return
        # Memory: blank / non-scorable colored decor — reveal for this life, no score.
        if self._memory_mode and (i, j) not in self.revealed_colors:
            if self.led_table is not None:
                try:
                    raw = self.led_table.led_table[i][j]
                except Exception:
                    raw = [0, 0, 0]
            else:
                raw = [0, 0, 0]
            self._mark_revealed(i, j, raw, checked_empty=True)
        # else non-memory: background decor — neutral, no effect.

    def _consume_cell(self, i, j, total_pass=None):
        """Remove a stepped goal/deduct tile from the group(s) whose time window
        is CURRENTLY ACTIVE. Non-memory: cell blanks. Memory mode: caller keeps
        the cell painted via revealed_colors. 2P (.ledb multiplayer): respawns
        after respawn_delay. 1P: follows native level timing — groups with
        staggered start_times provide natural wave progression; no
        artificial respawn.

        Must filter by time window: the same (row,col) coordinate can be
        reused across separate groups/waves at different times, and without
        this filter, consuming one occurrence silently wipes out every
        future occurrence sharing that coordinate too, ending the level
        early (same bug found and fixed in the other 4 games' consume
        functions)."""
        if total_pass is None:
            total_pass = self._current_level_time()
        reappear_at = time.time() + self.respawn_delay if self.multiplayer else None
        if self.dict_group:
            for g in self.dict_group.values():
                sm = getattr(g, "start_member", None)
                if not sm:
                    continue
                st = getattr(g, "start_time_sec", 0)
                et = getattr(g, "end_time_sec", 0)
                if not (st <= total_pass <= et):
                    continue
                if (i, j) in sm:
                    try:
                        if isinstance(sm, set):
                            sm.discard((i, j))
                        else:
                            sm.remove((i, j))
                        if reappear_at is not None:
                            self.pending_respawn.append([g, (i, j), reappear_at])
                    except Exception:
                        pass
        # display-only hit flash (white blink) for ~0.4s
        self.flashes[(i, j)] = time.time()

    def process_respawns(self):
        """Re-add consumed 2P goal tiles after respawn_delay. Per-frame.
        New life starts hidden again — drop any reveal marks for that cell."""
        if not self.pending_respawn:
            return
        now = time.time(); still = []
        for entry in self.pending_respawn:
            g, cell, t = entry
            if now >= t:
                self._clear_cell_reveal(cell)
                sm = getattr(g, "start_member", None)
                try:
                    if isinstance(sm, set): sm.add(cell)
                    elif sm is not None and cell not in sm: sm.append(cell)
                except Exception:
                    pass
            else:
                still.append(entry)
        self.pending_respawn = still

    def apply_input(self, row: int, col: int, action: str):
        """Record simulator press/release state for the game thread to score."""
        if not self.accepting_input:
            return False
        if self.led_table is None:
            return False
        # Ignore presses outside the level's active zone (e.g. 5x9).
        z = self.zone
        if z and not (z[0] <= row < z[1] and z[2] <= col < z[3]):
            return False
        with self.input_lock:
            if not self.accepting_input:
                return False
            if action == "press":
                self._sim_pressed.add((row, col))
                self.led_table.press_cell(row, col)
            elif action == "release":
                self._sim_pressed.discard((row, col))
                self.led_table.release_cell(row, col)
                self._suppress_until_release.discard((row, col))
                self._hint_pressed.discard((row, col))
        return True


class LevelAttemptPreparationError(ValueError):
    """A level attempt could not be loaded and prepared safely."""


def _run_level_attempt(
    path,
    *,
    led_table,
    level_id,
    setup_consumer,
    play_consumer,
    transition_consumer=None,
    ready_consumer=None,
    failure_consumer=None,
):
    """Load and prepare one fresh attempt before invoking runtime consumers."""
    if transition_consumer is not None:
        transition_consumer()
    groups, game = _load_level_file(path)
    if not groups:
        error = LevelAttemptPreparationError(
            f"Level {level_id} failed to load for attempt"
        )
        if failure_consumer is not None:
            failure_consumer(error)
        raise error

    setup_consumer(groups, game)
    if ready_consumer is not None:
        ready_consumer()
    try:
        play_consumer(groups)
    finally:
        if transition_consumer is not None:
            transition_consumer()
    return groups, game


class GameManager:
    """Manages all running game instances"""

    def __init__(self):
        self.games: Dict[str, GameInstance] = {}
        self.lock = threading.Lock()
        self._create_lock = threading.Lock()
        self.zombie_threads = []
        logger.info("GameManager initialized")

    def clear_all(self):
        """Stop and remove all existing games. Joins threads (3s timeout) before clearing."""
        with self.lock:
            for gid, g in list(self.games.items()):
                g.begin_level_transition()
                g.running = False
            threads = [(gid, g.thread) for gid, g in self.games.items() if getattr(g, "thread", None)]
            # Capture led_table refs before self.games.clear() drops them —
            # needed to send each cleared game's HW blank frame below.
            led_tables = [(gid, getattr(g, "led_table", None)) for gid, g in self.games.items()]
            self.games.clear()
        for gid, t in threads:
            t.join(timeout=3.0)
            if t.is_alive():
                logger.warning(f"Thread {gid} didn't stop in 3s — zombie")
                self.zombie_threads.append(gid)
        # Blank the floor for any game being cleared (e.g. a new game starting
        # while a prior one was still running/stuck) — join threads first so
        # we don't race a still-running frame callback's own draw call.
        for gid, led_table in led_tables:
            _hw_blank_floor(led_table)
        logger.info("Cleared all existing games")

    def create_game(self, card_id: str, level: int, difficulty: str,
                    mode: str = None) -> str:
        """Create new game instance. Clears any prior games first (kiosk model)."""
        self.clear_all()
        with self.lock:
            game_id = str(uuid.uuid4())[:8]
            game = GameInstance(game_id, card_id, level, difficulty, mode=mode)

            # Eagerly set multiplayer from file extension BEFORE the load
            # thread starts, so _consume_cell respawns correctly even if
            # a press arrives before the shelve is fully loaded (~7s).
            # Group mode is always 1P (.led under source_group/).
            if game.mode != "group":
                _clone = str(GAMES_ROOT)
                _ledb = os.path.join(_clone, "source", "---", f"{level}.ledb")
                if os.path.exists(_ledb):
                    game.multiplayer = True
                    logger.info(
                        f"Game created: {game_id} multiplayer=True "
                        f"(card={card_id}, level={level})"
                    )
                else:
                    logger.info(
                        f"Game created: {game_id} (card={card_id}, level={level})"
                    )
            else:
                logger.info(
                    f"Game created: {game_id} mode=group "
                    f"(card={card_id}, level={level})"
                )

            self.games[game_id] = game
            return game_id

    def get_game(self, game_id: str) -> Optional[GameInstance]:
        """Get game by ID"""
        with self.lock:
            return self.games.get(game_id)

    def start_game(self, game_id: str):
        """Start game loop in background thread"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game not found: {game_id}")

        def _run_game():
            try:
                logger.info(f"Starting game loop: {game_id}")

                if USE_SERIAL_HD:
                    _hw_init()

                # Import game modules
                from game_play.Play import Play
                from game_play.game_running import LedTable
                from model.setting import Setting

                # Initialize game components (16x26 grid from settings). These
                # are created ONCE per session and reused across every level
                # in the marathon (only dict_group/board_time/zone/multiplayer
                # change per level, via _setup_level below).
                logger.debug(f"Initializing LED table for game {game_id}")
                led_table = LedTable(wall_light_arr_len=100, led_row=16, led_col=26)

                logger.debug(f"Creating Play instance for game {game_id}")
                play = Play(led_table, game_level=game.level)

                # Sweep speed scale (cells/sec = (1/group.speed) * game_level_speed).
                # Lower = slower sweep. Tune per difficulty to match real game pace.
                difficulty_speed = {"easy": 0.25, "normal": 0.4, "hard": 0.6}
                play.game_level_speed = difficulty_speed.get(game.difficulty, 0.4)

                game.play = play
                game.led_table = led_table  # expose for press input

                BLACK3 = [(0, 0, 0), (0, 0, 0), (0, 0, 0)]

                def _ensure_anim(g):
                    """Pickled groups lack breath state; init it lazily so
                    group.breath() works (shimmer effect)."""
                    if not isinstance(getattr(g, "breath_color_float", None), list) \
                            or not (g.breath_color_float and isinstance(g.breath_color_float[0], (list, tuple))):
                        col = g.color if (isinstance(g.color, (list, tuple)) and g.color
                                          and isinstance(g.color[0], (list, tuple))) else BLACK3
                        g.breath_color = [list(c) for c in col]
                        g.breath_color_float = [list(c) for c in col]
                        g.breath_switch = [True, True, True]
                    if not hasattr(g, "trigger_span_tm"):
                        g.trigger_span_tm = 0

                def _setup_level(dg, go, lvl_path):
                    """Configure game state for a freshly-loaded level. Score,
                    score2, life, session timer all PERSIST (set elsewhere)."""
                    game.dict_group = dg  # for consume-on-hit
                    # Memory mode is a FILENAME property, not a folder one: the
                    # 1P advanced tier ("--") is entirely YC01-18.led, but the
                    # 2P tier ("---") mixes plain DK01-11.ledb with memory-mode
                    # YCDK02-11.ledb in the SAME folder. So detect by whether
                    # the level's own filename (not its tier folder) starts
                    # with "YC" -- covers both 1P and 2P memory levels alike.
                    stem = os.path.basename(lvl_path).rsplit(".", 1)[0]
                    game._memory_mode = stem.upper().startswith("YC")
                    # Board length = max group end_time; board ends at min(board, session).
                    try:
                        game.board_time_sec = max(
                            (getattr(g, "end_time_sec", 0) for g in dg.values()),
                            default=1e9)
                    except Exception:
                        game.board_time_sec = 1e9
                    # Active play zone from the level (e.g. 5x9); guards input.
                    if go is not None:
                        try:
                            game.zone = (
                                int(getattr(go, "zone_row_from", 0)),
                                int(getattr(go, "zone_row_to", 16)),
                                int(getattr(go, "zone_col_from", 0)),
                                int(getattr(go, "zone_col_to", 26)),
                            )
                        except Exception:
                            game.zone = None
                    # Upgrade-only: never flip an established 2P session back to
                    # 1P. Session lock (set at marathon start) is the floor.
                    if any(getattr(g, "type", None) == Setting.SCREEN_LIGHT
                           for g in dg.values()):
                        game.multiplayer = True
                    elif getattr(game, "_session_is_2p", False):
                        game.multiplayer = True
                    # Init breath/anim state for all groups.
                    for g in dg.values():
                        try:
                            _ensure_anim(g)
                        except Exception:
                            pass

                # Per-frame callback fired by Play.update() inside Play.running().
                # By this point Play has: moved groups (deal_all_direction by
                # speed), advanced total_pass, cleared+redrawn led_table for the
                # current frame. We score presses and publish the frame.
                # Returning False makes Play.running() stop (timeout / Stop btn).
                frame_counter = {"n": 0}

                def _frame_callback(play_self, dgroup, time_pass, total_pass):
                    # total_pass is PER-LEVEL (reset each level). Session timing
                    # is wall-clock from game.session_start.
                    try:
                        session_elapsed = time.time() - game.session_start

                        # ── SESSION-END conditions (stop the whole marathon) ──
                        #   life<=0          -> result 0 (out of lives)
                        #   session timer up -> result 2 (5-min timeout)
                        if game.life <= 0:
                            time_left = game.game_time_sec - session_elapsed
                            if time_left > 10.0:
                                # Lives gone but time remains: restart same level,
                                # keep score. Session loop refills HP and replays.
                                game._restart_level = True
                                return False
                            game._session_over = True
                            game.update_state(game_over_reason="out_of_life", result=0)
                            return False
                        if (not game.running) or game.is_expired() \
                                or session_elapsed > game.game_time_sec:
                            game._session_over = True
                            game.update_state(game_over_reason="timeout", result=2)
                            return False
                        # ── LEVEL-END by TIME (advance to next level) ──
                        if total_pass > game.board_time_sec:
                            game._level_cleared = True
                            return False

                        grid = led_table.led_table

                        # 1) Determine goal colors from indicators.
                        #    goal_led  = P1; goal2_led = P2 (multiplayer only).
                        #    Memory mode: the WALL_LIGHT indicator cell doubles as
                        #    the hint tile -- pressable within its own data window.
                        hint_cells = set()
                        hint1_color_full = None   # P1's true 3-ring color (memory-mode hint blink)
                        hint2_color_full = None   # P2's true 3-ring color
                        for g in dgroup.values():
                            gtype = getattr(g, "type", None)
                            if not g.start_member:
                                continue
                            if not (g.start_time_sec <= total_pass <= g.end_time_sec):
                                continue
                            if gtype == Setting.WALL_LIGHT:
                                game.goal_color = _group_main_color(g.color)
                                if game._memory_mode:
                                    hint1_color_full = hint1_color_full or g.color
                                    for cell in g.start_member:
                                        ci = round(cell[0]); cj = round(cell[1])
                                        if 0 <= ci < led_table.led_row and 0 <= cj < led_table.led_col:
                                            hint_cells.add((ci, cj))
                            elif gtype == Setting.SCREEN_LIGHT:
                                game.goal2_color = _group_main_color(g.color)
                                game.multiplayer = True
                                if game._memory_mode:
                                    hint2_color_full = hint2_color_full or g.color
                        game.hint_cells = hint_cells

                        # 2) CLASSIFY floor (normal_led) cells:
                        #    - color == goal_color -> scoreable target
                        #    - DEDUCT_COLOR         -> penalty + consume
                        #    - red                  -> hazard (stays)
                        #    - else                 -> decor (neutral)
                        goal_cells = set()
                        goal2_cells = set()
                        red_cells = set()
                        deduct_cells = set()
                        goal_color_full = None   # true 3-ring color (for reveal paint)
                        goal2_color_full = None
                        red_color_full = None    # true 3-ring color (moving hazard, always shown)
                        deduct_color_full = None
                        gc = game.goal_color
                        gc2 = game.goal2_color
                        for g in dgroup.values():
                            sm = getattr(g, "start_member", None)
                            if not sm:
                                continue
                            if getattr(g, "type", None) != Setting.FLOOR_LIGHT:
                                continue
                            if not (g.start_time_sec <= total_pass <= g.end_time_sec):
                                continue
                            mc = _group_main_color(g.color)
                            is_deduct = _rgb_is_deduct(mc)
                            # Goal color OVERRIDES red classification:
                            # e.g. DK09 where P2 goal indicator = (254,0,0).
                            # A tile that matches P1 or P2 goal color is scored,
                            # not penalized, even if it looks red.
                            is_p1_color = (gc is not None and mc == gc)
                            is_p2_color = (gc2 is not None and mc == gc2)
                            is_red = (not is_deduct and not is_p1_color
                                      and not is_p2_color and _rgb_is_red(mc))
                            is_goal = is_p1_color and not is_deduct
                            is_goal2 = is_p2_color and not is_deduct
                            same_color_2p = (is_goal and is_goal2)
                            for cell in sm:
                                ci = round(cell[0]); cj = round(cell[1])
                                if not (0 <= ci < led_table.led_row and 0 <= cj < led_table.led_col):
                                    continue
                                if is_deduct:
                                    deduct_cells.add((ci, cj))
                                    deduct_color_full = deduct_color_full or g.color
                                elif is_red:
                                    red_cells.add((ci, cj))
                                    red_color_full = red_color_full or g.color
                                elif same_color_2p:
                                    # Checkerboard spatial split so each player
                                    # has their own distinct tiles even when
                                    # P1 and P2 share the same goal color (DK03).
                                    if (ci + cj) % 2 == 0:
                                        goal_cells.add((ci, cj))
                                        goal_color_full = goal_color_full or g.color
                                    else:
                                        goal2_cells.add((ci, cj))
                                        goal2_color_full = goal2_color_full or g.color
                                elif is_goal:
                                    goal_cells.add((ci, cj))
                                    goal_color_full = goal_color_full or g.color
                                elif is_goal2:
                                    goal2_cells.add((ci, cj))
                                    goal2_color_full = goal2_color_full or g.color
                        game._goal_color_full = goal_color_full
                        game._goal2_color_full = goal2_color_full
                        game._deduct_color_full = deduct_color_full
                        # Fresh active life at a coord (respawn / new wave) must
                        # start hidden again — drop any leftover reveal paint.
                        if game._memory_mode:
                            for cell in goal_cells | goal2_cells | deduct_cells:
                                game._clear_cell_reveal(cell)

                        # ── LEVEL COMPLETION / WAVE-SKIP ─────────────────────
                        # Unlike hoops/laser/climb/grid, hexagon's scoreable
                        # color isn't a fixed constant -- it's derived from
                        # whichever WALL_LIGHT indicator group is currently
                        # active (gc/gc2, resolved above). We use THIS frame's
                        # already-resolved gc/gc2 as the snapshot for both
                        # checks below. If the indicator later shifts to a
                        # different color, per-frame classification picks that
                        # up on its own regardless of this skip logic -- the
                        # skip only shortcuts guaranteed-empty stretches, it
                        # never gates what actually becomes scoreable.
                        # Mirrors the classification loop's own is_goal/is_goal2
                        # exclusion (a DEDUCT-colored group matching gc/gc2 by
                        # coincidence must not count as scoreable).
                        remaining_scoreable = 0
                        for g in dgroup.values():
                            if getattr(g, "type", None) != Setting.FLOOR_LIGHT:
                                continue
                            sm = getattr(g, "start_member", None)
                            if not sm:
                                continue
                            mc = _group_main_color(g.color)
                            if _rgb_is_deduct(mc):
                                continue
                            if mc == gc or mc == gc2:
                                remaining_scoreable += len(sm)

                        # Grace period (>1.5s) so the level has time to spawn
                        # its first wave. All scoreable cleared -> LEVEL done
                        # -> advance to next level (not game over).
                        if total_pass > 1.5 and remaining_scoreable == 0:
                            logger.info(f"Level cleared (all tiles): "
                                        f"score={game.score}, score2={game.score2}, "
                                        f"life={game.life}")
                            game._level_cleared = True
                            return False

                        # AUTO-JUMP: scoreable remain but none active NOW
                        # (current wave cleared, next wave is in the future).
                        # Skip dead time by advancing total_pass to the next
                        # scoreable wave's start.
                        if total_pass > 1.5 and remaining_scoreable > 0 \
                                and not goal_cells and not goal2_cells:
                            next_start = None
                            for g in dgroup.values():
                                if getattr(g, "type", None) != Setting.FLOOR_LIGHT:
                                    continue
                                sm = getattr(g, "start_member", None)
                                if not sm:
                                    continue
                                mc = _group_main_color(g.color)
                                if _rgb_is_deduct(mc):
                                    continue
                                if mc != gc and mc != gc2:
                                    continue
                                st = g.start_time_sec
                                if st > total_pass and (next_start is None or st < next_start):
                                    next_start = st
                            if next_start is not None:
                                logger.debug(f"Auto-jump: {total_pass:.1f}s -> {next_start:.1f}s")
                                play_self.total_pass = next_start
                                game.last_life_loss_time = 0.0  # reset hazard gate
                                if game._memory_mode:
                                    game._clear_all_reveals()  # no ghost paint into next wave

                        hardware_state = None
                        if USE_SERIAL_HD and _hw_led_control is not None:
                            with _hw_serial_lock:
                                hardware_state = _read_hardware_snapshot(
                                    led_table,
                                    lambda snapshot: _hw_read_sensors(
                                        _hw_layout_type, snapshot
                                    ),
                                )

                        game.process_frame_input(
                            goal_cells=goal_cells,
                            goal2_cells=goal2_cells,
                            red_cells=red_cells,
                            deduct_cells=deduct_cells,
                            hint_cells=hint_cells,
                            hardware_state=hardware_state,
                        )

                        # 2) Build display buffer from led_table (3 rings per cell).
                        led_display = [_normalize_rings(cell)
                                       for row in grid for cell in row]
                        cols = led_table.led_col

                        # 2a) MEMORY MODE paint order:
                        #   1) teal-hide unscored targets (or bright during reveal)
                        #   2) per-life revealed_colors (scored / deduct / checked empty)
                        #   3) moving red on top (danger always visible)
                        #   4) hint blink
                        #   5) white flash (below)
                        if game._memory_mode:
                            TEAL_HIDDEN = [c[:] for c in _TEAL_HIDDEN]
                            BLACK_OFF = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
                            # Each player has their OWN reveal window (separate
                            # hint presses -- see hint tile block below), not a
                            # single shared one.
                            reveal1_active = total_pass <= game._reveal_until
                            reveal2_active = total_pass <= game._reveal2_until
                            if goal_cells:
                                bright = _normalize_rings(goal_color_full) if reveal1_active else TEAL_HIDDEN
                                for (ci, cj) in goal_cells:
                                    led_display[ci * cols + cj] = bright
                            if goal2_cells:
                                bright2 = _normalize_rings(goal2_color_full) if reveal2_active else TEAL_HIDDEN
                                for (ci, cj) in goal2_cells:
                                    led_display[ci * cols + cj] = bright2
                            # Spent / checked cells stay painted for this life
                            # (do not blank after consume).
                            for (ci, cj), paint in game.revealed_colors.items():
                                led_display[ci * cols + cj] = [c[:] for c in paint]
                            # Moving RED hazard on top of reveal paint so a
                            # sweeping danger is never hidden by a checked cell.
                            if red_cells:
                                red_paint = _normalize_rings(red_color_full)
                                for (ci, cj) in red_cells:
                                    led_display[ci * cols + cj] = red_paint
                            # Hint tile itself: there's only ONE physical button
                            # (P1's and P2's indicator groups sit on the same
                            # cell, and the floor has no per-player input
                            # channel), so it alternates every _reveal_duration
                            # seconds to show whose turn it is. A press is
                            # attributed to whichever player's color is showing
                            # at that instant (see try_score_cell). 1P levels
                            # reuse the identical cadence for a consistent look,
                            # just with black standing in for "no second player".
                            if hint_cells:
                                hint_phase = int(total_pass // game._reveal_duration) % 2
                                if not game.multiplayer:
                                    hint_paint = _normalize_rings(hint1_color_full) if hint_phase == 0 else BLACK_OFF
                                elif hint_phase == 0:
                                    hint_paint = _normalize_rings(hint1_color_full)
                                else:
                                    hint_paint = _normalize_rings(hint2_color_full)
                                for (ci, cj) in hint_cells:
                                    led_display[ci * cols + cj] = hint_paint

                        # 2b) FLASH: stepped tiles blink white ~0.4s then vanish.
                        now = time.time()
                        for cell, t0 in list(game.flashes.items()):
                            el = now - t0
                            if el > 0.4:
                                game.flashes.pop(cell, None)
                                continue
                            fi, fj = cell
                            on = int(el / 0.1) % 2 == 0
                            col = [254, 254, 254] if on else [0, 0, 0]
                            led_display[fi * cols + fj] = [col[:], col[:], col[:]]

                        _now = time.time()
                        if USE_SERIAL_HD and _hw_led_control is not None and \
                                _now - getattr(game, "_hw_last_draw", 0) >= _HW_DRAW_INTERVAL:
                            with _hw_serial_lock:
                                try:
                                    _rc = led_table.led_row
                                    _cc = led_table.led_col
                                    # hexagon: cells are 3-ring [[r,g,b],[r,g,b],[r,g,b]] — pass through unchanged
                                    _ld2 = [[led_display[r * _cc + c] for c in range(_cc)] for r in range(_rc)]
                                    _hw_led_control.draw_screen_by_com(_hw_layout_type, _ld2)
                                    game._hw_last_draw = _now
                                    game._hw_draw_count = getattr(game, "_hw_draw_count", 0) + 1
                                except Exception as _hw_err:
                                    logger.warning(f"HW I/O: {_hw_err}")

                        game.update_state(
                            score=game.score,
                            score2=game.score2,
                            multiplayer=game.multiplayer,
                            time_elapsed=session_elapsed,                       # SESSION elapsed
                            time_left=max(0, game.game_time_sec - session_elapsed),  # SESSION countdown
                            life=game.life,
                            display_lives=math.ceil(game.life * 5 / game.max_life) if game.max_life else 0,
                            display_max=5,
                            game_over=False,
                            led_display=led_display,
                            grid_rows=led_table.led_row,
                            grid_cols=led_table.led_col,
                            current_level=game.current_level_id,
                            levels_cleared=game.levels_cleared,
                            phase=game.phase,
                            accepting_input=game.accepting_input,
                            phase_step=(
                                game.current_state.get("phase_step")
                                if game.phase == "countdown" else None
                            ),
                            countdown_step=(
                                game.current_state.get("countdown_step")
                                if game.phase == "countdown" else None
                            ),
                            phase_remaining_ms=(
                                game.current_state.get("phase_remaining_ms")
                                if game.phase == "countdown" else None
                            ),
                            backend_audio_active=getattr(
                                getattr(game, "_audio", None), "active", False
                            ),
                        )

                        frame_counter["n"] += 1
                        if frame_counter["n"] % 120 == 0:
                            logger.debug(f"Game {game_id}: score={game.score}, "
                                         f"t={total_pass:.1f}s")
                        # Pace ~100fps. running() is a tight loop with no sleep;
                        # wall-clock timing keeps movement correct regardless.
                        time.sleep(0.01)
                        return True
                    except Exception as cb_err:
                        logger.error(f"Frame callback error {game_id}: {cb_err}")
                        return False

                # ── SESSION LOOP ─────────────────────────────────────────────
                # Marathon through level_sequence. Score + lives + 5-min timer
                # persist across levels. Each level runs via Play.running() until
                # the callback returns False (level cleared -> advance, or session
                # over -> stop). End on life<=0, timer<=0, or sequence exhausted.
                game.session_start = time.time()
                import datetime as _dt
                game.update_state(started_at=_dt.datetime.now().isoformat(timespec="seconds"))
                if game.mode == "group":
                    game.level_sequence = _build_group_level_sequence(game.level)
                    # Sync display start level to first playlist entry
                    if game.level_sequence:
                        game.level = os.path.basename(
                            game.level_sequence[0]
                        ).rsplit(".", 1)[0]
                else:
                    game.level_sequence = _build_level_sequence(game.level)
                # 2P-ness is fixed for the whole session (chain is category-
                # locked to .led=1P or .ledb=2P). Lock it so a later level whose
                # data lacks a SCREEN_LIGHT group can't flip multiplayer False.
                # Group mode is always 1P.
                if game.mode == "group":
                    game._session_is_2p = False
                else:
                    game._session_is_2p = (
                        str(game.level_sequence[0]).endswith(".ledb")
                        if game.level_sequence else False
                    )
                game.multiplayer = game._session_is_2p
                game._end_reason = None
                logger.info(
                    f"Session: {len(game.level_sequence)} levels from "
                    f"'{game.level}' mode={game.mode or 'single'} (5-min marathon)"
                )

                if not game.level_sequence:
                    logger.warning(f"Empty level sequence; session cannot run: {game_id}")
                    game.update_state(game_over=True, game_over_reason="no_levels",
                                      time_left=0)
                    _hw_blank_floor(getattr(game, "led_table", None))
                    game.running = False
                    return

                audio = AudioManager()
                game._audio = audio
                game.update_state(backend_audio_active=audio.active)
                session_end_handled = {"done": False}

                def _run_effect_led(path, phase_name: str) -> None:
                    dg_eff, _go_eff = _load_level_file(path)
                    if not dg_eff:
                        logger.warning(f"Missing effect archive: {path}")
                        _set_phase(game, phase_name, False)
                        return
                    board_t = _effect_board_time(dg_eff)

                    def _effect_cb(play_self, dgroup, time_pass, total_pass):
                        if not game.running or total_pass >= board_t:
                            return False
                        grid_eff = led_table.led_table
                        led_display = [
                            _normalize_rings(cell)
                            for row in grid_eff for cell in row
                        ]
                        _now = time.time()
                        if USE_SERIAL_HD and _hw_led_control is not None and \
                                _now - getattr(game, "_hw_last_draw", 0) >= _HW_DRAW_INTERVAL:
                            with _hw_serial_lock:
                                try:
                                    _rc = led_table.led_row
                                    _cc = led_table.led_col
                                    _ld2 = [
                                        [led_display[r * _cc + c] for c in range(_cc)]
                                        for r in range(_rc)
                                    ]
                                    _hw_led_control.draw_screen_by_com(
                                        _hw_layout_type, _ld2
                                    )
                                    game._hw_last_draw = _now
                                except Exception as _hw_err:
                                    logger.warning(f"HW I/O (effect): {_hw_err}")
                        session_elapsed = (
                            time.time() - game.session_start
                            if game.session_start else 0.0
                        )
                        step = None
                        remaining_ms = None
                        if phase_name == "countdown":
                            step = _phase_step_from_pass(total_pass)
                            remaining_ms = _phase_remaining_ms(total_pass, step)
                        game.update_state(
                            score=game.score,
                            score2=game.score2,
                            multiplayer=game.multiplayer,
                            time_elapsed=session_elapsed,
                            time_left=max(0, game.game_time_sec - session_elapsed),
                            life=game.life,
                            display_lives=math.ceil(game.life * 5 / game.max_life)
                            if game.max_life else 0,
                            display_max=5,
                            game_over=False,
                            led_display=led_display,
                            grid_rows=led_table.led_row,
                            grid_cols=led_table.led_col,
                            current_level=game.current_level_id,
                            levels_cleared=game.levels_cleared,
                            phase=phase_name,
                            accepting_input=False,
                            phase_step=step,
                            countdown_step=step,
                            phase_remaining_ms=remaining_ms,
                            backend_audio_active=audio.active,
                        )
                        time.sleep(0.01)
                        return True

                    _set_phase(game, phase_name, False)
                    play.callback = _effect_cb
                    play.running_state = True
                    play.total_pass = 0
                    play.running(dg_eff)

                def _run_countdown():
                    audio.play_countdown_tick()
                    _run_effect_led(str(_effects_path("countdown.led")), "countdown")

                def _run_clear_hold():
                    _run_effect_led(str(_effects_path("level_clear.led")), "level_clear")
                    audio.play_stinger()

                def _run_fail_hold():
                    _run_effect_led(str(_effects_path("level_fail.led")), "level_fail")
                    audio.play_stinger()

                def _finish_session():
                    if session_end_handled["done"]:
                        return
                    session_end_handled["done"] = True
                    game.begin_level_transition()
                    audio.stop_bgm()
                    _run_clear_hold()
                    _hw_blank_floor(led_table)
                    _set_phase(game, "session_end", False)
                    state_result = game.get_state().get("result")
                    if state_result is not None:
                        final_result = state_result
                    elif game._end_reason == "timeout":
                        final_result = 2
                    elif game._end_reason:
                        final_result = 0
                    else:
                        final_result = 1
                    final_reason = (
                        game.get_state().get("game_over_reason")
                        or game._end_reason
                        or "session_end"
                    )
                    game._session_over = True
                    game.update_state(
                        game_over=True,
                        time_left=0,
                        game_over_reason=final_reason,
                        result=final_result,
                        levels_cleared=game.levels_cleared,
                        phase="session_end",
                        accepting_input=False,
                    )

                play.callback = _frame_callback
                for lvl_index, lvl_path in enumerate(game.level_sequence):
                    if game._session_over or not game.running:
                        break
                    session_elapsed = time.time() - game.session_start
                    if session_elapsed > game.game_time_sec:
                        game._session_over = True
                        game._end_reason = "timeout"
                        _finish_session()
                        break

                    lvl_id = os.path.basename(lvl_path).rsplit(".", 1)[0]

                    # ── RESTART LOOP: replay this level whenever lives hit 0 with
                    #    >10s left (score persists, HP refills). Exits on level
                    #    clear, session timeout, or true game-over (life=0, <10s).
                    while True:
                        if game._session_over or not game.running:
                            break
                        session_elapsed = time.time() - game.session_start
                        if session_elapsed > game.game_time_sec:
                            game._session_over = True
                            game._end_reason = "timeout"
                            break

                        def _setup_attempt(dg, go):
                            game.current_level_id = lvl_id
                            game.reset_for_level()
                            _setup_level(dg, go, lvl_path)
                            session_elapsed = time.time() - game.session_start
                            logger.info(
                                f"▶ Level {lvl_id}: groups={len(dg)}, "
                                f"mp={game.multiplayer}, board_time={game.board_time_sec}s, "
                                f"score={game.score}, life={game.life}, "
                                f"t_left={game.game_time_sec - session_elapsed:.0f}s"
                            )

                        def _play_attempt(dg):
                            play.callback = _frame_callback
                            play.running_state = True
                            play.total_pass = 0
                            play.running(dg)

                        _run_countdown()
                        audio.start_bgm()
                        try:
                            _run_level_attempt(
                                lvl_path,
                                led_table=led_table,
                                level_id=lvl_id,
                                setup_consumer=_setup_attempt,
                                play_consumer=_play_attempt,
                                transition_consumer=game.begin_level_transition,
                                ready_consumer=game.finish_level_transition,
                            )
                        except LevelAttemptPreparationError as prepare_err:
                            logger.warning(
                                f"Level {lvl_id} failed to reload: {prepare_err}"
                            )
                            break
                        except Exception as run_err:
                            import traceback
                            logger.warning(
                                f"Level {lvl_id} run error: {run_err}\n"
                                f"{traceback.format_exc()}"
                            )
                            game._session_over = True
                            break
                        finally:
                            audio.stop_bgm()

                        if game._session_over:
                            _finish_session()
                            break

                        if game._restart_level:
                            game._restart_level = False
                            _run_fail_hold()
                            game.refill_life_for_restart()
                            logger.info(
                                f"↻ Life restart: level={lvl_id}, score={game.score}"
                            )
                            continue

                        if game._level_cleared:
                            game.levels_cleared += 1
                            logger.info(
                                f"✓ Level {lvl_id} cleared "
                                f"(total cleared={game.levels_cleared})"
                            )
                            is_last = lvl_index >= len(game.level_sequence) - 1
                            session_elapsed = time.time() - game.session_start
                            time_left = game.game_time_sec - session_elapsed
                            if is_last or time_left <= 0:
                                _finish_session()
                            else:
                                _run_clear_hold()
                        break

                    if game._session_over or session_end_handled["done"]:
                        break

                if not session_end_handled["done"]:
                    game._session_over = True
                    state_result = game.get_state().get("result")
                    if state_result is not None:
                        final_result = state_result
                    elif game._end_reason == "timeout":
                        final_result = 2
                    else:
                        final_result = 1
                    final_reason = (
                        game.get_state().get("game_over_reason")
                        or game._end_reason
                        or "session_end"
                    )
                    logger.info(
                        f"Session over: reason={final_reason}, "
                        f"score={game.score}, levels_cleared={game.levels_cleared}"
                    )
                    game.update_state(
                        game_over=True,
                        time_left=0,
                        game_over_reason=final_reason,
                        result=final_result,
                        levels_cleared=game.levels_cleared,
                        phase="session_end",
                        accepting_input=False,
                    )
                    _hw_blank_floor(getattr(game, "led_table", None))
                game.running = False

            except Exception as e:
                logger.error(f"Game error {game_id}: {e}", exc_info=True)
                _hw_blank_floor(getattr(game, "led_table", None))
                game.running = False
                game.update_state(
                    game_over=True,
                    game_over_reason=str(e)
                )

        game.running = True   # set synchronously — clear_all() won't skip this thread
        game.thread = threading.Thread(target=_run_game, daemon=True)
        game.thread.start()

    def stop_game(self, game_id: str) -> dict:
        """Stop game and return final state"""
        game = self.get_game(game_id)
        if not game:
            return {"success": False, "error": f"Game not found: {game_id}"}

        game.begin_level_transition()
        game.running = False
        if game.thread:
            game.thread.join(timeout=5)

        # Manual stop (e.g. /logout mid-session): the level-loop's own blank
        # (session-end path in _run_game) only fires on a natural session
        # end, not a mid-level stop request — blank here too so the floor
        # doesn't stay lit with whatever was on it when Stop was pressed.
        _hw_blank_floor(getattr(game, "led_table", None))

        final_state = game.get_state()

        with self.lock:
            del self.games[game_id]

        logger.info(f"Game stopped: {game_id}")
        return {"success": True, "state": final_state}

    def cleanup_expired(self):
        """Remove expired games"""
        with self.lock:
            expired = [gid for gid, game in self.games.items() if game.is_expired()]
            for gid in expired:
                del self.games[gid]
                logger.warning(f"Game expired and removed: {gid}")

    def get_stats(self) -> dict:
        """Get manager statistics"""
        with self.lock:
            return {
                "active_games": len(self.games),
                "max_games": MAX_CONCURRENT_GAMES,
                "timeout_seconds": GAME_TIMEOUT_SECONDS
            }


# Global instance
_manager = None

def get_manager() -> GameManager:
    """Get GameManager singleton"""
    global _manager
    if _manager is None:
        _manager = GameManager()
    return _manager
