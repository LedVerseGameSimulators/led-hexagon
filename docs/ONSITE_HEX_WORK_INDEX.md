# Onsite Hex / Laser — Working Index

**Date:** 2026-09-09  
**Purpose:** Single entry point for onsite Hex (and shared Laser effects) work.

## Docs

| Doc | What it covers |
|-----|----------------|
| [Memory two reds](./ONSITE_HEX_MEMORY_TWO_REDS.md) | Moving red vs hidden deduct under teal. Paint bug. Fix checklist. |
| [Red over scoreables](./ONSITE_HEX_RED_OVER_SCOREABLE.md) | Moving red does not paint over scoreables (Hex only; Grid OK). Dense technical spec. |
| [SP level sweep](./ONSITE_HEX_SP_LEVEL_SWEEP.md) | 35 single-player levels: moving red, gc-shift, memory, board_time. |
| [2P retiling sweep](./ONSITE_HEX_2P_RETILING_SWEEP.md) | 22 multiplayer levels. Respawn = infinite retiling cause. Off like Grid, or cap at 8/tile. |
| [Effects Grid parity](./ONSITE_HEX_LASER_EFFECTS_GRID_PARITY.md) | Countdown / clear / fail — port Grid patterns to Hex + Laser. |
| [Long levels (Hex + Hoops)](./ONSITE_LONG_LEVELS_HEX_HOOPS.md) | "Level not finishing" — content too long vs code bugs. |
| [Hoops SP sweep](https://github.com/LedVerseGameSimulators/led-hoops/blob/main/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md) | Hoops archive: waves, board vs session. |

## Product facts

- Grid red-over-scoreable: **fine** — don't fix Grid.
- Hex memory has **two reds**: moving (visible) and hidden deduct (under teal, stays revealed after step).
- Hex 2P respawn (8 s) is **still on** — Grid turned it off. Causes infinite retiling on 7 levels. Fix: **off** (like Grid) **or cap at 8 respawns per tile**.
- Transition effects: shared with Grid — OK to follow Grid.
- Wave / red display: Hex-specific — use sweep docs, not blind Grid copy.
- Some "won't finish" cases are **content** (too many waves). See long-levels doc.

## Suggested order

1. **Fix moving red paint** — display priority so red covers scoreables and teal ([two reds doc](./ONSITE_HEX_MEMORY_TWO_REDS.md), [red spec](./ONSITE_HEX_RED_OVER_SCOREABLE.md))
2. **Fix 2P respawn** — off like Grid **or** max 8 per tile; smoke DK01 + DK02 ([2P sweep](./ONSITE_HEX_2P_RETILING_SWEEP.md))
3. **Effects parity** — countdown / clear / fail for Hex + Laser ([effects doc](./ONSITE_HEX_LASER_EFFECTS_GRID_PARITY.md))
4. **Pro 04 gc-shift** — wave-skip without premature level clear ([SP sweep](./ONSITE_HEX_SP_LEVEL_SWEEP.md))
5. **Onsite smoke** — Pro 03, 04, 05 then hardware overlap on one memory + one normal level

## Quick numbers

**SP (35 levels):**
- 12 / 35 (34%) moving red + scoreables
- 18 / 35 (51%) memory (YC*)
- 1 / 35 gc-shift (Pro 04)
- 35 / 35 board_time 600 s vs 300 s session

**2P (22 levels):**
- 7 respawn-dependent (infinite retiling: DK01, DK04, DK05, DK07, DK08, DK09, DK10)
- 10 memory (YCDK*)
- 22 / 22 board_time 600 s


## Grid reference (GitHub)

- Repo: https://github.com/LedVerseGameSimulators/led-grid
- Effects: https://github.com/LedVerseGameSimulators/led-grid/blob/main/api/effects_runner.py
- Game manager: https://github.com/LedVerseGameSimulators/led-grid/blob/main/api/game_manager.py
