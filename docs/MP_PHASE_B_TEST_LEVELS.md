# Hex — MP Phase B test levels

**Date:** 2026-09-17  
**Scope:** Team Battle (`.ledb`) either-player wave advance + vacuous-empty latch.  
**Parent:** `docs/PLAN_MULTIPLAYER_SCORING_AND_HUD.md`

---

## Quick start (Team Battle)

1. Start API + frontend (`scripts/start-dev.sh` or `START_GAME.bat`).
2. Mode → **Team Battle** → pick a level → RFID or Play without RFID for both players.
3. Confirm HUD shows `multiplayer: true` and 3-ring goal swatches (Phase A).

---

## Phase A + B verify checklist

| # | Check | Pass? |
|---|--------|-------|
| A1 | Plain red / DEDUCT in TB → life only (scores flat) | |
| A2 | 1P `.led` red still deducts score + life | |
| A3 | HUD shows P1/P2 3-ring swatches | |
| A4 | Normal level hurt SFX on red/DEDUCT; score SFX on goals | |
| B1 | Staggered wave: clear P1 tiles while P2 tiles remain → wave jumps without waiting | |
| B2 | P1-only wave (no P2 tiles lit) → does **not** false-advance until P1 clears | |
| B3 | After either-player discard → no ghost respawn on dropped P2/P1 cells | |
| B4 | Memory (YCDK): discarded cells lose teal/reveal paint; no ghost traps | |

---

## Recommended `.ledb` levels (`games/source/---/`)

| Level | Why |
|-------|-----|
| **DK01** | Baseline 2P; staggered P1/P2 waves — primary either-advance smoke |
| **DK02** | Alternate pacing / color mix |
| **DK03** | Same-color 2P (checkerboard split) — discard must respect P1/P2 partition |
| **DK04–DK06** | Mid-tier DK pacing sweeps |
| **DK09** | P2 goal color looks red — classification must not confuse hazard vs goal |
| **YCDK02** | Memory + 2P; reveal/discard interaction |
| **YCDK05** | Memory deduct + goals |
| **YCDK08–YCDK10** | Longer memory 2P marathons |

### 1P regression (unchanged)

| Level | Path |
|-------|------|
| Casual tier | `games/source/-/001.led` |
| Advanced tier | `games/source/--/14.led` |

---

## Pytest

From `led-hexagon/`:

```bash
python -m pytest tests/test_mp_phase_a.py tests/test_mp_phase_b.py -q
python -m pytest tests/test_masked_goal_grace.py tests/test_gc_shift_remaining.py -q
```

Full MP-related suite:

```bash
python -m pytest tests/test_mp_phase_a.py tests/test_mp_phase_b.py \
  tests/test_masked_goal_grace.py tests/test_gc_shift_remaining.py \
  tests/test_respawn_cap.py -q
```
