# HEX: Moving Red Does Not Paint Over Scoreable Tiles

> **Status:** Open — display/compositing gap vs Grid  
> **Scope:** `led-hexagon/api/game_manager.py` frame callback (`_frame_callback`)  
> **Grid reference:** `led-grid/api/game_manager.py` — working overlap priority

> **Memory levels have two kinds of red** (moving vs hidden-under-teal). Plain summary: [ONSITE_HEX_MEMORY_TWO_REDS.md](./ONSITE_HEX_MEMORY_TWO_REDS.md). This doc focuses on **moving red** paint-over-scoreable / paint-over-teal only.

---

## Symptom / Grid vs Hex

| | Grid | Hex |
|---|------|-----|
| **Symptom** | Moving red hazard visibly covers scoreable tiles while overlapping; tile reverts to scoreable when red moves off | Moving red **does not** cover active scoreable tiles — scoreable color (or memory teal/reveal) stays visible under/over the hazard |
| **Interaction** | Red penalizes when cell is in `red_cells` from priority winners | Red penalizes when cell is in `red_cells`; **but** goal-colored overlaps are excluded from `red_cells` (see classification) |
| **Display source** | Rebuilt each frame from `cell_win` priority map | **Normal:** raw `led_table` copy from Play (no priority pass). **Memory:** partial overlay stack on top of `led_table` |

Grid fixes overlap at **both** classification-for-display and paint time. Hex only applies a custom paint stack in **memory mode** and never applies a display-priority pass in **normal mode**.

---

## Two Scoreable Types (Hex)

### Type 1 — Memory reveal persist (`revealed_colors`)

- **When:** Memory levels only (`YC*` filename prefix, e.g. `YC01.led`, `YCDK02.ledb`).
- **Behavior:** After a goal/deduct/empty-check is consumed, `_mark_revealed()` stores a 3-ring color in `revealed_colors` and keeps it painted for the rest of that tile’s **life** (until respawn, wave jump, or level end).
- **Code:** `_mark_revealed` at ```857:862:api/game_manager.py```; paint loop at ```1592:1593:api/game_manager.py```.
- **Expected:** Red hazard should paint **on top** of reveal paint when moving red sweeps the cell (comment at ```1594:1599:api/game_manager.py```).

### Type 2 — Normal visible scoreable / blank-on-score

- **When:** Non-memory levels (plain `DK*.ledb`, casual `.led`, etc.).
- **Behavior:** Scoring calls `_consume_cell()` which removes the coord from the active group’s `start_member`; tile **blanks** on the next Play redraw (no `revealed_colors`). Active **unscored** scoreables are whatever Play last wrote into `led_table`.
- **Code:** Non-memory goal path at ```1004:1012:api/game_manager.py``` (no `_mark_revealed`); display is ```1563:1565:api/game_manager.py``` only (no overlay).
- **Expected:** While unscored and active, moving red should visually dominate the cell (Grid parity).

---

## Exact Paint Order (with file:line cites)

### A. Play engine (before callback)

`Play.update()` clears the table, draws every in-window group in `dict_group` iteration order (last writer wins), **then** invokes the API callback:

```150:169:games/game_play/Play.py
    def update(self, dict_group, time_pass=0):
        ...
        self.clear_led_table()
        for key, value in dict_group.items():
            ...
                o_led_table.set_color_table_by_set_cell(set_cell, draw_color)
        if self.callback:
            ret = self.callback(self, self.dict_group, time_pass, total_pass)
```

No overlap priority here — arbitrary group order.

### B. Hex classification (interaction sets)

Per-frame floor scan builds `goal_cells`, `goal2_cells`, `red_cells`, `deduct_cells`:

```1388:1449:api/game_manager.py
                        # 2) CLASSIFY floor (normal_led) cells:
                        ...
                            # Goal color OVERRIDES red classification:
                            ...
                            is_red = (not is_deduct and not is_p1_color
                                      and not is_p2_color and _rgb_is_red(mc))
                            ...
                                elif is_red:
                                    red_cells.add((ci, cj))
```

**Critical:** A cell that is both goal-colored and red-colored is added to **`goal_cells` only**, never `red_cells`.

### C. Hex display build (`_frame_callback`)

**Step 0 — Base buffer (all modes):**

```1563:1566:api/game_manager.py
                        led_display = [_normalize_rings(cell)
                                       for row in grid for cell in row]
                        cols = led_table.led_col
```

**Steps 1–4 — Memory mode only** (`if game._memory_mode:`):

```1568:1618:api/game_manager.py
                        # 2a) MEMORY MODE paint order:
                        #   1) teal-hide unscored targets (or bright during reveal)
                        #   2) per-life revealed_colors (scored / deduct / checked empty)
                        #   3) moving red on top (danger always visible)
                        #   4) hint blink
                        ...
                            if goal_cells:
                                ...
                                    led_display[ci * cols + cj] = bright
                            ...
                            for (ci, cj), paint in game.revealed_colors.items():
                                led_display[ci * cols + cj] = [c[:] for c in paint]
                            if red_cells:
                                red_paint = _normalize_rings(red_color_full)
                                for (ci, cj) in red_cells:
                                    led_display[ci * cols + cj] = red_paint
                            if hint_cells:
                                ...
```

**Normal mode:** Steps 1–4 are **skipped** — display stays as Play’s `led_table` composite.

**Step 5 — Flash (all modes):**

```1620:1630:api/game_manager.py
                        # 2b) FLASH: stepped tiles blink white ~0.4s then vanish.
                        ...
                            led_display[fi * cols + fj] = [col[:], col[:], col[:]]
```

### D. Grid reference (working)

**Classification with overlap ranks** (`green > red/deduct > goal > decor`):

```815:852:led-grid/api/game_manager.py
def _classify_floor_groups(groups, *, total_pass, multiplayer, rows, cols):
    """Classify active floor cells with the runtime's overlap priority."""
    winners = {}
    ...
            if previous is None or rank > previous[0]:
                winners[(row, col)] = (rank, category, color)
```

**Display built from winners, not raw `led_table`:**

```1807:1824:led-grid/api/game_manager.py
                        # 2) Build display buffer from the PRIORITY winner map so
                        #    overlapping cells render the WINNING color (green >
                        #    red/deduct > blue/orange), matching interaction.
                        ...
                        for (ci, cj), (rank, cat, mc) in cell_win.items():
                            ...
                                led_display[idx] = [int(mc[0]), int(mc[1]), int(mc[2])]
```

---

## Root Cause

**Primary (confirmed):** Hex has **no display-side overlap priority in normal mode**, and in memory mode the red overlay only touches `red_cells`, which **intentionally excludes** goal-colored overlaps at classification time (```1413:1420:api/game_manager.py```).

When moving red and an active scoreable share a cell:

1. Classification puts the cell in `goal_cells`, **not** `red_cells`.
2. **Normal mode:** `led_display` is a straight copy of Play’s last-writer `led_table`; whichever group painted last in `dict_group` iteration wins — often the scoreable wave, not red.
3. **Memory mode:** Step 1 paints teal-hidden or bright goal on every `goal_cells` coord; step 3 never runs for that coord because it is absent from `red_cells`. `revealed_colors` (type 1) **does** get red on top when the cell is no longer in `goal_cells` — so type-1 overlap bugs mainly affect **unscored** active targets, not post-score reveals.

**Secondary:** Play’s group draw order (```154:165:games/game_play/Play.py```) is non-deterministic with respect to hazard vs goal priority, so even copying `led_table` cannot guarantee red-on-top without a runtime winner map.

**Not the bug:** `revealed_colors` painting **after** goals but **before** red in memory mode (```1592:1599:api/game_manager.py```) — that order is correct; the gap is that `red_cells` never contains goal-overlap coords.

**DK09 nuance:** Goal-over-red in **classification** is correct for **scoring** (P2 goal can be `(254,0,0)`). The fix must split **display winners** from **interaction winners**, not remove the scoring rule.

---

## Affected Modes

| Mode | Levels | Affected? | Mechanism |
|------|--------|-----------|-----------|
| **Normal** | `DK*.ledb`, casual `.led`, non-`YC*` | **Yes — primary** | No overlay pass; raw `led_table` |
| **Memory** | `YC*.led`, `YCDK*.ledb` (`_memory_mode` from ```1288:1289:api/game_manager.py```) | **Yes — unscored active goals** | Goal teal/bright paint without matching `red_cells` entry |
| **Memory — post-score reveal** | Same | **Lower risk** | `revealed_colors` then red overlay should work **if** cell is out of `goal_cells` |
| **2P respawn** | `.ledb` multiplayer | **Yes** when respawned goal overlaps red | Fresh life clears reveal (```1455:1457:api/game_manager.py```) but goal still wins classification |

Grid has no memory mode; it always uses `cell_win` — hence “Grid is fine.”

---

## Proposed Fix Steps (checklist)

### 1. Add display priority helper (hex-specific)

- [ ] Port or adapt Grid’s `_classify_floor_groups` pattern to hex 3-ring colors.
- [ ] Suggested display ranks: `deduct/red hazard (2) > goal/p1/p2 (1) > decor (0)` (add `green` if hex levels use it).
- [ ] Return **`display_winners: dict[(i,j) -> (rank, category, color_full)]`** separate from interaction sets.

### 2. Split interaction vs display classification

- [ ] **Keep** goal-over-red exclusion in interaction/`try_score_cell` paths (DK09).
- [ ] **Do not** use interaction `red_cells` alone for display red paint — derive `display_red_cells` from `display_winners` where `category in ("red", "deduct")`.

### 3. Normal mode display rebuild

- [ ] After ```1563:1565:api/game_manager.py```, replace “trust `led_table`” with painting from `display_winners` (or merge winners onto base decor from `led_table`).
- [ ] Match Grid behavior: overlapping active scoreable + moving red → red visible until red group moves off.

### 4. Memory mode overlay alignment

- [ ] Option A (preferred): Apply memory overlays (teal hide, `revealed_colors`, hint) **first**, then stamp `display_winners` red/deduct on top (same final authority as Grid).
- [ ] Option B: Expand `red_cells` used **only** for display paint, not for `try_score_cell`.
- [ ] Ensure goal teal paint skips cells where display winner is red (avoid painting teal then losing to missing `red_cells`).

### 5. Tests + simulator

- [ ] Add unit test: synthetic overlap → `led_display` cell equals red rings, not goal/teal.
- [ ] Add memory test: unscored goal under red → red wins; post-score `revealed_colors` under red → red wins.
- [ ] Manual simulator check on one normal DK level + one `YC` memory level with moving red mask.

### 6. Hardware verification

- [ ] `USE_SERIAL_HD=1` smoke on venue floor: overlap cell shows red rings on physical hex tile.
- [ ] Confirm DK09-style red goal still **scores** (does not penalize) when stepped.

---

## Test Plan

| # | Scenario | Mode | Setup | Pass criteria |
|---|----------|------|-------|---------------|
| 1 | Active unscored goal under moving red | Normal (`DK01.ledb`) | Simulator or API `led_display` poll during overlap | Cell RGB matches red group’s 3-ring color, not goal color |
| 2 | Same overlap | Memory (`YC01.led`) | Before stepping the goal | Red visible on overlap (not teal-hidden) |
| 3 | Post-score reveal under red | Memory | Score a goal, wait for red sweep | `revealed_colors` paint replaced by red while overlapping |
| 4 | Red moves off | Both | After overlap ends | Scoreable color/teal returns |
| 5 | DK09 red goal | 2P memory/normal | Step red-looking **goal** tile | +1 score, no HP loss (interaction unchanged) |
| 6 | Grid parity spot-check | Grid | Same level geometry if available | Hex matches Grid overlap appearance |
| 7 | Hardware | Hex HW | `test_hardware.py` or live play | Physical rings show red on overlap |

### Suggested automated test sketch

```python
# tests/test_display_red_over_goal.py
# Build minimal dict_group with two concurrent FLOOR_LIGHT groups sharing (r,c):
# one goal-colored, one red. Run classification + display build helpers.
# Assert led_display[r,c] normalizes to red rings.
```

### Regression watchlist

- Memory teal-hide during non-reveal window (should not return if red is on cell).
- Hint blink (```1609:1618:api/game_manager.py```) — decide if hint or red wins on hint cell overlap.
- White hit flash (```1620:1630:api/game_manager.py```) — should remain topmost.
- 2P respawn + `_clear_cell_reveal` (```1455:1457:api/game_manager.py```).

---

## Key Files

| File | Role |
|------|------|
| `api/game_manager.py` | Classification, memory overlays, `led_display` publish |
| `games/game_play/Play.py` | Pre-callback `led_table` compositing |
| `led-grid/api/game_manager.py` | Reference implementation for overlap priority |

---

## Summary for implementers

1. **Grid works** because display is built from `cell_win` where red rank > goal rank.  
2. **Hex breaks** because normal mode publishes Play’s unprioritized buffer, and memory mode paints red only onto `red_cells` that exclude goal overlaps.  
3. **Fix** = add display priority (like Grid) while keeping goal-wins-red for **scoring** only.  
4. **Type 1** (`revealed_colors`) overlay order is already red-last in memory — fix classification/display set for overlaps.  
5. **Type 2** (normal active scoreables) needs the normal-mode display rebuild — biggest visible gap.
