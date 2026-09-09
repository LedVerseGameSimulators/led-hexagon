# Hex 2P Retiling Sweep

> **Date:** 2026-09-09  
> **Scope:** `games/source/---/*.ledb` (22 files).  
> **Question:** Why do some 2P levels never finish? Is respawn the cause?

---

## Short answer

**Yes — code respawn is the main cause of infinite retiling.**

Hex multiplayer still respawns consumed tiles after **8 seconds**:

```1050:1050:led-hexagon/api/game_manager.py
        reappear_at = time.time() + self.respawn_delay if self.multiplayer else None
```

Grid **disabled** respawn for both 1P and 2P:

```1344:1344:led-grid/api/game_manager.py
        reappear_at = None  # respawn disabled — clear progression for 1P + 2P
```

Hoops also has **no respawn** in `_consume_cell` — consumed cells stay gone.

When a 2P level has all scoreables active from t=0 with no wave stagger, respawn refills the board forever. The level-clear check (`remaining_scoreable == 0`) never stays true.

---

## Key numbers

| Metric | Count |
|--------|------:|
| 2P `.ledb` files scanned | **22** |
| Memory (`YCDK*`) | **10** |
| `board_time = 600 s` (all) | **22** |
| Session cap | **300 s** |
| Respawn-dependent (t=0 only, no stagger) | **7** |
| Staggered (2–11 waves, can finish without respawn) | **15** |
| Moving-red groups | **7** levels |
| Hidden deduct (memory traps) | **10** levels |
| Marathon (50+ goal-indicator windows) | **0** at content level* |

\*DK05/07/09 have huge static-red fields (4800 / 1328 / 608 cells) but only one scoreable wave — marathon feel comes from respawn + red fields, not wave count.

---

## Respawn-dependent levels (infinite retiling)

These have **one scoreable wave at t=0**, no stagger. Without respawn they would clear once; with respawn they refill every 8 s:

| Level | Unique scoreable coords | Notes |
|-------|------------------------:|-------|
| **DK01** | 30 | Classic 2P starter; 1 moving-red group |
| **DK04** | 36 | Same pattern |
| **DK08** | 32 | Same pattern |
| **DK10** | 20 | Same pattern |
| **DK05** | 32 | + 4800 static-red cells (marathon hazard board) |
| **DK07** | 24 | + 1328 static-red cells |
| **DK09** | 24 | + 608 static-red cells; P2 goal can look red |

**4 pure infinite-retile** (DK01, DK04, DK08, DK10): small boards designed around respawn refresh, like Hoops marathon mode.

**3 hazard marathons** (DK05, DK07, DK09): same respawn loop plus massive static-red fields.

---

## Staggered levels (can finish)

These have **2–11 distinct scoreable start times**. Disabling respawn should let wave-skip + clear detection advance the level:

| Level | Waves | Memory | Hidden deduct |
|-------|------:|:------:|:-------------:|
| DK02 | 3 | No | — |
| DK03 | 2 | No | — |
| DK06 | 11 | No | — |
| DK11 | 6 | No | — |
| Mind level 01 | 2 | No | 4 cells |
| YCDK02–YCDK06 | 2 each | Yes | 8–20 cells |
| YCDK08–YCDK10 | 2 each | Yes | 6–12 cells |
| YCDK11 | 2 | Yes | 606 cells (outlier) |

---

## Code vs content

| Issue | Owner | Notes |
|-------|-------|-------|
| Infinite retiling on DK01/04/08/10 | **Code** | Option A: disable respawn (match Grid). Option B: cap at 8 respawns per tile |
| DK05/07/09 marathon feel | **Code + content** | Respawn + huge red fields; trim red cells if needed |
| YCDK11 606 deduct cells | **Content** | Likely authoring error — review before onsite |
| Memory hidden deduct reveal | **Code** | Works; see [ONSITE_HEX_MEMORY_TWO_REDS.md](./ONSITE_HEX_MEMORY_TWO_REDS.md) |
| Level never advances in staggered 2P | **Code** | Check respawn refilling cells inside active wave window |

---

## Recommendation

Pick one product option for 2P respawn levels:

### Option A — Disable respawn (match Grid)

Set `reappear_at = None` in `_consume_cell` (```1050:1050:led-hexagon/api/game_manager.py```) like Grid. One-line change. Levels clear once all scoreables are consumed.

### Option B — Max 8 respawns per tile (preferred for respawn levels)

Keep the refresh feel but stop infinite retiling. **Per tile**, not per level — same `(i,j)` already flows through `_consume_cell` → `pending_respawn` → `process_respawns`.

**Concrete implementation:**

1. On `GameInstance`: `self.respawn_counts = {}`  # `(i,j) -> int`; clear in `reset_for_level` (alongside `pending_respawn` at ```688:688:led-hexagon/api/game_manager.py```).
2. In `_consume_cell`, before `pending_respawn.append(...)` (```1066:1067:led-hexagon/api/game_manager.py```): if `self.respawn_counts.get((i,j), 0) >= 8`, skip enqueue (set `reappear_at` effectively unused for that consume). Else increment count and append as today.
3. `process_respawns` unchanged — it only re-adds cells already queued.

Each tile gets up to **8** comebacks (~64 s at 8 s delay), then stays gone. DK01 (30 tiles) still finishes; staggered levels unaffected once active wave cells are exhausted.

### After either option

1. **Smoke test:** DK02 (staggered, should clear), DK01 (was infinite — clears once with A, or after bounded refresh with B).
2. **Content trim** only if still too long: DK05/07/09 red fields, YCDK11 deduct count.
3. Do **not** trim staggered YCDK levels — they should complete naturally once respawn is bounded or off.

---

## Related docs

- [ONSITE_HEX_MEMORY_TWO_REDS.md](./ONSITE_HEX_MEMORY_TWO_REDS.md) — hidden deduct vs moving red
- [ONSITE_HEX_RED_OVER_SCOREABLE.md](./ONSITE_HEX_RED_OVER_SCOREABLE.md) — moving red paint bug
- [LEVELS.md](./LEVELS.md) — tier overview, respawn notes
