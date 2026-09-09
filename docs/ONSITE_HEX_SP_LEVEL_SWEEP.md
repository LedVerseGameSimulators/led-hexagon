# Onsite SP Level Sweep — LED Hexagon

> **Generated:** 2026-09-09  
> **Scope:** Single-player levels under `games/source/-` (pro) and `games/source/--` (advanced).  
> **Out of scope (noted):** `games/source/---` (2P `.ledb`), `games/source/effects/`, `games/source_group/` (10 group-mode `.led`), `games/Extra/` (dev/test).

---

## Method

### How levels are loaded

Same pipeline as `tests/test_effects_session_loop.py` (`load_level_archive` fixture) and `api/game_manager._load_level_file()`:

1. Open `.led` / `.ledb` as a **zip** archive.
2. Extract to a temp directory.
3. Walk for `game_file.dat` / `game_file.db`.
4. **`shelve.open("game_file")`** → read `dict_group` (floor/wall groups) and `para_key_game` (zone, metadata).

Analysis script: offline Python sweep over all 35 SP files (no server, no Play loop). Classification mirrors `api/game_manager.py` frame logic:

| Field | Source |
|-------|--------|
| `goal_color` (gc) | Active `goal_led` (`WALL_LIGHT`) group at probe time |
| Scoreable | `normal_led` floor group whose main ring color == current gc, not red, not DEDUCT |
| Moving red | `normal_led`, `speed != 0`, main color red `(254,0,0)` |
| Memory mode | Filename stem starts with `YC` (per `_setup_level`, line ~1288) |
| `board_time` | `max(group.end_time_sec)` across all groups |

### Category definitions

| Cat | Name | Detection rule |
|-----|------|----------------|
| **A** | Moving red + scoreables | ≥1 moving-red floor group time-overlaps an active scoreable floor group under the same gc phase. Sub-flag `blank+red`: moving red still active after last scoreable in phase ends (post-clear hazard). |
| **B** | Large inter-wave gaps ≥10s | **Primary:** dead gap (scoreable window end → next window start) ≥10s within a gc phase. **Secondary:** wave **start cadence** (consecutive scoreable `start_time_sec` deltas) ≥10s when waves overlap continuously (pro stagger pattern). |
| **C** | Multi-color / gc-shift (premature-clear risk) | Goal indicator (`goal_led`) **color changes** mid-level (gc at t₁ ≠ gc at t₂), or simultaneous scoreable floor colors under one gc. Triggers wave-skip / remaining_scoreable logic edge cases. |
| **D** | Memory-mode levels | `YC*.led` in `--` tier (`_memory_mode = True`). |
| **E** | `board_time > 300s` | Level timeline exceeds 300s session cap (session ends at 300s regardless). |
| **F** | Pro 03 / 04 / 05 | Explicit callout rows for onsite smoke levels. |

---

## Summary

| Category | Count | % of 35 SP | Severity for onsite |
|----------|------:|----------:|---------------------|
| **Total SP levels** | 35 | 100% | — |
| **A** Moving red + scoreables | 12 | 34.3% | High — display + blank-after-score risk |
| **B** Inter-wave gap ≥10s | 5 (cadence) / 0 (dead) | 14.3% / 0% | Low — auto-jump mitigates dead time |
| **C** gc-shift / multi-color | 1 | 2.9% | Medium — Pro 04 only |
| **D** Memory mode | 18 | 51.4% | High — teal/reveal/hint stack |
| **E** board_time > 300s | 35 | 100% | Info — session timer always wins |

**Overlap note:** Categories are not mutually exclusive. Example: `YC09` is both **A** and **D**.

---

## Category A — Moving red + scoreables (12 levels, 34.3%)

**Risk:** Moving red overlaps active scoreables. In normal mode, display has no red-over-goal priority (`ONSITE_HEX_RED_OVER_SCOREABLE.md`). After scoring, non-memory tiles blank but moving red may still sweep the cell (blank+red flash). No levels showed post-clear-only red without overlap (blank+red sub-flag = 0/35).

### Pro tier (`-`, 6/17)

`03`, `05`, `06`, `09`, `11`, `15`

### Advanced tier (`--`, 6/18)

`YC09`, `YC10`, `YC12`, `YC14`, `YC16`, `YC18`

### Clean pro levels (no A–D flags)

`00`, `01`, `02`, `07`, `08`, `10`, `12`, `13`, `14`, `16` — best baselines for regression.

---

## Category B — Inter-wave gaps ≥10s

### Dead gaps (scoreable window end → next start)

**0 / 35 (0%).** All SP levels keep scoreable floor groups overlapping continuously within each gc phase (t=0–600). Auto-jump in `game_manager` advances `total_pass` to the next wave start when the current wave is cleared.

### Start cadence gaps (consecutive scoreable `start_time_sec` ≥10s apart)

**5 / 35 (14.3%)** — all pro tier, staggered wave design:

| Level | Max cadence | Pattern |
|-------|------------|---------|
| `00` | 40s | 0 → 40 → 80 → 120 … |
| `01` | 30s | 0 → 30 → 60 → 90 … |
| `02` | 30s | same |
| `06` | 20s | 0 → 20 → 40 … (+ moving red, **A**) |
| `08` | 60s | single 60s beat |

Advanced (`YC*`) and most other pro levels: **no stagger** — all scoreable groups run t=0–600 simultaneously, so cadence metric is N/A.

---

## Category C — gc-shift / multi-color (1 level, 2.9%)

| Level | Detail |
|-------|--------|
| **`-/04` (Pro 04)** | Goal indicator switches **cyan → magenta at t=60s**. Only SP level with a mid-level gc change. Wave-skip and `remaining_scoreable` checks use per-frame gc; risk of premature level-clear when old-color groups remain in `dict_group` but new gc no longer matches. |

No SP levels had simultaneous multi-color scoreable floor groups under a single gc window.

---

## Category D — Memory mode (18 levels, 51.4%)

Entire advanced tier: **`YC01`–`YC18`** (`games/source/--/YC*.led`).

Mechanics enabled by code (not level file flag): teal camouflage, `_mark_revealed` persist, hint-tile blink, red overlay pass in memory paint stack. **6 of 18** also hit category **A** (moving red): `YC09`, `YC10`, `YC12`, `YC14`, `YC16`, `YC18`.

---

## Category E — board_time > 300s (35/35, 100%)

Every SP level: **`board_time_sec = 600`**. Session is capped at **300s** (`game_time_sec`). Level never runs to board end in a normal session; level advance is driven by clearing scoreables (or life/session end), not board timeout.

---

## Pro 03 / 04 / 05 callout (Category F)

| | **Pro 03** (`-/03.led`) | **Pro 04** (`-/04.led`) | **Pro 05** (`-/05.led`) |
|---|--------------------------|--------------------------|--------------------------|
| **Memory** | No | No | No |
| **board_time** | 600s | 600s | 600s |
| **Groups** | 204 | 303 | 303 |
| **Goal indicators** | 201 windows | 300 windows | 300 windows |
| **Moving red** | 1 group | 0 | 1 group |
| **A** red+scoreable | **Yes** (overlap) | No | **Yes** (overlap) |
| **B** gap ≥10s | No | No | No |
| **C** gc-shift | No | **Yes** (cyan→magenta @60s) | No |
| **Onsite focus** | Red-over-goal display; score-then-blank under moving red | gc transition at 60s; wave-skip / level-clear timing | Same as Pro 03 |

**Suggested onsite sequence for F:** Play 04 to 60s (watch color change) → 03 or 05 for moving-red overlap cells.

---

## Full per-level matrix

| Level | Tier | Mem | board_t | A | B† | C | Reds | Notes |
|-------|------|-----|---------|---|----|---|------|-------|
| 00 | `-` | N | 600 | N | Y | N | 0 | cad 40s |
| 01 | `-` | N | 600 | N | Y | N | 0 | cad 30s |
| 02 | `-` | N | 600 | N | Y | N | 0 | cad 30s |
| 03 | `-` | N | 600 | **Y** | N | N | 1 | **F** |
| 04 | `-` | N | 600 | N | N | **Y** | 0 | **F** gc@60s |
| 05 | `-` | N | 600 | **Y** | N | N | 1 | **F** |
| 06 | `-` | N | 600 | **Y** | Y | N | 1 | cad 20s |
| 07 | `-` | N | 600 | N | N | N | 0 | baseline |
| 08 | `-` | N | 600 | N | Y | N | 0 | cad 60s |
| 09 | `-` | N | 600 | **Y** | N | N | 1 | |
| 10 | `-` | N | 600 | N | N | N | 0 | |
| 11 | `-` | N | 600 | **Y** | N | N | 1 | |
| 12 | `-` | N | 600 | N | N | N | 0 | baseline |
| 13 | `-` | N | 600 | N | N | N | 0 | baseline |
| 14 | `-` | N | 600 | N | N | N | 0 | baseline |
| 15 | `-` | N | 600 | **Y** | N | N | 1 | |
| 16 | `-` | N | 600 | N | N | N | 0 | baseline |
| YC01–YC08 | `--` | Y | 600 | N | N | N | 0 | memory only |
| YC09 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |
| YC10 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |
| YC11 | `--` | Y | 600 | N | N | N | 0 | |
| YC12 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |
| YC13 | `--` | Y | 600 | N | N | N | 0 | |
| YC14 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |
| YC15 | `--` | Y | 600 | N | N | N | 0 | |
| YC16 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |
| YC17 | `--` | Y | 600 | N | N | N | 0 | |
| YC18 | `--` | Y | 600 | **Y** | N | N | 1 | A+D |

† **B** = start cadence ≥10s (see Category B). Dead-gap B: none.

---

## Implications — level data vs code

| Issue | Root | Fix owner |
|-------|------|-----------|
| **A** Red not visible over scoreable | Code — no display priority in normal mode; `goal_cells` excludes `red_cells` | **Code** (`game_manager` display winner map, see `ONSITE_HEX_RED_OVER_SCOREABLE.md`) |
| **A** Blank cell + red hazard after score | Code — `_consume_cell` blanks tile; Play redraws red on next frame | **Code** (expected hazard behavior; verify visually) |
| **B** Long wait between waves | Level data sets stagger (pro 00–08); code auto-jumps dead time | **Code** already mitigates; level data sets pacing |
| **C** Pro 04 gc switch @60s | Level data — intentional cyan/magenta phases | **Code** must handle gc transition without premature `_level_cleared`; level data is correct |
| **D** Memory teal / reveal | Level data uses `YC` prefix; code enables `_memory_mode` | **Code** (reveal stack, hint, red overlay order) |
| **E** 600s board vs 300s session | All levels authored at 600s; session cap is product constant | **Code/config** — no level edit needed |

**Do not edit level files** for A, B, or E. Pro 04's gc shift (C) is intentional level design.

---

## Priority order for onsite testing

1. **Pro 03, 04, 05 (F)** — explicit smoke trio: gc transition (04), moving red overlap (03, 05).
2. **Category A pro levels** — `06`, `09`, `11`, `15` after F passes.
3. **Category A + D memory** — `YC09`, `YC10`, `YC12`, `YC14`, `YC16`, `YC18` (red overlay on teal-hidden goals).
4. **Category D memory (no A)** — `YC01` (canonical prompt mode per `LEVELS.md`), then `YC02`–`YC08`.
5. **Category B stagger** — `00` (40s waves), `08` (60s beat) to verify auto-jump feels correct.
6. **Baselines** — `07`, `12`, `13`, `14`, `16` (no A–D flags) for regression after fixes.
7. **Hardware overlap** — any A level with `USE_SERIAL_HD=1`: confirm 3-ring red visible on physical tile during overlap.

---

## Other trees (not swept)

| Path | Count | Notes |
|------|------:|-------|
| `games/source/---/*.ledb` | 22+ | 2P marathon; separate onsite doc |
| `games/source_group/` | 10 | Group mode; own `_build_group_level_sequence` |
| `games/source/effects/` | 3 | `countdown`, `level_clear`, `level_fail` |
| `games/Extra/` | 10 | Dev/test; not in `_TIERS_1P` progression |

---

## Related docs

- `docs/ONSITE_HEX_RED_OVER_SCOREABLE.md` — A category display fix spec
- `docs/LEVELS.md` — tier overview, stagger, memory mechanics
- `HARDWARE_VALIDATION.md` — first hardware session checklist
- `api/game_manager.py` — `_load_level_file`, `_setup_level`, auto-jump, masked-goal grace
