# Onsite — Long Levels (Hex + Hoops)

> **Generated:** 2026-09-09  
> **Purpose:** When operators report **“level not finishing”**, distinguish **content that is too long** (many waves / bad timestamps) from **code bugs** (clear detection, display, gc-shift). Same playbook applies to Hex and Hoops.

> **Product rule (Hoops)**  
> 1. Most levels: no more than **10 scoreable waves**. **Exceptions:** `Challenge - 85 Hoops` and `Challenge -- 85 Hoops` (long marathons — keep as-is).  
> 2. Wave timing is **authored per level** (`end_time_sec`) — inspect each file; do not assume one pattern.  
> 3. **33 levels** need trim under the cap (35 over 10, minus 2 Challenge exceptions).  
> 4. Fix by **dropping excess waves** in level archives — see [PLAN_HOOPS_MAX_10_WAVES.md](./PLAN_HOOPS_MAX_10_WAVES.md).

---

## Executive summary

| Game | SP levels | Session default | board > session | Primary “too long” signal |
|------|----------:|----------------:|----------------:|---------------------------|
| **Hex** | 35 | 300 s | **35 / 35** (all 600 s board) | Usually **not** length — clears via scoreables; see code categories A/C |
| **Hoops** | 25 | 300 s | **16 / 25** | **Wave count** (up to **106**); **1 level broken** (`--/16`) |

**Product fact (both games):** `board_time_sec` is often **600 s** while `game_time_sec` is **300 s**. That alone does **not** mean a level is broken — advance is driven by **clearing scoreables** (with wave-skip in Hoops), not running the board clock out. On Hoops, `board_time_sec = 600` often comes from **decoration** groups, not scoreable wave length.

**When length *is* the problem:** so many waves or so late a final wave that a typical player cannot clear the level before the **300 s session** ends — or a **data error** places scoreables after the session window.

---

## Method (shared)

1. Open `.led` / `.ledb` under `games/source/` as **zip**.
2. Extract; find main `game_file` shelve (`play_order=False`).
3. `shelve.open` with game `model` on `PYTHONPATH`.
4. Read `dict_group` → per-group `start_time_sec`, `end_time_sec`, `type`, `color`, `start_member`, `speed`.
5. Derive `board_time_sec = max(end_time_sec)` and scoreable-wave counts per game rules.

**Hex detail:** [led-hexagon/docs/ONSITE_HEX_SP_LEVEL_SWEEP.md](../led-hexagon/docs/ONSITE_HEX_SP_LEVEL_SWEEP.md)  
**Hoops detail:** [led-hoops/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md](../led-hoops/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md)

---

## Session timer defaults

| Game | `game_time_sec` | Source |
|------|----------------:|--------|
| Hex | 300 | `game_time_sw` = 5 min |
| Hoops | 300 | `api/game_manager._SETTINGS_DEFAULTS` / `led_parameter` |

Hoops also sets `GAME_TIMEOUT_SECONDS = 600` in `api/config.py` (process-level guard, not player UI).

---

## Hex findings (cited)

From [ONSITE_HEX_SP_LEVEL_SWEEP.md](../led-hexagon/docs/ONSITE_HEX_SP_LEVEL_SWEEP.md):

| Category | Count | % of 35 SP |
|----------|------:|----------:|
| Total SP | 35 | 100% |
| **E** board_time > 300 s | **35** | **100%** (all `board_time_sec = 600`) |
| **A** moving red + scoreables | 12 | 34% |
| **B** start cadence ≥ 10 s | 5 | 14% |
| **C** gc-shift (Pro 04) | 1 | 3% |
| **D** memory (YC*) | 18 | 51% |
| Unreachable last scoreable | 0 | — |

**Hex implication for “long level” reports:** With wave-skip and stagger, pro levels complete well under 300 s in practice. Reports of non-finishing Hex levels should prioritize **code** (red-over-scoreable, Pro 04 gc-shift, memory reveal) per the sweep — **not** shortening all boards from 600 s.

---

## Hoops findings (2026-09-09 sweep)

From [ONSITE_HOOPS_SP_LEVEL_SWEEP.md](../led-hoops/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md):

### Summary table

| Metric | SP | 2P |
|--------|---:|---:|
| Levels scanned | 25 | 10 |
| board_time > 300 s | 16 | 5 |
| board_time = 600 s | 5 | 5 |
| Waves ≥ 50 | 5 | 3 |
| Waves ≥ 70 | 3 | 1 |
| Last wave start > 300 s | **1** | 0 |
| Est. not completable @ 3 s/shot | **2** (007, 008) | — |

### Top 10 longest (by wave count)

| Level | Waves | board_time | Last wave @ |
|-------|------:|-----------:|------------:|
| `-/007` | 106 | 220 s | 214 s |
| `-/008` | 106 | 226 s | 220 s |
| `-/011` | 70 | 252 s | 246 s |
| `-/001` | 52 | 260 s | 255 s |
| `-/Challenge - 85 Hoops` | 52 | 594 s | 281 s |
| `-/Challenge -- 85 Hoops` | 48 | 600 s | 235 s |
| `--/15` | 46 | 596 s | 225 s |
| `-/009` | 44 | 595 s | 215 s |
| `-/004` | 43 | 595 s | 210 s |
| `-/005` | 43 | 594 s | 252 s |

### Blocking content bug

**`--/16`:** scoreable waves every 6.5 s through t=195 s, then a **1018.5 s gap**, final wave at **t=1213.5 s**. Level cannot clear in any 300 s session. **Content fix required** (move/remove orphan group).

---

## Hex vs Hoops — pattern comparison

| Dimension | Hex | Hoops |
|-----------|-----|-------|
| board_time = 600 s | Universal (35/35) | Common on hard tiers (5/25 SP; 5/10 2P) |
| Wave mechanism | Goal color phases + floor scoreables | Scoreable hoop columns; **micro-waves** every ~2–6 s |
| Typical wave count | Tens of goal windows; 4–15 staggered pro groups | **20–106** scoreable start times |
| Dead gaps ≥ 10 s | 0 (scoreables overlap) | 0 except **`16` bug** and `24` (11 s design) |
| “Too long” root cause | Rare for SP; session vs marathon | **Wave volume** + one bad timestamp |
| Recommended first fix | Code (A/C/D categories) | **Content trim** on flagged levels; code for skip/clear/HW |

---

## Recommendations

### Content-trim candidates (Hoops)

Drop excess scoreable waves to ≤10 — **keep authored durations** on waves you keep. **Do not** trim Challenge marathons. **Do not** add a new game mode.

| Priority | Level(s) | Action |
|----------|----------|--------|
| P0 | `--/16` | Fix orphan wave at 1213.5 s (delete or move) |
| P1 | `-/007`, `-/008` | Drop excess waves (106 → ≤10); keep kept waves’ timing |
| P2 | `-/011`, `-/001`, other SP over cap | Same drop-excess approach; judge subset per file |
| — | `Challenge - 85 Hoops`, `Challenge -- 85 Hoops` | **Exempt** — leave as-is |
| P3 | 2P `DK*.ledb` | Only if product wants 2P under same cap |

### Code fixes (both games)

| Issue | Game | Action |
|-------|------|--------|
| Level clear when all scoreables done | Hoops | Verify wave-skip + `_level_cleared` on 007/008 onsite |
| Red not visible over scoreable | Hex | Display priority ([RED doc](../led-hexagon/docs/ONSITE_HEX_RED_OVER_SCOREABLE.md)) |
| gc-shift premature clear | Hex Pro 04 | Code handles transition |
| Moving red overlap | Hoops `17`, `21` | Verify priority map on hardware |
| Session timeout vs level in progress | Both | Expected at 300 s — distinguish from per-level clear failure |

### Hex — generally **not** content-trim for length

Per Hex sweep: **do not edit level files** for category E (600 s board). Focus onsite smoke on **Pro 03/04/05** and category A/D.

---

## Suggested onsite test order

### Hoops (length-focused)

1. `--/16` — must fail to clear (document before/after content fix)
2. `-/007` or `-/008` — stopwatch full clear; note session remaining
3. `-/011` — late finale under time pressure
4. `-/006` or `-/018` — short baseline (board < 220 s)
5. 2P `DK05` — long 2P board

### Hex (code-focused; length baseline)

1. Pro **04** (gc-shift @ 60 s)
2. Pro **03**, **05** (moving red)
3. Pro **00** (40 s stagger — confirm auto-jump)
4. Baseline **07**, **12** (no A–D flags)

### Cross-game regression

After Hoops content trim on `16`: replay `16` → `007` in one 300 s session and confirm at least one level clear + advance.

---

## Related docs

| Doc | Path |
|-----|------|
| Hex SP sweep | [led-hexagon/docs/ONSITE_HEX_SP_LEVEL_SWEEP.md](../led-hexagon/docs/ONSITE_HEX_SP_LEVEL_SWEEP.md) |
| Hoops SP sweep | [led-hoops/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md](../led-hoops/docs/ONSITE_HOOPS_SP_LEVEL_SWEEP.md) |
| Hex work index | [ONSITE_HEX_WORK_INDEX.md](./ONSITE_HEX_WORK_INDEX.md) |
| Hex red over scoreable | [led-hexagon/docs/ONSITE_HEX_RED_OVER_SCOREABLE.md](../led-hexagon/docs/ONSITE_HEX_RED_OVER_SCOREABLE.md) |
