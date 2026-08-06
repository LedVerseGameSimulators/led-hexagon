# LED Hexagon — effects implementation plan

**Status:** Ready for Phase 0 (plan reviewed 2026-08-07)  
**Spec:** [EFFECTS_SPEC.md](./EFFECTS_SPEC.md)  
**Global rules:** [GLOBAL_RULES.md](../../docs/game-effects/GLOBAL_RULES.md)  
**Matrix:** [GRID_MATRICES.md](../../docs/game-effects/GRID_MATRICES.md) (Hex section)

---

## Plan review (2026-08-07)

**Verdict:** **Ready** for Phase 0 authoring + Phase 1 backend work, subject to human decisions below.

### Spot-check: shelve + code (authoritative)

Verified against `games/setting/led_parameter` (shelve) and `api/game_manager.py`:

| Check | Result |
|-------|--------|
| `value_high` / `value_width` | **5 / 9** |
| `led_layout_type` | **1** (hex) |
| `floor_layout_coors_no_use` | **12** dead cells (see footprint below) |
| Live tiles | **33** (`list_com_info`: COM9, 33× `normal_led`) |
| `LedTable` in marathon | **16 × 26** hardcoded (`L966`: `led_row=16, led_col=26`) |
| `_HW_DEFAULT_ROWS/COLS` | **16 / 26** (fallback when shelve missing) |
| `_hw_init()` | Reads shelve → **5×9** + `no_use` → `init_layout()` |

**Authoritative footprint** (from shelve `floor_layout_coors_no_use`, not ASCII alone):

```
Cols:  0  1  2  3  4  5  6  7  8
Row 0: X  X  X  X  .  X  X  X  X     ← 1 live: (0,4)
Row 1: .  X  .  X  .  X  .  X  .     ← 5 live: staggered
Row 2: .  .  .  .  .  .  .  .  .     ← 9 live (full row)
Row 3: .  .  .  .  .  .  .  .  .     ← 9 live
Row 4: .  .  .  .  .  .  .  .  .     ← 9 live
```

`.` = live (33 total), `X` = dead (12 total). Matches `EFFECTS_SPEC.md` and `GRID_MATRICES.md` Hex ASCII **when `.`/`X` legend is read correctly** — rows 2–4 are fully live (all `.`), not empty.

### Top findings (critical review)

| # | Finding | Plan action |
|---|---------|-------------|
| 1 | Prior audit wrongly claimed rows 2–4 ASCII was “empty”; shelve confirms **27 live tiles in rows 2–4** and diagrams are correct | Fixed §1.1; generate `.led` coords from shelve, not hand-copy |
| 2 | `EFFECTS_SPEC.md` § “Timer expire” runs into **level fail (red)** bullets without a `## Level fail` heading (same doc bug as Grid) | Implementation follows GLOBAL_RULES; note in §1.1; fix heading in H3.2 |
| 3 | `LedTable` 16×26 vs HW 5×9 is real; gameplay coords live in 0–4 × 0–8 so effect `.led` at zone 5×9 is safe for MVP | Keep Phase A (effects on 5×9 zone); Phase B remains follow-up |
| 4 | `_hw_blank_floor()` builds grid from `led_table.led_row/col` (16×26); HW draw maps via `rect_position_arr` with OOB → black — works today but sim publishes 16×26 | H1.5 must blank via same HW path; optional H2.3 sim footprint |
| 5 | Script name drift: §2.1 `author_effect_led.py` vs H0.1 `author_hex_effect_leds.py` | Unified to `scripts/author_hex_effect_leds.py` |
| 6 | Double countdown at session start (frontend `CountdownScreen` + backend 3-2-1) | **Human decision** — recommend backend owns floor; frontend defers or mirrors `phase` |

### Human decisions (before Phase 1 merge)

1. **Session-start countdown owner:** backend-only floor countdown (frontend waits for `phase=playing`) vs keep frontend UI and accept duplicate timing risk.
2. **Countdown `.led` packaging:** three files (locked default) vs one multi-group file — three files kept unless ops asks for single reload.
3. **Phase B timing:** migrate `LedTable` + sim to shelve 5×9 after effects MVP validated on HW, or block sim polish until then.

---

## Locked decisions (do not revisit)

| # | Decision |
|---|----------|
| 1 | **`.led` mini-levels** for countdown / clear / fail — loaded and played through the **same** `Play.running()` path as gameplay levels; wired into the marathon loop. |
| 2 | **Hex simple solids** on all **33 live tiles**, all **3 rings** same color: countdown **3=red, 2=blue, 1=green**; **clear=green**; **fail=red**. No digit glyphs on the floor. |
| 3 | **Timer expire = session end** — same clear (green) hold → stinger → all black/off; **no countdown**. |
| 4 | **Non-blocking audio** — SFX and stingers must not stall the frame loop or marathon transitions. |

---

## 1. Audit — current state vs spec

### 1.1 Footprint: 16×26 (code/docs) vs 5×9 / 33 tiles (onsite)

| Source | Rows × cols | Live tiles | Notes |
|--------|-------------|------------|-------|
| **`setting/led_parameter` (onsite shelve)** | **5 × 9** | **33** (`list_com_info`: COM9, 33 `normal_led`) | `value_high=5`, `value_width=9`, `led_layout_type=1`, 12 dead coords in `floor_layout_coors_no_use` |
| **`api/game_manager.py`** | **16 × 26** hardcoded | All 416 buffer cells | `LedTable(..., led_row=16, led_col=26)`; `_HW_DEFAULT_ROWS/COLS = 16/26`; zone fallback `0–16 / 0–26` |
| **`games/game_play/game_running.py`** | defaults **16 × 26** | — | Mock `LedTable` fallbacks when `led_row/col` omitted |
| **`games/test_hardware.py`** | reads shelve (→ **5×9**) but comment says 16×26 | 33 on HW | Correct runtime read; misleading header comment |
| **`ONSITE.md`, `docs/HARDWARE_MODE.md`, `docs/LEVELS.md`** | document **16×26** full grid + 5×9 zone | — | Stale relative to onsite shelve and effects spec |
| **`docs/EFFECTS_SPEC.md` + GRID_MATRICES ASCII** | **5×9** bounding | 33 | Footprint **matches shelve** when `.`=live / `X`=dead; rows 2–4 are **fully live** (9 tiles each) |
| **`docs/EFFECTS_SPEC.md` structure** | — | — | § “Timer expire” merges into level-fail (red) bullets without `## Level fail` — follow GLOBAL_RULES, not broken heading |

**Authoritative live-cell set** (from shelve, verified 2026-08-07 — use for `.led` authoring):

```
(0,4)
(1,0) (1,2) (1,4) (1,6) (1,8)
(2,0)…(2,8)  (3,0)…(3,8)  (4,0)…(4,8)   ← rows 2–4: full 9-wide bands (27 tiles)
```

**Effects `.led` files MUST** target only these 33 coordinates inside zone `row 0–5, col 0–9` (`para_key_game`: `row=5`, `col=9`, `zone_* = 0–5 / 0–9`). Dead cells stay black. Do **not** author on a 16×26 canvas. Generate member lists from shelve via `author_hex_effect_leds.py`.

### 1.2 Marathon / transitions — not implemented

`api/game_manager.py` session loop (`_run_game`, ~L1376+) today:

- Loads gameplay `.led` → `play.running(dg)` → on `_level_cleared` immediately advances to next file.
- On `_restart_level` (life=0, >10 s session time): refills HP and reloads same level — **no fail LED, no stinger, no countdown**.
- On session end (`_session_over`, timeout, chain exhausted): `_hw_blank_floor()` only — **no green clear hold, no stinger**.
- **No effect `.led` loads**, no transition state machine, no BGM lifecycle.

### 1.3 Countdown — UI only, not floor-synced per level

| Layer | Today | Spec gap |
|-------|-------|----------|
| **Frontend** `CountdownScreen.jsx` | Pre-session 3-2-1-GO @ **1.0 s** step; Web Audio beeps | Runs **before** `/start-game`; not repeated mid-session; **no floor colors** (red/blue/green) |
| **Backend** | None between levels | Every level start needs 3→2→1 solids @ ~**0.8 s** on 33 tiles |
| **Legacy Tk** `gui/gui_countdown.py` | MP4 fullscreen video | Not used by headless API |

First-level countdown is split across frontend (UI) and nothing (floor). Mid-session transitions have no countdown anywhere.

### 1.4 Audio — mocked / silent in API path

- `game_manager.py` mocks `pygame` / `audio_play` for headless import (L67–70).
- Shelve has paths: `game_bg_audio_sw` (TRON *End of Line*), `game_scode_sw`, `game_blood_sw` — **never played** in API marathon.
- `SimulatorScreen.jsx` uses Web Audio synth beeps for score/hurt only — not BGM/stinger/countdown ticks.
- `audio_play/audio.py`: `play()` is non-blocking (`Sound` on free channel); `play_bmg()` uses `mixer.music` — suitable if real pygame loaded once.

### 1.5 Three-ring cell format — ready

- Gameplay already uses `[[R,G,B],[R,G,B],[R,G,B]]` per cell; `_normalize_rings`, HW draw path pass-through (L1338–1340).
- Effect groups must store **3-ring identical colors** per tile (solid outer/mid/inner).
- `_group_main_color()` reads **ring[1]** — for solids all rings match; safe for effect groups.

### 1.6 `.led` load path — ready for mini-levels

- `_load_level_file()` (L402–432): zip → shelve → `(dict_group, para_key_game)`.
- Gameplay levels use zone `0–5 / 0–9`, types `normal_led` + `goal_led` (see `00.led`: 300 goal groups + 4 normal).
- Effect mini-levels can mirror gameplay structure with **one `normal_led` group** covering 33 cells, short `end_time_sec`.

---

## 2. Architecture

### 2.1 Effect assets (`.led` mini-levels)

New directory (not part of marathon tier chain):

```
games/source/effects/
  hex_countdown_3.led   # ~0.8 s, all live tiles solid red
  hex_countdown_2.led   # ~0.8 s, solid blue
  hex_countdown_1.led   # ~0.8 s, solid green
  hex_level_clear.led   # ~2.5 s, solid green
  hex_level_fail.led    # ~2.5 s, solid red
```

**Authoring rules**

1. **`para_key_game`:** `row=5`, `col=9`, `zone_row_from=0`, `zone_row_to=5`, `zone_col_from=0`, `zone_col_to=9`, `play_order=False`, `background=(0,0,0)`.
2. **One `normal_led` group** (`Setting.FLOOR_LIGHT`): `start_member` = list of 33 `(row,col)` floats from shelve live set; `start_time_sec=0`; `end_time_sec` = hold duration; `speed=0`.
3. **Colors** (all 3 rings identical per cell):

   | File | RGB (per ring) |
   |------|----------------|
   | `hex_countdown_3.led` | `[254, 0, 0]` |
   | `hex_countdown_2.led` | `[0, 0, 254]` |
   | `hex_countdown_1.led` | `[0, 254, 0]` |
   | `hex_level_clear.led` | `[0, 254, 0]` |
   | `hex_level_fail.led` | `[254, 0, 0]` |

4. **No `goal_led` groups** in effect files (avoid goal-color classifier side effects).
5. **Optional:** single `hex_countdown_all.led` with 3 timed groups @ t=0, 0.8, 1.6 — still one `Play.running()` call. Prefer **three files** per locked “mini-levels” wording and simpler tuning.

**Authoring tool:** `scripts/author_hex_effect_leds.py` (H0.1) — reads live coords from `led_parameter` shelve, emits zip+shelve matching existing level format; manual GUI editor is error-prone for 33 coords.

### 2.2 Runtime: `EffectRunner` in `game_manager.py`

Minimal helper used **inside** the game thread (same `Play` + `LedTable` instance):

```text
_run_effect_led(path, *, score_audio=None):
  dg, go = _load_level_file(path)
  configure zone from go; skip scoring classifier hooks
  play.total_pass = 0
  play.callback = _effect_frame_callback   # draw + HW push only; no input/scoring
  play.running(dg)                         # exits when total_pass > board_time
```

**`_effect_frame_callback`**

- Blank non-live cells each frame (or rely on groups only touching live coords).
- Push `led_display` to HW at `_HW_DRAW_INTERVAL`.
- Publish `current_state.phase` for frontend sync (`countdown_3`, `countdown_2`, `countdown_1`, `level_clear`, `level_fail`, `transition`).
- **No BGM** during effects.

Do **not** fork a second Play implementation — reuse `_load_level_file` + `Play.running()`.

### 2.3 Marathon state machine (insertion points)

```text
SESSION START
  └─ (optional) align UI: frontend may show countdown OR defer to backend for floor sync
  └─ COUNTDOWN 3→2→1  ──► LEVEL PLAY (BGM on)
       ▲                        │
       │                        ├─ board cleared ──► CLEAR (~2.5s) ──► STINGER ──► COUNTDOWN ──► next level
       │                        │
       │                        ├─ life=0, time>10s ──► FAIL (~2.5s) ──► STINGER ──► COUNTDOWN ──► replay level
       │                        │
       │                        ├─ life=0, time≤10s ──► session end path
       │                        │
       │                        └─ session timer expired ──► SESSION END PATH
       │
       └─ life restart (same level) uses FAIL path above

SESSION END (timeout | out of life w/ ≤10s | chain done | manual stop)
  └─ CLEAR (~2.5s) ──► STINGER ──► BLANK FLOOR ──► game_over (no countdown)
```

**Timer expire:** treat as session end even if `_level_cleared` also fired in the same frame — clear green, stinger, black, **no** countdown (per GLOBAL_RULES).

**Chain exhausted with time left:** session end path (not “clear → countdown → nothing”).

### 2.4 Audio (`HexAudio` — non-blocking)

| Event | Asset | API |
|-------|-------|-----|
| Level play | TRON BGM (`game_bg_audio_sw`) | `play_bmg(..., loops=-1)` on first frame of level; `stop()` before any effect |
| Score +1 | shared positive MP3 | `Audio.play()` (Sound channel) |
| Penalty / life loss | shared negative / blood MP3 | `Audio.play()` |
| Countdown 3-2-1 | tick/noise SFX (stock OK) | `play()` at start of each countdown mini-level |
| Level transition | stinger ~2–3 s (TBD) | `play()` or short `play_bmg` once; **never** overlap BGM |

**Implementation notes**

- Init pygame mixer **once** when `USE_SERIAL_HD` or `ENABLE_AUDIO=1`; do not mock when audio enabled.
- Never call `play_sync` / blocking `mixer.music.wait` in the game thread.
- BGM off during: countdown, clear, fail, stinger, session end.
- Frontend Web Audio score/hurt can remain for sim; optional later: mute when backend audio active.

### 2.5 Frontend sync (follow-up, same plan phase)

- Add WS/API fields: `phase`, `phase_step`, `phase_remaining_ms`.
- **`CountdownScreen`:** either remove for session start (backend-owned floor countdown) or drive display from backend phase events so UI matches 0.8 s steps and colors meta (show 3/2/1 labels only — floor stays solid colors).
- **`SimulatorScreen`:** start-game on mount stays; first countdown may duplicate unless frontend waits for `phase=playing`.

### 2.6 Grid dimension strategy (effects vs gameplay buffer)

**Decision: author effect `.led` files at native 5×9 zone** (unlike Grid’s 16×26). Hex onsite shelve is 5×9; all 33 live coords fit in rows 0–4, cols 0–8.

| Phase | Change |
|-------|--------|
| **A (effects MVP)** | Keep `LedTable` 16×26 for gameplay compatibility; effect `.led` files use `para_key_game` zone 5×9 and paint only 33 shelve live cells; `_effect_frame_callback` zeros dead cells in zone each frame. HW init already uses shelve 5×9. `_hw_blank_floor` OOB-safe via `rect_position_arr` bounds. |
| **B (follow-up)** | Read `value_high/value_width` from shelve for `LedTable` + simulator `grid_rows/cols`; update docs/sim canvas. **Out of scope for effects MVP** unless sim/HW mismatch blocks validation. |

Effects validation must run on **hardware/sim with 5×9 HW init**, not assume 416 tiles.

---

## 3. Implementation tasks

### Phase 0 — Authoring & fixtures

| ID | Task | Owner hint |
|----|------|------------|
| H0.1 | Add `scripts/author_hex_effect_leds.py` — generate 5 effect `.led` from shelve live coords | scripting |
| H0.2 | Commit `games/source/effects/*.led` | assets |
| H0.3 | Unit test: load each effect file; assert 1 floor group, 33 members, correct duration & color | pytest |

### Phase 1 — Backend core

| ID | Task | Notes |
|----|------|-------|
| H1.1 | `HexAudio` wrapper; gate mocks off when audio enabled | `ENABLE_AUDIO=1` |
| H1.2 | `_effect_frame_callback` + `_run_effect_led()` | no scoring |
| H1.3 | `_run_countdown_sequence()` → 3 mini-levels + tick SFX | ~2.4 s total |
| H1.4 | `_run_level_clear()` / `_run_level_fail()` | green / red holds |
| H1.5 | Wire marathon loop: before every level → countdown; on clear → clear→stinger→countdown; on restart → fail→stinger→countdown; on session end → clear→stinger→blank | see §2.3 |
| H1.6 | BGM start/stop around level play only | |
| H1.7 | Hook score/life SFX in existing `try_score_cell` / `_apply_hazard_penalty` | non-blocking |

### Phase 2 — Frontend & API surface

| ID | Task |
|----|------|
| H2.1 | Expose `phase` in `current_state` / WS bridge |
| H2.2 | Align `CountdownScreen` timing (0.8 s) or delegate to backend phase |
| H2.3 | Sim canvas: render 5×9 hex footprint when `grid_rows=5` (optional polish) |

### Phase 3 — Docs & cleanup

| ID | Task |
|----|------|
| H3.1 | Fix `ONSITE.md`, `HARDWARE_MODE.md`, `LEVELS.md` — 5×9 onsite, 16×26 logical buffer |
| H3.2 | Fix `EFFECTS_SPEC.md` § heading (`## Level fail` split from timer expire); align `GRID_MATRICES.md` legend note (rows 2–4 = full live bands) |
| H3.3 | Update `SETTINGS.md` audio rows to ✅ when implemented |

---

## 4. Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **16×26 buffer vs 5×9 HW** | Effect cells off-zone or wrong HW mapping | Author only 33 shelve coords; HW init from shelve; test on HW early |
| **Wrong footprint diagram** | Effect `.led` missing tiles | Generate coords from shelve (`author_hex_effect_leds.py`); do not hand-copy ASCII |
| **Double countdown** (frontend + backend) | 6+ s pre-start | Single owner: backend for floor; frontend listens or skips first |
| **Scoring during effect play** | Ghost score/life changes | Effect callback skips input/scoring; ignore `/game-input` while `phase != playing` |
| **pygame mock in tests** | Silent CI | Default mock; `ENABLE_AUDIO=0`; separate smoke with audio flag |
| **Stinger asset TBD** | Silent transitions | Ship stock MP3 placeholder; swap path via shelve or env |
| **Life restart edge (≤10 s)** | Should session-end not fail→countdown | Keep existing `_restart_level` gate; session end uses clear→black only |
| **3-ring byte order on HW** | Wrong colors on rings | Solids on all rings; verify with `test_hardware.py` pattern |
| **Marathon reload cost** | Extra zip extract per transition | Only 5 small effect files; cache loaded effect `dict_group` in memory if needed |

---

## 5. Test plan

### Automated

- [ ] `test_load_effect_leds.py` — structure, member count, colors, durations
- [ ] `test_marathon_transitions.py` (mock Play): assert call order `countdown* → play → clear → countdown → play` on level clear; `fail → countdown → replay` on life restart; `clear → blank` on timeout with **no** countdown
- [ ] `test_audio_policy.py` — BGM off during effects; `play()` invoked on score event (mock mixer)

### Simulator

- [ ] Start session: floor shows red→blue→green (~0.8 s each) before level 1 tiles appear
- [ ] Clear a level mid-marathon: all live tiles green ~2.5 s → next countdown → next level
- [ ] Lose all lives with time left: all red ~2.5 s → countdown → same level restarts with full HP
- [ ] Session timer hits 0: green ~2.5 s → black; **no** 3-2-1 after
- [ ] UI phase labels track backend steps

### Hardware (`USE_SERIAL_HD=1`)

- [ ] `_hw_init` logs `5×9, layout=1, 33 LEDs`
- [ ] Countdown/clear/fail solids visible on all physical hex tiles (all rings)
- [ ] Session end leaves floor black
- [ ] BGM audible during play only; tick/stinger audible during transitions
- [ ] Reference timing against `~/Downloads/Battle Arena/` captures

---

## 6. Reference map

| Topic | Location |
|-------|----------|
| Marathon loop | `api/game_manager.py` `_run_game`, L1376–1508 |
| Level load | `_load_level_file`, `_setup_level` |
| HW init (shelve-driven) | `_hw_init`, L179–206 |
| 3-ring normalize | `_normalize_rings`, L236–253 |
| Life restart | `_frame_callback` L1054–1060; restart loop L1471–1476 |
| Level clear advance | L1478–1482 |
| Session blank | `_hw_blank_floor`, L209–233 |
| Live coords source | `games/setting/led_parameter` → `floor_layout_coors_no_use` |
| Frontend pre-countdown | `frontend/src/screens/CountdownScreen.jsx` |
| Spec | `docs/EFFECTS_SPEC.md` |

---

## 7. Out of scope (this plan)

- Migrating gameplay `LedTable` from 16×26 to 5×9 (phase B above)
- Digit-shaped countdown (Grid-style) — hex uses solid colors only
- Tkinter / legacy `gui_countdown.py` video path
- New stinger final asset selection (placeholder OK)

---

**Next step:** Phase 0 authoring script + Phase 1 H1.2/H1.5 in `api/game_manager.py`, then hardware smoke per §5.
