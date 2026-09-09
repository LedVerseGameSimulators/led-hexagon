# Hex Memory Mode — Two Kinds of Red

> Plain reference for onsite. Memory levels = filename starts with `YC` (1P) or `YCDK` (2P).

---

## Quick summary

Memory levels hide scoreable tiles under **teal**. There are two different “red” hazards:

| Kind | What it is | Player sees | After stepped |
|------|-----------|-------------|---------------|
| **A — Moving red** | Red floor group with `speed ≠ 0` | Always visible while sweeping | Penalty every frame (rate-limited). No reveal. |
| **B — Hidden red** | DEDUCT tile `(254, 0, 48)` under teal | Looks like teal until stepped | −score, −HP, tile **stays revealed** until retile / wave jump / level end |

---

## A — Moving red

- Sweeps across the board like a normal hazard.
- **Must paint on top of** active scoreables **and** teal-hidden tiles.
- Code intent: memory paint stack puts red last (step 3 in `_frame_callback`).
- **Known bug:** In some levels, moving red does **not** cover teal or unscored goals. Root cause: overlap cells go into `goal_cells`, not `red_cells`, so the red paint step skips them. See [ONSITE_HEX_RED_OVER_SCOREABLE.md](./ONSITE_HEX_RED_OVER_SCOREABLE.md).

**Levels with moving red (SP):** YC09, YC10, YC12, YC14, YC16, YC18 (6 of 18).

**Levels with moving red (2P):** DK01, DK03, DK04, DK07, DK08, DK09, YCDK07, YCDK09 (moving-red groups; most are static-red fields, not sweepers).

---

## B — Hidden red (DEDUCT under teal)

- Authored as DEDUCT color `(254, 0, 48)` in level data.
- Display: covered by teal like any unscored tile (`TEAL_HIDDEN` paint).
- On step:
  1. Penalty (−score, −HP).
  2. `_mark_revealed()` paints the true deduct color.
  3. `revealed_live_red` keeps hurting if player stands on it.
  4. Tile consumed (removed from group); in 2P, respawns after 8 s.
- **Stays revealed** until: respawn, auto-jump to next wave, or level end. `_clear_cell_reveal()` runs on those events.

**Levels with hidden deduct (SP):** all 18 YC01–YC18.

**Levels with hidden deduct (2P):** YCDK02–YCDK06, YCDK08–YCDK11, Mind level 01 (9 of 10 memory 2P levels).

---

## How this differs from Grid

| | Grid | Hex memory |
|---|------|------------|
| Teal hide | No | Yes — unscored goals hidden |
| Hidden traps | No | Yes — DEDUCT under teal |
| Moving red over goals | Works (display priority map) | **Broken** on overlap (see red-over-scoreable doc) |
| Post-hit reveal | N/A | Revealed color persists for tile life |
| 2P respawn | **Disabled** | **Enabled** (8 s) — causes infinite retiling on some 2P boards |

Grid has no memory mode. Do not copy Grid paint logic blindly — Hex needs memory overlays **plus** a display-winner pass for moving red.

---

## Fix checklist

### Moving red over teal / goals
- [ ] Split **display** winners from **scoring** winners (goal still beats red for score, red wins for paint).
- [ ] Paint red on overlap coords even when cell is in `goal_cells`.
- [ ] Test: YC09 with moving red sweeping an unscored teal tile → red visible.
- [ ] Test: post-reveal cell under moving red → red visible.

### Hidden red reveal
- [ ] Confirm deduct step calls `_mark_revealed` + `revealed_live_red` (already in code).
- [ ] Confirm reveal clears on respawn / wave jump (`_clear_cell_reveal`, `_clear_all_reveals`).
- [ ] Test: step hidden deduct → stays red-ish deduct color until wave ends.

### 2P respawn interaction
- [ ] Hidden deduct that respawns should start hidden again (fresh life clears reveal — line ~1455).
- [ ] See [ONSITE_HEX_2P_RETILING_SWEEP.md](./ONSITE_HEX_2P_RETILING_SWEEP.md) for marathon / infinite-board levels.

---

## Key code

| What | Where |
|------|-------|
| Memory mode flag | `_memory_mode = stem.startswith("YC")` |
| Teal hide + red overlay | `_frame_callback` memory paint block |
| Hidden deduct scoring | `try_score_cell` → `deduct_cells` branch |
| Reveal persist | `revealed_colors`, `revealed_live_red` |
| Reveal clear | `_clear_cell_reveal`, `_clear_all_reveals` |
