# LED Hexagon (Battle Arena) — effects spec

Audio, countdown, and hex-floor behavior for **LED Hexagon / Battle Arena**.

Global rules: [activerse_final_changes/docs/game-effects/GLOBAL_RULES.md](../../docs/game-effects/GLOBAL_RULES.md)  
Locked decisions: [LOCKED_DECISIONS.md](../../docs/game-effects/LOCKED_DECISIONS.md)  
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
physical floor. Rows 2–4 are **fully live** (9 tiles each).

> Some repo docs still mention 16×26 from level-authoring / legacy code paths.
> **Effects patterns** (countdown, clear, fail) should be designed on this
> **5×9 hex footprint** with only the **33 live cells** lit (authoritative coords
> from onsite shelve `games/setting/led_parameter`).

---

## Effect `.led` files (exactly three)

All effect assets live under `games/source/effects/`:

| File | Purpose |
|------|---------|
| **`countdown.led`** | One file with **three timed groups** (3→2→1 @ ~0.8 s each) — **not** three separate countdown files |
| **`level_clear.led`** | Solid green hold (~2.5 s) on all 33 live tiles |
| **`level_fail.led`** | Solid red hold (~2.5 s) on all 33 live tiles |

Each group covers all 33 live `(row,col)` members; dead cells stay black. All
three rings per tile use the same RGB (solid outer/mid/inner).

---

## Audio assets

| Asset | File / source |
|-------|---------------|
| **BGM** | TRON *End of Line* — level play only |
| **Positive score SFX** | Shared positive MP3 (cross-game) |
| **Negative score SFX** | Shared negative MP3 (cross-game) |
| **Countdown** | Tick/noise during 3-2-1; **no BGM** |
| **Level transition** | `games/audio/transition_stinger.mp3` (~2–3 s) — **one shared file** for clear **and** fail |

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

UI countdown and floor countdown **both run**; keep **approximately in sync**
(floor from backend `countdown.led`; UI countdown stays). Floor shows solid
colors only (no digit glyphs).

---

## Level clear

**All 33 live hex tiles → solid green** (all 3 rings).

1. Hold ~2–3 s with transition stinger (not BGM)
2. **Countdown** (3 red → 2 blue → 1 green)
3. **Next level** play begins

If more levels remain: clear → stinger → countdown → next level play.

---

## Timer expire (= session end)

Same LED treatment as **level clear** (all green).

1. Hold ~2–3 s with transition stinger (not BGM)
2. All tiles **black / off**
3. **No countdown** — session is over

Also applies when **last level is cleared** with time remaining, or when
**all lives are lost with ≤10 s session time left** (session end — no fail
panel, no countdown).

---

## Level fail

**All 33 live hex tiles → solid red** (all 3 rings).

Triggered when **all lives are lost** and **>10 s session time remains**.

1. Hold ~2–3 s with transition stinger (not BGM)
2. **Countdown** (3 red → 2 blue → 1 green)
3. **Same level** restart play begins

---

## Reference media

Capture and timing reference: **`~/Downloads/Battle Arena/`**

Use for LED pattern design only — not frontend video playback.
