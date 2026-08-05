# LED Hexagon — Operator Guide

For studio staff. No coding required.

---

## Daily use (3 steps)

1. **Double-click `START_GAME.bat`**
   - Checks Python / Node
   - Turns on **hardware mode** (real floor tiles)
   - Starts the floor engine, bridge, and game UI
   - Opens the browser automatically

2. **Play in the browser** → [http://localhost:5177](http://localhost:5177)
   - Choose **Guest** (or card login if RFID is set up)
   - Pick a level and start
   - Step on the lit tiles to score

3. **When finished, double-click `STOP_GAME.bat`**
   - Shuts down all three services
   - Frees the ports so the next start is clean

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
| Browser does not open / blank page | Wait 20–30 seconds, then open [http://localhost:5177](http://localhost:5177) yourself |
| “Python was not found” | Ask tech to install Python and tick “Add to PATH” |
| “Node.js was not found” | Ask tech to install Node.js LTS from nodejs.org |
| Tiles do not light | Run `STOP_GAME.bat`, unplug/replug USB, run `START_GAME.bat` again |
| “Port already in use” | Run `STOP_GAME.bat`, wait 5 seconds, then `START_GAME.bat` |
| Tiles stay lit after stop | Start again, use Stop / Logout in the UI, then `STOP_GAME.bat` |
| Wrong COM / no floor | Ask tech — settings live in `games\setting` (copied from the original install on `D:\`) |

---

## What the three windows are

After start you may see three black command windows. Leave them open while playing:

| Window title | Role |
|--------------|------|
| **LED Hexagon API** | Floor engine (port 8004) |
| **LED Hexagon Bridge** | Links engine ↔ UI (port 8767) |
| **LED Hexagon UI** | Web game screen (port 5177) |

Closing them by hand also stops the game; prefer **`STOP_GAME.bat`**.

---

## Need tech help?

Say what you saw (error text or “tiles dark / browser blank”) and whether `START_GAME.bat` finished or stopped with an error.
