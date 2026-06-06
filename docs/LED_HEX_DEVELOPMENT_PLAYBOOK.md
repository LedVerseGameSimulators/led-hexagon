# LED Hex — Development Playbook & Status

**Last updated:** 2026-06-07  
**Repo:** `/Users/apple/activerse_final_changes/led-hexagon`  
**Original source:** decompiled ledhexagon / ledplay under `games/`  
**Template for:** Hoops, Climb, Laser migrations

---

## What this game is

LED **hexagon floor** game. Each tile has **3 concentric RGB rings** (outer / mid / inner).

| Mode | Behavior |
|------|----------|
| **1P (Extra, advanced, pro)** | Step tiles matching goal indicator color → +1 |
| **2P (DK / YCDK `.ledb`)** | P1/P2 goal indicators; separate scores; 8s respawn on consumed tiles |
| **Hazards** | RED → −1 score + HP drain while standing |
| **DEDUCT** | `(254,0,48)` penalty + consume |
| **Grid** | Full floor up to 16×26; many levels use **5×9 active zone** |
| **Session** | 300s, 20 HP (from shelve) |

This repo was the **first headless migration** and remains the reference implementation for the other games.

---

## Status at a glance

| Area | Status |
|------|--------|
| Headless API + real `Play.running()` | ✅ Done |
| 3-ring display end-to-end | ✅ Done (simulator + API; `breath_color` fix in Play) |
| 67 levels (extra / basic / advanced / pro) | ✅ Done |
| Goal-color scoring, consume-on-hit | ✅ Done |
| 2P `.ledb` + respawn | ✅ Done |
| HP, session time, zone confinement | ✅ Done |
| Parallel ports (8002 / 8767 / 5175) | ✅ Done |
| Hardware serial output/input | ⏳ Pending — drivers in `games/`, mocked in API |
| Hidden-tile prompt mechanic | ❌ Not implemented |
| Wall / screen LED outputs | ❌ Off in current levels |
| RFID session timer | ❌ Not integrated |

---

## Architecture

```
led-hexagon/
├── api/
│   ├── main.py
│   ├── game_manager.py      # 3-ring led_display, breath, scoring
│   └── config.py            # API_PORT=8002
├── games/
│   ├── game_play/Play.py    # breath() + set_color_table; movement fixes
│   ├── led/led_control.py   # Serial: 9 bytes/tile (3 rings × RGB)
│   ├── game_play/game_hw.py
│   ├── source/              # Extra, ---/DK, --/YC, -/pro levels
│   └── setting/
├── frontend/
├── games/simulator/static/  # Hex canvas, cellToRings(), 3 concentric bands
├── ws_bridge.py               # 3-ring grid in WebSocket frames
└── scripts/start-dev.sh
```

### 3-ring data path

```
Play.update → group.breath() → breath_color (3 rings)
    → led_table cell = [[R,G,B],[R,G,B],[R,G,B]]
    → game_manager _normalize_rings → led_display
    → ws_bridge → simulator draws outer/mid/inner hex bands
```

**Note:** Some level files set **identical RGB on all 3 rings** (e.g. DK06) — simulator looks solid; others (Extra 17, DK03) show distinct rings.

### Data flow (simulator)

```
React → /start-game → Play.running()
    → callback → led_display (3 rings × 416 cells max)
    → ws_bridge → hex simulator
    → click → /game-input
```

### Data flow (hardware — future)

```
led_display (flatten 9 bytes/tile, outer→mid→inner, reversed phys order)
    → serial OUT
serial IN (0x0A = pressed) → state_table → scoring
```

See `HARDWARE_MODE.md` in `led-climb/docs/` (same protocol; copy/adapt to `led-hexagon/docs/` when wiring).

---

## Run locally

```bash
cd led-hexagon
./scripts/start-dev.sh
```

| Service | Port |
|---------|------|
| Frontend | 5175 |
| API | 8002 |
| ws_bridge | 8767 |

---

## What has been done

### Core (reference implementation)
- [x] FastAPI + background `Play.running()` thread
- [x] `HeadlessLedTable` with 3-ring cell support
- [x] Dependency mocks for headless import
- [x] Settings loader (`led_parameter`, `debug_parameter`)
- [x] Level ZIP → shelve load (`play_order=False` gameplay)
- [x] Zone confinement from level `zone_*`
- [x] `_normalize_rings`, goal-color scoring, red/deduct handling
- [x] 2P: `goal2_led`, checkerboard split for same-color DK levels
- [x] Leaderboard → `hex_scores` SQLite
- [x] React flow: login → select → settings → simulator → result
- [x] Web Audio synth on score / hurt

### Recent fixes
- [x] `Play.update()` uses `group.breath()` + `breath_color` (not flat `group.color`)
- [x] Removed API pulse that overwrote rings with static color
- [x] Dynamic `grid_rows` / `grid_cols` in state + ws_bridge
- [x] Parallel dev ports + Hex-only selection UI
- [x] `GAMES_ROOT` relative paths (no hardcoded clone paths)

### Git milestones
| Commit | Summary |
|--------|---------|
| `4e98857` | Initial headless stack |
| `1a8c07e` | GAMES_ROOT path fix |
| `6d1e2f0` | 3-ring rendering + parallel ports |
| `74d9264` | Ignore source `.rar` |

---

## Pending checklist

### P0 — Gameplay fidelity (from original ROADMAP)
- [ ] **cover_action disappear** — un-stepped goals vanish after `blue_hide_max_time` (replace wrong respawn if any remains)
- [ ] **DEDUCT_COLOR** distinct from plain RED (verify classifier)
- [ ] **Board result + end-fragments** — win/lose/timeout + optional `game_accomplished` board
- [ ] Verify: board advance is **time-based**, not “clear all tiles” (see `GAPS.md`)

### P1 — Hardware integration
- [ ] `HardwareDriver` or sidecar (see `led-climb/docs/HARDWARE_MODE.md`)
- [ ] `init_com` + `init_layout(led_layout_type, rows, cols, no_use)`
- [ ] Flatten 3-ring `led_display` → 9 bytes/tile serial frame `[255,255,R,G,B,...]`
- [ ] `read()` → `state_table` — test reverse-index bug noted in hardware docs (~line 202)
- [ ] Non-blocking serial reads (`com_is_block=False` for tight loop)
- [ ] Windows dongle (`encryption/yanqian.py`) or lab bypass
- [ ] On-site calibration checklist (COM, serpentine layout, ring order, sensor map)

### P2 — Kiosk / production
- [ ] Fix `database.py` scores DB path
- [ ] MySQL + RFID wedge login
- [ ] `USE_SERIAL_HD` env flag vs code constant
- [ ] Deploy scripts / systemd

### P3 — Polish
- [ ] Hidden-tile prompt / safe_color reveal mechanic
- [ ] Real MP3 audio paths
- [ ] Intro / idle video
- [ ] Level catalog docs (`LEVELS.md` — copy from climb/docs and keep in hex repo)
- [ ] Frontend `player_count` for 2P parity with Hoops

### P4 — Later
- [ ] Wall / screen lights (when levels enable them)
- [ ] Multi-board fragment chains

---

## How to continue development

### Quick-start

```bash
cd /Users/apple/activerse_final_changes/led-hexagon
./scripts/start-dev.sh
# http://localhost:5175
```

### Level buckets

| Category | Path | 2P |
|----------|------|-----|
| `extra` | `Extra/*.led` | No |
| `basic` | `source/---/*.ledb` (DK, YCDK) | Yes |
| `advanced` | `source/--/*.led` | No |
| `pro` | `source/-/*.led` | No |

### Testing 3-ring visuals

Use **Extra level 17** or **DK03** — distinct outer/mid/inner colors. DK06 uses same color on all rings by design.

### Porting pattern to other games

See `led-climb/docs/PLAYBOOK_OTHER_GAMES.md` — Hex is the template; Climb/Hoops/Laser differ in grid shape and input model.

---

## Key files

| File | Role |
|------|------|
| `api/game_manager.py` | Scoring, 3-ring led_display, mocks |
| `games/game_play/Play.py` | breath_color, movement |
| `games/simulator/static/index.html` | `cellToRings`, 3-band draw |
| `ws_bridge.py` | `_cell_to_rings` |
| `games/led/led_control.py` | Hardware serial |

---

## Related docs

| Doc | Location |
|-----|----------|
| Hardware I/O design | `../led-climb/docs/HARDWARE_MODE.md` |
| Hardware deployment steps | `HARDWARE_DEPLOYMENT.md` (this repo) |
| Known gaps / verification | `../led-climb/docs/GAPS.md` (Hex-focused) |
| Phased roadmap | `../led-climb/docs/ROADMAP.md` |
| Level catalog | `../led-climb/docs/LEVELS.md` |
| Settings reference | `../led-climb/docs/SETTINGS.md` |
| Hoops playbook | `../led-hoops/docs/HOOPS_DEVELOPMENT_PLAYBOOK.md` |

*Consider copying HARDWARE_MODE.md and LEVELS.md into this repo’s `docs/` when Hex becomes the active hardware target.*

---

*Update this document when closing pending items.*
