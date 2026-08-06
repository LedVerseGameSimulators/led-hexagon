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

Runs before **every level** — first level of the session, after level clear,
and after level fail restart. **Not** repeated when the session has ended.

Tick/noise audio; no BGM. All **33 live hex tiles** lit (all 3 rings same color).

| Step | Duration | Pattern |
|------|----------|---------|
| **3** | ~0.8 s (suggested) | **All red** |
| **2** | ~0.8 s | **All blue** |
| **1** | ~0.8 s | **All green** |
| **Start** | — | Level play begins (BGM on) |

UI countdown and floor stay in sync. Floor shows solid colors only (no digits).

---

## Level clear

**All 33 live hex tiles → solid green** (all 3 rings).

1. Hold ~2–3 s with transition stinger (not BGM)
2. **Countdown** (3 red → 2 blue → 1 green)
3. **Next level** play begins

Timer expire uses the **same** clear pattern (all green).

If session ends after final clear → all tiles **black / off** (**no** countdown).

---

## Level fail

**All 33 live hex tiles → solid red** (all 3 rings).

Triggered when **all lives are lost**.

1. Hold ~2–3 s with transition stinger (not BGM)
2. **Countdown** (3 red → 2 blue → 1 green)
3. **Same level** restart play begins

---

## Timer expire

Same as **level clear** (all green) → stinger → countdown → next level or session end.

---

## Reference media

Capture and timing reference: **`~/Downloads/Battle Arena/`**

Use for LED pattern design only — not frontend video playback.
