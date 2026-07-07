# On-Site Hardware Integration Guide — LED Hexagon

> **For Cursor agent:** Follow every step in order. Do not skip verification steps. Do not touch the RFID server, SQL server, or any service already running on this PC.

> **Hexagon is protocol-different from all other games.** Each floor tile has 3 concentric LED rings. Every tile sends 9 bytes (outer/mid/inner × RGB) instead of 3. The `test_hardware.py` and game code already handle this — do not change the protocol code.

---

## Game Config

| Key | Value |
|-----|-------|
| Game | LED Hexagon |
| Grid | 16 rows × 26 cols |
| COM ports | 3 (read from shelve — see Step 4) |
| Layout type | 1 (read from shelve to confirm) |
| Display var | `led_display` (cells are `[[R,G,B],[R,G,B],[R,G,B]]` — 3 rings each) |
| Zip extract dir | `C:\activerse\led-hexagon` |
| Python version | 3.10 or 3.11 |
| Server port | 8004 (adjust if already assigned differently) |

---

## Step 1 — Extract the zip

```
C:\activerse\led-hexagon\
  api\
  games\
  requirements.txt
  ...
```

Open **Command Prompt as Administrator**. Use for all remaining steps.

---

## Step 2 — Check Python

```cmd
python --version
pip --version
```

**If missing:** install Python 3.11 (winget or python.org, add to PATH). See HOOPS_ONSITE.md Step 2.

---

## Step 3 — Install dependencies

```cmd
cd C:\activerse\led-hexagon
pip install -r requirements.txt
```

---

## Step 4 — Verify shelve

```cmd
cd C:\activerse\led-hexagon\games
python -c "import shelve; db=shelve.open('setting/led_parameter',flag='r'); [print(k,'=',db[k]) for k in db.keys()]; db.close()"
```

**Expected:**
- `list_com_info` — 3 COM port entries
- `led_layout_type` — 1
- `value_high` — 16
- `value_width` — 26

---

## Step 5 — Verify COM ports

```cmd
python -c "import serial.tools.list_ports; [print(p) for p in serial.tools.list_ports.comports()]"
```

All 3 COM ports from shelve must appear.

---

## Step 6 — Run hardware diagnostic

```cmd
cd C:\activerse\led-hexagon\games
python test_hardware.py
```

**Expected:**
1. `All COM ports opened OK` (3 ports)
2. All 3 rings on every tile light **green** for 3s (each hexagon should glow solid green on all rings)
3. Step on tiles → `PRESS detected: row=X col=Y`
4. `Floor cleared. Done.`

> If only the outer ring lights but inner rings stay dark, the 3-ring protocol is working correctly — that means the hardware controller on this machine treats all 9 bytes the same way. If no rings light, check cables.

---

## Step 7 — Install frontend dependencies

```cmd
cd C:\activerse\led-hexagon\frontend
npm install
```

---

## Step 8 — Start all 3 services

**Option A — one command (recommended):**
```cmd
cd C:\activerse\led-hexagon
scripts\start-dev.bat
```

**Option B — three terminals manually:**

Terminal 1 — API:
```cmd
cd C:\activerse\led-hexagon
set USE_SERIAL_HD=1
python -m uvicorn api.main:app --host 0.0.0.0 --port 8004
```
Expected: `Hardware ready: 3 port(s), 16×26, layout=1`

Terminal 2 — ws_bridge:
```cmd
cd C:\activerse\led-hexagon
set API_PORT=8004
set WS_BRIDGE_PORT=8767
python ws_bridge.py
```

Terminal 3 — Frontend:
```cmd
cd C:\activerse\led-hexagon\frontend
npm run dev
```

---

## Step 9 — Verify sim + hardware

1. Browser → `http://localhost:5177`
2. Start a Hexagon game
3. Simulator iframe renders 16×26 hex grid (3 rings per tile)
4. Hexagon tiles light per game state (colored rings = active groups)
5. Stepping on a colored tile scores

---

## What NOT to touch

- RFID server / SQL server — leave untouched
- `games/setting/led_parameter` shelve — do not modify
- Do not flatten the 3-ring cell format — other games use `[R,G,B]` per cell, hexagon uses `[[R,G,B],[R,G,B],[R,G,B]]`. This is intentional.

---

## Troubleshooting

**Rings all same color / no ring differentiation:** normal — game logic controls which rings get which color. During `test_hardware.py` all rings are the same green intentionally.

**`led_control.draw_screen_by_com` crashes:** most likely a cell in `led_display` has wrong shape. Check game_manager.py line with `_normalize_rings` — it guards against this.

**Port 8004 in use:** `netstat -ano | findstr :8004` → `taskkill /PID <pid> /F`
