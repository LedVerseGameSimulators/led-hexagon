"""
run_simulator.py — Start the LED Hex game with the web simulator active.

What this does
──────────────
1. Disables all serial hardware (USE_SERIAL_HD = False)
   → No Windows COM ports needed, runs clean on macOS
2. Patches gui2.gui_led_table_editor.LedTable with SimulatorLedTable
   → LED color output is routed to the browser instead of physical tiles
   → Browser clicks are routed back as tile-press input
3. Starts the FastAPI / WebSocket server in a background thread
4. Launches the real game GUI (tkinter) — or the demo loop if assets are missing

Usage
─────
  cd /Users/apple/parallel-work/ledhexagon_clone
  source .venv/bin/activate

  python run_simulator.py           # real game with simulator
  python run_simulator.py --demo    # animated demo loop only (no game files needed)

  Then open http://127.0.0.1:8765 in Safari or Chrome
"""

import sys
import os
import time
import math
import types
import platform

# ── PyInstaller bundle path fix ───────────────────────────────────────────────
# When frozen by PyInstaller, all bundled data lives under sys._MEIPASS.
# We change the working directory so relative paths (photo/, audio/, source/,
# etc.) resolve correctly whether running from source or as a .exe.
if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle
    _bundle_dir = sys._MEIPASS
    os.chdir(_bundle_dir)
# ─────────────────────────────────────────────────────────────────────────────
import subprocess

# ── 0. Ensure project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root so relative paths (./setting, ./source, ./photo) work
os.chdir(PROJECT_ROOT)

# ── 0b. Platform-specific fixes ───────────────────────────────────────────────
_IS_MAC = platform.system() == "Darwin"
_IS_WIN = platform.system() == "Windows"

if _IS_MAC:
    # pygame/SDL2 on macOS hijacks NSApplication, breaking tkinter.
    # SDL_VIDEODRIVER=dummy stops SDL touching the display system entirely.
    # Audio and game logic are unaffected.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# ── 0c. Fix PIL ImageTk on macOS when SDL is loaded ──────────────────────────
# On macOS, SDL2 breaks the _imagingtk C bridge. Use PNG-via-BytesIO instead.
# On Windows, ImageTk works fine natively — skip this patch.
if _IS_MAC:
    def _patch_imagetk():
        import io, base64, tkinter as _tk
        from PIL import ImageTk as _itk, Image as _img

        class _SafePhotoImage(_tk.PhotoImage):
            """Drop-in for ImageTk.PhotoImage that uses native Tk PNG support."""
            def __init__(self, image=None, **kw):
                if image is not None:
                    buf = io.BytesIO()
                    pil_img = image if hasattr(image, 'save') else _img.fromarray(image)
                    if pil_img.mode not in ('RGBA', 'RGB', 'L'):
                        pil_img = pil_img.convert('RGBA')
                    pil_img.save(buf, format='PNG')
                    super().__init__(data=base64.b64encode(buf.getvalue()))
                else:
                    super().__init__(**kw)

        _itk.PhotoImage = _SafePhotoImage

    _patch_imagetk()
    del _patch_imagetk

# ── 0d. Substitute unavailable fonts ─────────────────────────────────────────
# STKaiti is a Chinese font not installed on macOS (triggers 66 MB download dialog).
# On Windows it IS installed (part of Chinese Windows). On macOS use PingFang SC.
def _patch_fonts():
    import tkinter.font as _tkfont
    import tkinter as _tk

    # macOS: STKaiti not present → use built-in PingFang SC
    # Windows: STKaiti/SimHei/etc. are present → no substitution needed
    if _IS_MAC:
        _FONT_MAP = {
            "STKaiti": "PingFang SC",
            "SimHei":  "PingFang SC",
            "STHeiti": "PingFang SC",
            "STSong":  "PingFang SC",
            "KaiTi":   "PingFang SC",
        }
    else:
        _FONT_MAP = {}   # Windows has these fonts natively

    if not _FONT_MAP:
        return  # nothing to patch

    _orig_font_init = _tkfont.Font.__init__

    def _safe_font_init(self, root=None, font=None, name=None, exists=False, **options):
        if "family" in options:
            options["family"] = _FONT_MAP.get(options["family"], options["family"])
        if isinstance(font, (list, tuple)) and len(font) >= 1:
            font = list(font)
            font[0] = _FONT_MAP.get(font[0], font[0])
            font = tuple(font)
        _orig_font_init(self, root=root, font=font, name=name, exists=exists, **options)

    _tkfont.Font.__init__ = _safe_font_init

    _orig_create_text = _tk.Canvas.create_text

    def _safe_create_text(self, *args, **kw):
        if "font" in kw:
            f = kw["font"]
            if isinstance(f, (list, tuple)) and len(f) >= 1:
                f = list(f)
                f[0] = _FONT_MAP.get(f[0], f[0])
                kw["font"] = tuple(f)
            elif isinstance(f, str) and f in _FONT_MAP:
                kw["font"] = _FONT_MAP[f]
        return _orig_create_text(self, *args, **kw)

    _tk.Canvas.create_text = _safe_create_text

    # ttk.Style.configure() is used by gui_ui.py for the "BACK" button font.
    # It passes font as a keyword argument, e.g. font=("STKaiti", 24, "bold").
    import tkinter.ttk as _ttk
    _orig_style_configure = _ttk.Style.configure

    def _safe_style_configure(self, style, query_opt=None, **kw):
        if "font" in kw:
            f = kw["font"]
            if isinstance(f, (list, tuple)) and len(f) >= 1:
                f = list(f)
                f[0] = _FONT_MAP.get(f[0], f[0])
                kw["font"] = tuple(f)
            elif isinstance(f, str) and f in _FONT_MAP:
                kw["font"] = _FONT_MAP[f]
        return _orig_style_configure(self, style, query_opt, **kw)

    _ttk.Style.configure = _safe_style_configure

    # Also patch tkinter.Label and tkinter.Button font= kwarg
    for _widget_cls in (_tk.Label, _tk.Button, _tk.Entry, _tk.Text):
        _orig_init = _widget_cls.__init__

        def _make_patched_init(orig):
            def _patched_widget_init(self, master=None, cnf=None, **kw):
                if cnf is None:
                    cnf = {}
                for source in (kw, cnf):
                    if "font" in source:
                        f = source["font"]
                        if isinstance(f, (list, tuple)) and len(f) >= 1:
                            f = list(f)
                            f[0] = _FONT_MAP.get(f[0], f[0])
                            source["font"] = tuple(f)
                        elif isinstance(f, str) and f in _FONT_MAP:
                            source["font"] = _FONT_MAP[f]
                return orig(self, master, cnf, **kw)
            return _patched_widget_init

        _widget_cls.__init__ = _make_patched_init(_orig_init)

_patch_fonts()
del _patch_fonts

# ── 0e. Stub video players ────────────────────────────────────────────────────
# On macOS: VLC (use_dll/exe/vlc) is a Windows binary → doesn't exist → stub.
# On Windows: VLC and moviepy/pygame video work fine → keep the real classes.
import threading as _threading

class _NoOpVideo(_threading.Thread):
    """Silent no-op replacement for IdleVideoPlay and TkVideoPlayNew."""
    daemon = True
    running_ending = True   # GuiCountDown loops on this; True = already done, skip immediately
    def __init__(self, *a, **kw):
        super().__init__(daemon=True)
    def run(self):              pass
    def start(self):            pass
    def stop_running(self):     pass
    def reset(self):            pass
    def close(self):            pass
    def close_video(self, *a):  pass
    def join(self, *a, **kw):   pass

if _IS_MAC:
    import util.idle_video_play       as _idle_mod
    import util.gm_introduce_video_new as _vid_mod
    _idle_mod.IdleVideoPlay  = _NoOpVideo
    _vid_mod.TkVideoPlayNew  = _NoOpVideo
    del _idle_mod, _vid_mod
del _threading

# ── 1. Kill serial hardware BEFORE any game imports ──────────────────────────
#      Must happen before model.setting is imported by anything else.
from model.setting import Setting, Color
Setting.USE_SERIAL_HD = False
Setting.FULL_SCREEN = False

# ── 2. Install SimulatorLedTable as the global LedTable ──────────────────────
#      game_running.py does:  from gui2.gui_led_table_editor import LedTable
#      We intercept that import by pre-loading the module with our class.
import simulator.led_table_sim as _sim_mod
from gui2.gui_table_editor import TableEditor  # real stub

_fake_led_table_mod = types.ModuleType("gui2.gui_led_table_editor")
_fake_led_table_mod.LedTable = _sim_mod.SimulatorLedTable
sys.modules["gui2.gui_led_table_editor"] = _fake_led_table_mod

# ── 3. Start the WebSocket server ────────────────────────────────────────────
from simulator.ws_server import SimulatorServer

server = SimulatorServer(host="127.0.0.1", port=8765)
server.start()

# Give the server a moment to bind its port
time.sleep(0.6)

# Open browser automatically
try:
    url = "http://127.0.0.1:8765"
    if platform.system() == "Darwin":
        subprocess.Popen(["open", url], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    elif platform.system() == "Windows":
        subprocess.Popen(["start", url], shell=True, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", url], stderr=subprocess.DEVNULL)
except Exception:
    pass

# ── 4a. Demo loop (animated pattern, no game files needed) ───────────────────

_DEMO_COLORS = [
    Color.RED, Color.GREEN, Color.BLUE,
    (254, 165, 0),   # orange
    (138, 43, 226),  # violet
    (0, 206, 209),   # cyan
    (255, 20, 147),  # pink
]
_DEMO_CX, _DEMO_CY = 8, 13  # centre of 16×26 grid


def _demo_wave_color(r: int, c: int, t: float) -> list:
    dist = math.sqrt((r - _DEMO_CX) ** 2 + (c - _DEMO_CY) ** 2)
    intensity = max(0.0, math.sin(dist * 0.6 - t * 3.0))
    base = _DEMO_COLORS[int(dist + t * 0.5) % len(_DEMO_COLORS)]
    return [int(ch * intensity * 0.85) for ch in base]


def _demo_apply_pressed(table) -> None:
    state = table.get_state_table()
    for r in range(table.rows):
        for c in range(table.cols):
            if state[r][c]:
                table.led_table[r][c] = [254, 254, 254]
                state[r][c] = False


def run_demo_loop():
    """Animated colour demo — verifies the browser UI without needing game files."""
    from simulator.led_table_sim import SimulatorLedTable

    print("[Demo] Animated demo loop running.")
    print("[Demo] Open http://127.0.0.1:8765 in your browser.")
    print("[Demo] Click tiles to simulate stepping on them (they flash white).")
    print("[Demo] Ctrl+C to stop.\n")

    table = SimulatorLedTable(root=None, wall_light_arr_len=0, led_row=16, led_col=26)

    try:
        while True:
            t = time.time()
            for r in range(table.rows):
                for c in range(table.cols):
                    table.led_table[r][c] = _demo_wave_color(r, c, t)
            _demo_apply_pressed(table)
            table.draw_led_color()
            time.sleep(0.05)  # ~20fps
    except KeyboardInterrupt:
        print("\n[Demo] Stopped.")


# ── 4b. Real game ─────────────────────────────────────────────────────────────

def run_real_game():
    """
    Launch the full tkinter game UI with the simulator active.

    The SimulatorLedTable is already installed (step 2), so:
      • LED color writes → WebSocket → browser hex grid
      • Browser clicks → WebSocket → tile-press input to game logic
    """
    # Verify the minimum required data folders exist
    missing = [d for d in ["setting", "source", "photo"] if not os.path.isdir(d)]
    if missing:
        print(f"[Game] Missing folders: {missing}")
        print("[Game] Falling back to demo mode.")
        run_demo_loop()
        return

    print("[Game] Launching real game with web simulator.")
    print("[Game] Open http://127.0.0.1:8765 in your browser.")
    print("[Game] The hex grid will show actual game colors. Click tiles to play.\n")

    try:
        import gui.gui_game_main as _gmm

        # These two methods create Tkinter widgets from a background thread.
        # Tkinter is NOT thread-safe on macOS (causes SIGTRAP/EXC_BREAKPOINT).
        # They only draw decorative header labels, so we can safely skip them.
        _gmm.GuiMain.ui_init_game_level_title = lambda *a, **kw: None
        _gmm.GuiMain.ui_init_game_introduce_title = lambda *a, **kw: None

        GuiMain = _gmm.GuiMain
        GuiMain()  # creates tkinter root and runs mainloop() internally

    except Exception as e:
        import traceback
        print(f"\n[Game] Launch failed: {e}")
        print(traceback.format_exc())
        print("[Game] Falling back to demo mode.")
        run_demo_loop()


# ── 5. Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo_loop()
    else:
        run_real_game()
