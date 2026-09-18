# LED Hexagon — Operator Guide

For studio staff. No coding required.

---

## Start

1. Double-click **`START_GAME.bat`** in this folder.
2. Wait until you see **LED Hexagon is running (HARDWARE)**.
3. The API window must say **HARDWARE MODE ON**.
4. The browser opens in **fullscreen kiosk** at **http://127.0.0.1:5177/**.
5. **Ctrl+Shift+K** exits fullscreen only (the game keeps running). Use **`STOP_GAME.bat`** to stop the game.
6. Leave the minimized service windows open while playing.
7. When a game starts, the **physical floor** and the on-screen sim both run.

**Engineers / debug:** use `scripts\start-dev.bat` (normal browser, Vite dev server — not kiosk).

---

## Play

1. On the login screen, scan a card **or** choose **Play as Guest**.
2. Pick a level and start.
3. Use **one browser tab only**.
4. Step on the lit tiles to score.

---

## Stop

1. Double-click **`STOP_GAME.bat`**.
2. Wait until it says the game stopped.
3. Close any leftover black windows if they are still open.

---

## Before you start

- Floor USB cable(s) plugged in (this setup uses **COM9** for 33 tiles)
- This PC is the Hexagon machine
- Prefer **Run as administrator** if Windows blocks COM / serial access

Do **not** edit files inside the `games\setting` folder.

---

## Common fixes

| Problem | What to do |
|--------|------------|
| Start says Python not found | Ask tech to install Python 3.11 with "Add to PATH". |
| Start says Node.js not found | Ask tech to install Node.js LTS. |
| Start says floor settings missing | Ask tech to copy `games\setting\` files onto this PC (or ensure `D:\ledhexagonv010109\...` is available). |
| Browser page blank / won't load | Wait 10–15 seconds after start, then refresh. Or run `STOP_GAME.bat`, then `START_GAME.bat` again. |
| Floor LEDs dark but game runs in browser | Check USB cable to the floor controller. Run start again. |
| Two games fighting each other / freeze | Close all browser tabs, run `STOP_GAME.bat`, then start once with one tab. |
| Need to reboot game mid-day | `STOP_GAME.bat` → wait → `START_GAME.bat`. |
| Tiles stay lit after stop | Start again, use Stop / Logout in the UI, then `STOP_GAME.bat`. |
| Wrong COM / no floor | Ask tech — settings live in `games\setting` (copied from the original install on `D:\`). |

---

## What the three windows are

After start you may see three minimized command windows. Leave them open while playing:

| Window title | Role |
|--------------|------|
| **LED Hexagon API** | Floor engine (port 8004) |
| **LED Hexagon Bridge** | Links engine ↔ UI (port 8767) |
| **LED Hexagon UI** | Web game screen (port 5177) |

Closing them by hand also stops the game; prefer **`STOP_GAME.bat`**.

---

## Packaging / updates

- Download the latest release zip from **GitHub Releases** (operators do not need git).
- Extract the zip to a folder on the PC.
- Double-click **`LED Hexagon.exe`** (or **`START_GAME.bat`** — both start the game the same way).
- **First time on a new PC:** a technician runs **`SETUP_FIRST_TIME.bat`** once to install Python packages and frontend dependencies. The PC must already have **Python 3.11**, **Node.js LTS**, and **Chrome or Edge** installed.
- **Updates:** stop the game with `STOP_GAME.bat`, then replace the folder with the new release zip (or drop in the new `LED Hexagon.exe`).

## Notes

- Port used by the game UI: **5177**.
- These buttons only **run and stop** LED Hexagon on this PC.
- They do **not** change Wi‑Fi / LAN / RFID server settings.

---

## Need tech help?

Say what you saw (error text or "tiles dark / browser blank") and whether `START_GAME.bat` finished or stopped with an error.
