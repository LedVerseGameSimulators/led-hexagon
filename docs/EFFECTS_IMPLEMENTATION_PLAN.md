# LED Hexagon — effects implementation plan

**Status:** Ready for Phase 0 (aligned with locked decisions 2026-08-07)  
**Spec:** [EFFECTS_SPEC.md](./EFFECTS_SPEC.md)  
**Global rules:** [GLOBAL_RULES.md](../../docs/game-effects/GLOBAL_RULES.md)  
**Locked decisions:** [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md)  
**Matrix:** [GRID_MATRICES.md](../../docs/game-effects/GRID_MATRICES.md) (Hex section)

**Testing / TDD (locked #13, mandatory):** [docs/game-effects/TESTING_CONTRACT.md](../../docs/game-effects/TESTING_CONTRACT.md) — red→green→refactor via API; prove `phase` / `accepting_input` inside the marathon loop; Layer B smoke with FE + sim. No merge without green `tests/test_effects_session_loop.py`.

---

## Plan review (2026-08-07)

**Verdict:** **Ready** for Phase 0 authoring + Phase 1 backend work (aligned with [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md)).

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
| 2 | `EFFECTS_SPEC.md` § “Timer expire” ran into level-fail bullets without `## Level fail` | **Fixed** in gap-analysis pass (2026-08-07); see [EFFECTS_SPEC.md](./EFFECTS_SPEC.md) |
| 3 | `LedTable` 16×26 vs HW 5×9 is real; gameplay coords live in 0–4 × 0–8 so effect `.led` at zone 5×9 is safe for MVP | Keep Phase A (effects on 5×9 zone); Phase B remains follow-up |
| 4 | `_hw_blank_floor()` builds grid from `led_table.led_row/col` (16×26); HW draw maps via `rect_position_arr` with OOB → black — works today but sim publishes 16×26 | H1.5 must blank via same HW path; optional H2.3 sim footprint |
| 5 | Script name drift: §2.1 `author_effect_led.py` vs H0.1 `author_hex_effect_leds.py` | Unified to `scripts/author_hex_effect_leds.py` |
| 6 | Double countdown at session start (frontend `CountdownScreen` + backend 3-2-1) | **Locked:** both run; keep approximately in sync (see [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md) #4) |

### Follow-up (not blocking MVP)

1. **Phase B timing:** migrate `LedTable` + sim to shelve 5×9 after effects MVP validated on HW, or block sim polish until then.

---

## Gap analysis (2026-08-07)

**Verdict:** **Ready** for Phase 0 authoring + Phase 1 backend work — aligned with [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md), [EFFECTS_SPEC.md](./EFFECTS_SPEC.md), and [GRID_MATRICES.md](../../docs/game-effects/GRID_MATRICES.md) Hex section after fixes in this pass.

### Severity summary

| Severity | Before | Fixed this pass | Remaining |
|----------|--------|-----------------|-----------|
| **Blocker** | 0 | — | 0 |
| **High** | 1 | 1 | 0 |
| **Medium** | 3 | 2 | 1 |
| **Low** | 2 | 2 | 0 |

### Gaps found and disposition

| # | Sev | Gap | Disposition |
|---|-----|-----|-------------|
| G1 | **High** | `EFFECTS_SPEC.md` — level-fail bullets merged under **Timer expire** (no `## Level fail` heading) | **Fixed** — split sections; session-end edge cases explicit |
| G2 | **Medium** | `EFFECTS_SPEC.md` — no three-file contract or single `countdown.led` with timed groups | **Fixed** — added § Effect `.led` files |
| G3 | **Medium** | `EFFECTS_SPEC.md` — missing life=0 ≤10 s and last-level session-end paths | **Fixed** — under **Timer expire** |
| G4 | **Medium** | [PLAN_REVIEW_CROSS_GAME.md](../../docs/game-effects/PLAN_REVIEW_CROSS_GAME.md) still cites five `hex_countdown_*` files | **Human open** — refresh cross-game review doc (Hex plan is correct) |
| G5 | **Low** | Stinger listed as TBD vs locked `games/audio/transition_stinger.mp3` | **Fixed** in spec |
| G6 | **Low** | “Stay in sync” vs locked “approximately in sync” + both UI and floor run | **Fixed** in spec |

### Locked-decision verification (pass)

| Check | Result |
|-------|--------|
| Exactly **three** effect files | **Pass** — `countdown.led`, `level_clear.led`, `level_fail.led` |
| One `countdown.led` with timed groups (not `hex_countdown_3/2/1`) | **Pass** — §2.1, H0.1/H1.3 |
| Footprint **5×9 / 33 live** from shelve | **Pass** — shelve verified (`value_high=5`, `value_width=9`, 12 dead, 33 live) |
| GRID_MATRICES Hex ASCII + legend | **Pass** — rows 2–4 fully live; matches shelve |
| Session flow (life≤10s, last level, timer expire → clear → stinger → black) | **Pass** — § Locked decisions + §2.3 |

### Remaining human opens (not blocking Phase 0)

1. **Cross-game doc refresh** — update `PLAN_REVIEW_CROSS_GAME.md` §1 Hexagon row (still describes five-file / split countdown pattern).
2. **Phase B footprint** — optional `LedTable` + sim migration from 16×26 logical buffer to shelve-native 5×9 (§2.6).
3. **Asset drop** — ship `games/audio/transition_stinger.mp3` and wire BGM/score MP3s during Phase 1 (paths locked; files not in repo yet).
4. **Frontend timing** — align `CountdownScreen` step duration (~1.0 s today) with backend ~0.8 s during implementation (H2.2).

---

## Locked decisions (do not revisit)

Authoritative source: [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md). Hex-specific highlights:

| # | Decision |
|---|----------|
| 1 | **Effects directory:** `games/source/effects/` — exactly **three** files: `countdown.led`, `level_clear.led`, `level_fail.led`. |
| 2 | **Countdown packaging:** one `countdown.led` with **three timed groups** (3→2→1 @ ~0.8 s each), not three separate files. |
| 3 | **Hex simple solids** on all **33 live tiles**, all **3 rings** same color: countdown **3=red, 2=blue, 1=green**; **clear=green**; **fail=red**. No digit glyphs on the floor. |
| 4 | **UI + floor countdown:** both run; keep approximately in sync (floor from backend `.led`; UI countdown stays). |
| 5 | **Transition stinger:** one shared `games/audio/transition_stinger.mp3` for clear **and** fail. |
| 6 | **Audio helper:** `api/audio_manager.py` with class `AudioManager` — non-blocking (no game-thread waits). |
| 7 | **Phase API:** on `/game-state`, expose at least `phase` + `accepting_input`. Values: `countdown` \| `playing` \| `level_clear` \| `level_fail` \| `session_end`. |
| 8 | **Life=0 with ≤10 s left:** session end — `level_clear.led` → stinger → black; **no fail panel; no countdown**. |
| 9 | **Last level cleared / timer expire:** session end — `level_clear.led` → stinger → black; **no countdown**. |
| 10 | **Score SFX:** backend authoritative; mute frontend synth when backend audio active. |
| 11 | **Effect `.led` authoring:** study existing levels; bootstrap our own effect `.led`; test in sim. |

### Session flow (locked)

```
Every level start:
  play(countdown.led) + UI countdown (~sync) → play(gameplay) + BGM

Lives = 0 and >10 s left:
  stop BGM → play(level_fail.led) + stinger → play(countdown.led) → restart same level

Lives = 0 and ≤10 s left:
  stop BGM → play(level_clear.led) + stinger → black → session end

Level cleared (more levels remain):
  stop BGM → play(level_clear.led) + stinger → play(countdown.led) → next level

Timer expire OR last level cleared:
  stop BGM → play(level_clear.led) + stinger → black → session end
```

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
| **`docs/EFFECTS_SPEC.md` structure** | — | — | **Fixed** — separate `## Level fail`; session-end paths documented |

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
- Effect mini-levels can mirror gameplay structure: `countdown.led` uses **three timed `normal_led` groups**; `level_clear.led` / `level_fail.led` use one group each.

---

## 2. Architecture

### 2.1 Effect assets (`.led` mini-levels)

New directory (not part of marathon tier chain):

```
games/source/effects/
  countdown.led      # ~2.4 s total: 3 timed groups @ t=0, 0.8, 1.6 (red → blue → green)
  level_clear.led    # ~2.5 s, solid green
  level_fail.led     # ~2.5 s, solid red
```

Shared audio (cross-game):

```
games/audio/
  transition_stinger.mp3   # one stinger for clear AND fail
```

**Authoring rules**

1. **`para_key_game`:** `row=5`, `col=9`, `zone_row_from=0`, `zone_row_to=5`, `zone_col_from=0`, `zone_col_to=9`, `play_order=False`, `background=(0,0,0)`.
2. **`countdown.led`:** **three `normal_led` groups** (`Setting.FLOOR_LIGHT`), each covering all 33 live `(row,col)` members:
   - Group 1: `start_time_sec=0`, `end_time_sec=0.8`, color `[254, 0, 0]` (3)
   - Group 2: `start_time_sec=0.8`, `end_time_sec=1.6`, color `[0, 0, 254]` (2)
   - Group 3: `start_time_sec=1.6`, `end_time_sec=2.4`, color `[0, 254, 0]` (1)
3. **`level_clear.led` / `level_fail.led`:** one `normal_led` group each; `start_time_sec=0`; `end_time_sec` = hold duration (~2.5 s); `speed=0`.
4. **Colors** (all 3 rings identical per cell):

   | File | RGB (per ring) |
   |------|----------------|
   | `countdown.led` group 1 (3) | `[254, 0, 0]` |
   | `countdown.led` group 2 (2) | `[0, 0, 254]` |
   | `countdown.led` group 3 (1) | `[0, 254, 0]` |
   | `level_clear.led` | `[0, 254, 0]` |
   | `level_fail.led` | `[254, 0, 0]` |

5. **No `goal_led` groups** in effect files (avoid goal-color classifier side effects).
6. Single `Play.running()` call per effect file — countdown is one load, not three sequential mini-levels.

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
- Publish `current_state.phase` and `accepting_input` for frontend sync (`countdown`, `playing`, `level_clear`, `level_fail`, `session_end`).
- **No BGM** during effects.

Do **not** fork a second Play implementation — reuse `_load_level_file` + `Play.running()`.

### 2.3 Marathon state machine (insertion points)

```text
SESSION START
  └─ COUNTDOWN (countdown.led) + UI countdown (~sync) ──► LEVEL PLAY (BGM on)
       ▲                        │
       │                        ├─ board cleared (more levels) ──► CLEAR ──► STINGER ──► COUNTDOWN ──► next level
       │                        │
       │                        ├─ life=0, time>10s ──► FAIL ──► STINGER ──► COUNTDOWN ──► replay level
       │                        │
       │                        ├─ life=0, time≤10s ──► SESSION END PATH
       │                        │
       │                        └─ session timer expired ──► SESSION END PATH
       │
       └─ life restart (same level) uses FAIL path above

SESSION END (timeout | out of life w/ ≤10s | last level cleared | manual stop)
  └─ CLEAR (level_clear.led) ──► STINGER ──► BLANK FLOOR ──► game_over (no countdown)
```

**Timer expire:** treat as session end even if `_level_cleared` also fired in the same frame — `level_clear.led`, stinger, black, **no** countdown (per LOCKED_DECISIONS).

**Last level cleared with time remaining:** session end path (not “clear → countdown → nothing”).

**Life=0 with ≤10 s left:** session end — `level_clear.led` → stinger → black; **no fail panel; no countdown**.

### 2.4 Audio (`api/audio_manager.py` — `AudioManager`, non-blocking)

| Event | Asset | API |
|-------|-------|-----|
| Level play | TRON BGM (`game_bg_audio_sw` or `games/audio/bgm_hex.mp3`) | `start_bgm(..., loops=-1)` on first frame of level; `stop_bgm()` before any effect |
| Score +1 | shared positive MP3 | `play_sfx()` (Sound channel) |
| Penalty / life loss | shared negative / blood MP3 | `play_sfx()` |
| Countdown 3-2-1 | tick/noise SFX (stock OK) | `play_sfx()` at countdown start |
| Level transition | `games/audio/transition_stinger.mp3` (~2–3 s) | `play_stinger()` — **one shared file** for clear **and** fail |

**Implementation notes**

- Add `api/audio_manager.py` with class `AudioManager` (daemon thread + queue or fire-and-forget `Sound` channels).
- Init pygame mixer **once** when `USE_SERIAL_HD` or `ENABLE_AUDIO=1`; do not mock when audio enabled.
- Never call blocking `mixer.music.wait` in the game thread.
- BGM off during: countdown, clear, fail, stinger, session end.
- **Score SFX authority:** backend plays shared MP3s; **mute frontend Web Audio synth** when backend audio active.

### 2.5 Frontend sync

- Add WS/API fields on `/game-state`: at least `phase` + `accepting_input` (no RFID changes).
- **Suggested `phase` values:** `countdown` | `playing` | `level_clear` | `level_fail` | `session_end`.
- **`CountdownScreen`:** keep UI countdown; drive labels from backend `phase` where possible so UI and floor stay **approximately in sync** (~0.8 s steps, 3/2/1 labels — floor stays solid colors).
- **`SimulatorScreen`:** start-game on mount stays; frontend synth muted when backend audio active.

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
| H0.0 | Create `tests/test_effects_session_loop.py` skeleton + pytest fixtures (`TestClient`, short session config) — **before** marathon wiring | backend |
| H0.1 | Add `scripts/author_hex_effect_leds.py` — generate **3** effect `.led` from shelve live coords | scripting |
| H0.2 | Commit `games/source/effects/countdown.led`, `level_clear.led`, `level_fail.led` | assets |
| H0.3 | Unit test: load each effect file; assert group count (countdown=3, clear/fail=1), **33 members per group** on **5×9** zone, correct duration & color | pytest |
| H0.4 | Add `tests/fixtures/effects/` — tiny `.led` fixtures (short `board_time`) for fast marathon API tests | backend |

### Phase 1 — Backend core

| ID | Task | Notes |
|----|------|-------|
| H1.1 | `api/audio_manager.py` + `AudioManager`; gate mocks off when audio enabled | `ENABLE_AUDIO=1` |
| H1.2 | `_effect_frame_callback` + `_run_effect_led()` | no scoring |
| H1.3 | `_run_countdown()` → single `countdown.led` load + tick SFX | ~2.4 s total |
| H1.4 | `_run_level_clear()` / `_run_level_fail()` | green / red holds |
| H1.5 | Wire marathon loop per locked session flow (§ Locked decisions); on session end → `level_clear.led`→stinger→blank (no countdown) | **Blocked until** §5 pre-marathon TDD checklist (T1/T7/T8 red tests exist and fail) |
| H1.6 | BGM start/stop around level play only | |
| H1.7 | Hook score/life SFX in existing `try_score_cell` / `_apply_hazard_penalty` | non-blocking |

### Phase 2 — Frontend & API surface

| ID | Task |
|----|------|
| H2.1 | Expose `phase` + `accepting_input` in `current_state` / WS bridge |
| H2.2 | Keep `CountdownScreen`; align timing (~0.8 s) with backend `phase=countdown` |
| H2.3 | Sim canvas: render 5×9 hex footprint when `grid_rows=5` (optional polish) |

### Phase 3 — Docs & cleanup

| ID | Task |
|----|------|
| H3.1 | Fix `ONSITE.md`, `HARDWARE_MODE.md`, `LEVELS.md` — 5×9 onsite, 16×26 logical buffer |
| H3.2 | ~~Fix `EFFECTS_SPEC.md` § heading~~ **Done** (2026-08-07 gap pass); optional `GRID_MATRICES.md` legend note (rows 2–4 = full live bands) |
| H3.3 | Update `SETTINGS.md` audio rows to ✅ when implemented |

---

## 4. Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **16×26 buffer vs 5×9 HW** | Effect cells off-zone or wrong HW mapping | Author only 33 shelve coords; HW init from shelve; test on HW early |
| **Wrong footprint diagram** | Effect `.led` missing tiles | Generate coords from shelve (`author_hex_effect_leds.py`); do not hand-copy ASCII |
| **UI + floor countdown drift** | UI and floor slightly out of step | Both run per lock; publish `phase`; target ~0.8 s steps |
| **Scoring during effect play** | Ghost score/life changes | Effect callback skips input/scoring; ignore `/game-input` while `phase != playing` |
| **pygame mock in tests** | Silent CI | Default mock; `ENABLE_AUDIO=0`; separate smoke with audio flag |
| **Stinger asset** | Silent transitions | Ship `games/audio/transition_stinger.mp3` (shared clear+fail) |
| **Life restart edge (≤10 s)** | Should session-end not fail→countdown | Locked: `level_clear.led` → stinger → black; no fail panel |
| **3-ring byte order on HW** | Wrong colors on rings | Solids on all rings; verify with `test_hardware.py` pattern |
| **Marathon reload cost** | Extra zip extract per transition | Only 3 small effect files; cache loaded effect `dict_group` in memory if needed |

---

## 5. TDD / verification (locked #13)

**Contract:** [docs/game-effects/TESTING_CONTRACT.md](../../docs/game-effects/TESTING_CONTRACT.md) — mandatory for merge. Effects work is **not done** until automated tests prove behavior runs **inside the marathon loop** (`_run_game`, ~L1376+), exercised through the **API**, and spot-checked with **frontend + simulator**.

### Required test module

`tests/test_effects_session_loop.py` — one dedicated module covering **T1–T8** from [TESTING_CONTRACT.md §2](../../docs/game-effects/TESTING_CONTRACT.md#2-what-must-be-proven). T9 lives in `tests/test_audio_manager.py`. (T10 is Hoops-only — N/A for Hex.)

| Contract ID | Scenario | Assert via API (`GET /game-state` or `/game-state/{game_id}`) |
|-------------|----------|----------------------------------------------------------------|
| **T1** | Session start | After `POST /start-game`, poll until `phase=countdown` (or brief transition) then `phase=playing` with `accepting_input=true` |
| **T2** | Countdown every level | Mid-session clear → next level: `phase` goes `level_clear` → `countdown` → `playing` (not straight into gameplay) |
| **T3** | Level fail restart | Force life=0 with **>10 s** left → `phase=level_fail` → `countdown` → `playing` on **same** level; score preserved |
| **T4** | Session end (timer) | Timer expire → `phase=level_clear` or `session_end` → floor blank; **no** subsequent `countdown` |
| **T5** | Session end (life ≤10 s) | Life=0 with **≤10 s** left → clear path (not fail panel) → black; no countdown |
| **T6** | Last level cleared | Clear final level → session end (clear → black); no countdown |
| **T7** | Input gating | While `accepting_input=false` (countdown / clear / fail), `POST /game-input` does **not** change score / life |
| **T8** | Playing accepts input | During `phase=playing`, valid press **does** affect score or life — proves effects did not break gameplay |

**Marathon-loop proof requirement:** fail / clear / countdown transitions must be exercised **inside** `_run_game` session loop — not via isolated mocks of `Play.running` alone. Tests start a real session via `POST /start-game` and poll `phase` through at least one full transition cycle.

**How to run (Layer A — required, CI-friendly):**

- Start FastAPI in-process (`TestClient` / `httpx.ASGITransport`) **or** spawn uvicorn on a free port.
- Sim mode (`USE_SERIAL_HD=0` or unset).
- Drive `POST /start-game`, poll `GET /game-state` for `phase`, `accepting_input`, `life`, `score`, `current_level`; send `POST /game-input` during gated vs playing phases.
- Use short effect `.led` fixtures under `tests/fixtures/effects/` (tiny `board_time` on **5×9 / 33-tile** archives) or env override so tests finish in seconds.
- Effect fixtures must target only the 33 shelve live coords (see §1.1); assert `para_key_game` zone **5×9**.

```bash
cd led-hexagon
pytest tests/test_effects_session_loop.py -q   # merge gate
pytest tests/test_audio_manager.py -q          # T9 optional bar
```

### Layer B — API + ws_bridge + simulator (required smoke)

Manual or scripted smoke before merge:

1. Start API + `ws_bridge` + frontend (`scripts/start-dev.sh` or equivalent).
2. Guest login → start session.
3. Watch sim / floor iframe on **5×9 hex footprint** (33 live tiles):
   - Countdown: red → blue → green (~0.8 s each) on all live tiles before level 1
   - Gameplay LEDs + scoring works
   - Trigger fail (lose all lives, >10 s left) → red hold → countdown → same level
   - Or clear / short timer → green hold → next countdown or session black
4. Confirm UI countdown and floor stay roughly in sync; UI shows playing when `phase=playing`.

```bash
# From repo root or led-hexagon — adjust to local start script
./scripts/start-all-games.sh
# Optional: extend scripts/hw_mode_smoke_test.py / full_hw_sim_smoke.py with phase checks
```

### Layer C — Frontend checklist

- [ ] `SimulatorScreen`: scoring clicks ignored/disabled when backend `phase` is `countdown` / `level_clear` / `level_fail`
- [ ] Synth score/hurt beeps **muted** when backend `AudioManager` active (locked #10)
- [ ] No crash when `phase` / `accepting_input` appear on `/game-state`
- [ ] Optional H2.3: sim canvas renders 5×9 hex footprint when `grid_rows=5`

Automated FE tests are nice-to-have; **Layer A + B** are the merge gate.

### Red→green task order (TESTING_CONTRACT §4)

Follow this order — **write failing tests before wiring each marathon hook**:

1. [ ] **Red:** Add failing tests for **T1 + T7 + T8** (countdown → playing + input gate + gameplay still scores)
2. [ ] **Green:** Implement `_run_effect_led()` + marathon hooks until T1/T7/T8 pass
3. [ ] **Red:** Add failing tests for **T2, T3** (clear / fail loops inside marathon)
4. [ ] **Green:** Implement clear/fail panels + countdown-between-levels (H1.4–H1.5)
5. [ ] **Red:** Add failing tests for **T4, T5, T6** (session end paths)
6. [ ] **Green:** Implement session-end path: `level_clear.led` → stinger → blank (no countdown)
7. [ ] **Green:** `AudioManager` + BGM boundaries (T9 in `test_audio_manager.py`)
8. [ ] Run **Layer B** smoke; fix until sim shows panels inside the real loop
9. [ ] Note smoke date/result in commit message or plan

**Do not** land marathon wiring (H1.5) without tests that would fail on the pre-effects codebase.

### Pre-marathon wiring checklist (write tests FIRST)

- [ ] Create `tests/test_effects_session_loop.py` skeleton + pytest fixtures (`TestClient`, short session config)
- [ ] **Red:** T1 — session start reaches `phase=playing` with `accepting_input=true`
- [ ] **Red:** T7 — input blocked during `phase=countdown` / `level_clear` / `level_fail`
- [ ] **Red:** T8 — valid input works during `phase=playing`
- [ ] Confirm all three fail on current codebase → **then** begin H1.2/H1.5 marathon wiring

### Additional regression tests (same module or helpers)

| # | Scenario | Expected |
|---|----------|----------|
| 9 | Effect `.led` load on 5×9 zone | Each group covers exactly **33** shelve live coords; countdown has 3 timed groups (red/blue/green) |
| 10 | Stop mid-countdown | Input locked; clean stop; floor blank |
| 11 | Rapid fail restart (3×) | Each cycle: fail → countdown → replay; BGM never overlaps stinger |
| 12 | Session end after last level clear | `level_clear` hold in loop; `_finish_session` blanks only — **no** second clear, **no** countdown |

### Hardware (`USE_SERIAL_HD=1`) — post-merge validation

| # | Check |
|---|-------|
| 1 | `_hw_init` logs `5×9, layout=1, 33 LEDs` |
| 2 | Countdown solids: red → blue → green on all physical hex tiles (all 3 rings) |
| 3 | Clear = all green; fail = all red; hold ~2–3 s on 33 tiles |
| 4 | Timer expire → green hold → all off; **no** 3-2-1 after |
| 5 | BGM audible only during gameplay; tick/stinger audible during transitions |
| 6 | Session stop / logout blanks floor (`_hw_blank_floor`) |

Reference timing: `~/Downloads/Battle Arena/` captures.

### Definition of done

- [ ] `tests/test_effects_session_loop.py` covers T1–T8; pytest green in sim mode
- [ ] Layer B smoke documented and run once
- [ ] `/game-state` exposes `phase` + `accepting_input` during live session
- [ ] Gameplay still scores/loses life during `playing` (T8 regression)
- [ ] Effect `.led` archives validated on **5×9 / 33-tile** footprint

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
- Separate clear/fail stinger files (MVP uses one shared `transition_stinger.mp3`)

---

## 8. Implementation order (TDD-first)

1. **Red:** Create `tests/test_effects_session_loop.py` with failing T1 + T7 + T8 (see §5 pre-marathon checklist)
2. Author three effect `.led` files at **5×9 / 33 tiles** via `author_hex_effect_leds.py` + loader smoke test (H0.1–H0.3)
3. **Green:** `_run_effect_led()` + marathon loop wiring (H1.2/H1.5) until T1/T7/T8 pass
4. **Red:** Failing T2 + T3 → **Green:** clear/fail panels + countdown-between-levels (H1.4)
5. **Red:** Failing T4 + T5 + T6 → **Green:** session-end path (clear → stinger → blank, no countdown)
6. `AudioManager` + shared `transition_stinger.mp3` + BGM boundaries (T9 in `test_audio_manager.py`)
7. State fields (`phase`, `accepting_input`) + `CountdownScreen` / `SimulatorScreen` sync (H2.1–H2.2)
8. **Layer B** smoke — API + ws_bridge + FE/sim; fix until red→blue→green panels visible in real loop
9. HW validation on 5×9 onsite footprint

---

**Next step:** §5 pre-marathon TDD checklist (H0.0) → Phase 0 authoring (H0.1–H0.4) → H1.2/H1.5 only after red tests fail.

*Plan only — no runtime code changes in this commit.*
