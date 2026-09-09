# Onsite Hex — Work Handoff (pull & start here)

**Date:** 2026-09-09  
**Repo:** `led-hexagon` (`main`)  
**Pull:** `git pull origin main` then read this file.

---

## Docs in this repo

| Doc | What to fix |
|-----|-------------|
| **This file** | Order of work + external links |
| [ONSITE_HEX_MEMORY_TWO_REDS.md](./ONSITE_HEX_MEMORY_TWO_REDS.md) | Memory: **moving red** vs **hidden red** (under teal). Moving red must paint over pressable + teal. |
| [ONSITE_HEX_RED_OVER_SCOREABLE.md](./ONSITE_HEX_RED_OVER_SCOREABLE.md) | Technical: why red doesn’t cover scoreables/teal (display priority). |
| [ONSITE_HEX_SP_LEVEL_SWEEP.md](./ONSITE_HEX_SP_LEVEL_SWEEP.md) | 35 SP levels — moving red, Pro 03/04/05, memory, board_time. |
| [ONSITE_HEX_2P_RETILING_SWEEP.md](./ONSITE_HEX_2P_RETILING_SWEEP.md) | 22 multiplayer levels — infinite retiling; **disable respawn** or **cap at 8 per tile**. |
| [ONSITE_HEX_LASER_EFFECTS_GRID_PARITY.md](./ONSITE_HEX_LASER_EFFECTS_GRID_PARITY.md) | Countdown / clear / fail effects — Grid parity checklist. |
| [ONSITE_LONG_LEVELS_HEX_HOOPS.md](./ONSITE_LONG_LEVELS_HEX_HOOPS.md) | “Won’t finish” = content length vs code (Hex mostly code; Hoops mostly waves). |

---

## Suggested order

1. **Moving red paint** — cover scoreables + teal ([two reds](./ONSITE_HEX_MEMORY_TWO_REDS.md), [red spec](./ONSITE_HEX_RED_OVER_SCOREABLE.md))
2. **2P respawn** — off **or** max **8** respawns per tile ([2P sweep](./ONSITE_HEX_2P_RETILING_SWEEP.md)); smoke DK01 + DK02
3. **Effects** — countdown/clear/fail like Grid ([parity doc](./ONSITE_HEX_LASER_EFFECTS_GRID_PARITY.md))
4. **Pro 04 gc-shift** — ([SP sweep](./ONSITE_HEX_SP_LEVEL_SWEEP.md))
5. **Onsite smoke** — Pro 03, 04, 05 + one memory level

---

## Grid reference (working effects / display priority)

| What | Link |
|------|------|
| **Grid repo** | https://github.com/LedVerseGameSimulators/led-grid |
| **Clone** | `git clone https://github.com/LedVerseGameSimulators/led-grid.git` |
| **Effects runner** | https://github.com/LedVerseGameSimulators/led-grid/blob/main/api/effects_runner.py |
| **Overlap priority + HW** | https://github.com/LedVerseGameSimulators/led-grid/blob/main/api/game_manager.py (`_classify_floor_groups`, `_hw_init`, `_hw_draw_floor`) |
| **This Hex repo** | https://github.com/LedVerseGameSimulators/led-hexagon |

Grid is the reference for **effects** and **display priority** (red over scoreable). Hex keeps **3-ring**, **5×9 / 33 live cells**, and **memory two-red** behavior — do not blindly copy Grid footprint.

---

## Key local files

- `api/game_manager.py` — paint order, `_consume_cell` / `pending_respawn`, `_run_effect_led`
- `games/source/-/` Pro SP · `games/source/--/` memory YC* · `games/source/---/` 2P DK*
- Effects: `games/source/effects/{countdown,level_clear,level_fail}.led`
