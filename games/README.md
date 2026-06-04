# Ledhexagon Clone — Setup & Run Guide

Interactive LED floor/wall game controller for 6 game rooms.
Recovered and customized from the original manufacturer's build.

---

## Requirements

- **Windows 10/11** (64-bit) — required for USB-Serial COM port hardware
- **Python 3.7.x** — must match original build version
  - Download: https://www.python.org/downloads/release/python-379/
  - During install: check "Add Python to PATH"

---

## Quick Setup (Windows)

### 1. Install Python 3.7
Download and install Python 3.7.9 from python.org.

### 2. Install dependencies
Open Command Prompt in this folder and run:
```
pip install -r requirements.txt
```

### 3. Configure hardware (COM ports)
Edit `setting/led_parameter.dat` via the built-in Settings UI, or run the app
and go to Settings to assign your COM ports to LED zones.

Default mapping (change to match your PC's device manager):
- COM4 → Floor light zone 1
- COM5 → Floor light zone 2
- COM6 → Floor light zone 3
- COM7 → Wall light
- COM8 → Screen light 1
- COM9 → Screen light 2

### 4. Run the app
```
python main.py
```

---

## Folder Structure

```
ledhexagon_clone/
├── main.py              ← Entry point — run this
├── requirements.txt     ← Python dependencies
│
├── gui/                 ← All UI windows (Tkinter)
│   ├── gui_game_main.py ← Main game room controller
│   ├── gui_game.py      ← Individual game runner
│   ├── gui_setting.py   ← Hardware settings UI
│   ├── gui_editor_game.py ← Game pattern editor
│   └── language.py      ← All text strings (edit here to translate)
│
├── game_play/           ← Core game logic
│   ├── game_running.py  ← Main game loop
│   ├── Play.py          ← Game play orchestrator
│   └── game_util.py     ← Utilities
│
├── led/                 ← LED hardware layer
│   ├── led_control.py   ← Sends color commands via serial
│   ├── communication.py ← Serial port wrapper
│   └── position_convert.py ← Grid coordinate mapping
│
├── model/               ← Data structures
│   ├── setting.py       ← Constants (grid size, colors, levels)
│   ├── game.py          ← Game definition object
│   └── group.py         ← LED group (pattern/movement)
│
├── encryption/
│   └── yanqian.py       ← Dongle check (bypassed — always returns True)
│
├── source/              ← Game definition files (.led / .ledb)
│   ├── -/               ← Standard games (00.led to 16.led, YC01-YC18)
│   ├── --/              ← Variant games
│   └── ---/             ← Additional variants
│
├── audio/               ← Sound effects and music (MP3/MP4)
├── photo/               ← UI images and backgrounds
├── setting/             ← Hardware config (shelve files)
├── data/                ← SQLite score database
└── log/                 ← Runtime logs
```

---

## How to Customize

### Change game text / language
Edit `gui/language.py` — all Chinese strings are defined there.

### Add a new game
1. Use the built-in Game Editor (accessible from Settings)
2. Or create a `.led` file manually using the `model/game.py` structure
3. Drop it into `source/-/`

### Change LED grid size
Edit `model/setting.py`:
```python
SCREEN_ROW = 16   # change rows
SCREEN_COL = 26   # change columns
```

### Change UI images
Replace files in `photo/` — keep the same filenames.

### Change sounds
Replace MP3 files in `audio/` — keep the same filenames.

### Change network settings
The app listens on UDP for remote commands. Default: `192.168.225.50`
Edit in `setting/` config via the Settings UI.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named 'pygame'` | Run `pip install -r requirements.txt` |
| `COM port not found` | Open Device Manager, check which COM ports are assigned to USB-Serial adapters |
| `Serial open error` | Make sure no other app has the COM port open |
| App won't start | Check `log/led_play_runtime.log` for error details |
| Black screen | Check that `photo/` folder has all images |

---

## Repackaging to .exe (optional)

To distribute as a single .exe again:
```
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```
