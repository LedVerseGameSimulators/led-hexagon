# Debugging on Windows — LED Hex Game

This file gives the Cursor AI agent full context to start debugging immediately.
**Paste this into the Cursor chat:** `Read @DEBUGGING_WINDOWS.md and help me debug this error: [paste error here]`

---

## Step 1 — Run from source (not the .exe)

```bat
setup_and_run_windows.bat
```

This gives you full Python tracebacks. Copy the red error text and paste it into Cursor chat.

---

## Step 2 — Common errors and exact fixes

### `ModuleNotFoundError: No module named 'X'`
```bat
.venv\Scripts\activate
pip install X
```
Re-run after installing.

---

### `pygame.error: No video mode has been set` or `SDL_VIDEODRIVER` error
Open `run_simulator.py` and make sure the `SDL_VIDEODRIVER` block **only** runs on macOS:
```python
if platform.system() == "Darwin":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
```
On Windows this block must NOT execute. Check it is guarded by `if platform.system() == "Darwin"`.

---

### `FileNotFoundError: photo/ledplay.ico` or any asset path
The game uses relative paths. You must run from inside the `ledhexagon_clone` folder:
```bat
cd ledhexagon_clone
python run_simulator.py
```
The `setup_and_run_windows.bat` script already does this. If running manually, `cd` first.

---

### `sqlite3.OperationalError: unable to open database file`
The `data/` folder is missing. Create it:
```bat
mkdir data
```
The code also auto-creates it via `os.makedirs` in `tourist_record/tourist_record_main.py`.

---

### `TclError` or Tkinter window crashes immediately
- On Windows this is usually a display driver issue.
- Try: right-click `setup_and_run_windows.bat` → "Run as administrator"
- Or set environment variable before running: `set TCL_LIBRARY=` (clear it)

---

### `ImportError: DLL load failed` for pygame or similar
Install Visual C++ Runtime:
- Download from https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and reboot, then retry.

---

### Port 8765 already in use
```bat
netstat -ano | findstr 8765
taskkill /PID <pid_number> /F
```
Then run the game again.

---

### Game starts but browser simulator shows nothing at http://127.0.0.1:8765
- Open Windows Firewall → allow Python through private networks
- Or try http://localhost:8765 instead

---

### Antivirus blocking the app (silent crash, no error)
- Windows Defender may quarantine PyInstaller `.exe` files.
- Add the entire `ledhexagon_clone` folder to Windows Defender exclusions:
  Settings → Windows Security → Virus & Threat Protection → Exclusions → Add folder.

---

## Step 3 — Check these files first when debugging

| Symptom | File to check |
|---|---|
| Crash on startup | `run_simulator.py` |
| Tkinter window issues | `gui/gui_game_main.py` |
| Game not loading / blank screen | `gui/gui_game.py` |
| Score / timer wrong | `gui/gui_editor_game.py`, `gui/gui_editor_game2.py` |
| LED tiles not showing | `simulator/bridge.py`, `simulator/static/index.html` |
| Database error | `tourist_record/tourist_record_main.py` |
| Hardware / serial error | `model/setting.py` → set `USE_SERIAL_HD = False` |

---

## Step 4 — Environment info to include when asking for help

Run this and paste the output into chat:
```bat
python --version
python -c "import pygame; print('pygame', pygame.__version__)"
python -c "import fastapi; print('fastapi ok')"
python -c "import tkinter; print('tkinter ok')"
echo %OS% %PROCESSOR_ARCHITECTURE%
```

---

## Project structure (quick reference)

```
ledhexagon_clone/
├── run_simulator.py          ← START HERE, entry point
├── setup_and_run_windows.bat ← one-click run on Windows
├── model/setting.py          ← USE_SERIAL_HD = False  ← important
├── gui/
│   ├── gui_game_main.py      ← main Tkinter window
│   ├── gui_game.py           ← game logic + scoring
│   ├── gui_editor_game.py    ← game loop type 1
│   └── gui_editor_game2.py   ← game loop type 2 (co-op)
├── simulator/
│   ├── bridge.py             ← LED data → browser
│   ├── ws_server.py          ← FastAPI on port 8765
│   └── static/
│       ├── index.html        ← browser LED grid
│       └── leaderboard.html  ← scores page
├── tourist_record/
│   └── tourist_record_main.py ← SQLite DB
├── source/                   ← 57 game level zips
├── photo/, audio/, video/    ← assets
└── data/                     ← auto-created, holds local_data.db
```
