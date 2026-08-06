# LED Hexagon (Battle Arena) — effects spec

Audio, countdown, and hex-floor behavior for **LED Hexagon / Battle Arena**.

Global rules: [activerse_final_changes/docs/game-effects/GLOBAL_RULES.md](../../docs/game-effects/GLOBAL_RULES.md)

Matrix reference: [GRID_MATRICES.md](../../docs/game-effects/GRID_MATRICES.md)

---

## Hex floor layout (not 16×26)

Onsite hardware uses a **hexagonal** floor, not a full rectangular grid.

| Property | Value |
|----------|--------|
| **Coordinate grid** | **5 rows × 9 columns** (bounding box) |
| **Live hex tiles** | **33** (single COM port, 33 `normal_led` entries) |
| **Dead cells** | **12** — corners / edges with no physical tile |
| **Layout type** | `1` (hex) |
| **Per tile** | **3 concentric RGB rings** (outer, mid, inner) |

### Footprint

```
Cols:  0  1  2  3  4  5  6  7  8
Row 0: X  X  X  X  .  X  X  X  X
Row 1: .  X  .  X  .  X  .  X  .
Row 2: .  .  .  .  .  .  .  .  .
Row 3: .  .  .  .  .  .  .  .  .
Row 4: .  .  .  .  .  .  .  .  .
```

`.` = live hex tile, `X` = dead (no tile). Odd rows are **staggered** on the
physical floor.

> Some repo docs still mention 16×26 from level-authoring / legacy code paths.
> **Effects patterns** (countdown, clear, fail) should be designed on this
> **5×9 hex footprint** with only the **33 live cells** lit.

---

## Audio assets

| Asset | File / source |
|-------|---------------|
| **BGM** | TRON *End of Line* — level play only |
| **Positive score SFX** | Shared positive MP3 (cross-game) |
| **Negative score SFX** | Shared negative MP3 (cross-game) |
| **Countdown** | Tick/noise during 3-2-1; **no BGM** |
| **Level transition** | Short stinger ~2–3 s (asset TBD / stock OK) |

---

## Countdown (every level start)

**TBD** — design against the 5×9 hex footprint (33 live tiles).

---

## Level clear / fail / timer

**TBD** — patterns and diagram pending (same global flow as other games:
transition stinger → countdown → next level or restart; session end → black).

---

## Reference media

Capture and timing reference: **`~/Downloads/Battle Arena/`**

Use for LED pattern design only — not frontend video playback.
