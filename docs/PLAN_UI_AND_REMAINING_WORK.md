# Hex — UI redesign + remaining work

**Date:** 2026-09-16  
**Repo:** `led-hexagon`  
**Parent:** `docs/PLAN_FE_REDESIGN_AND_WORK_INDEX.md`

---

## Locked product rules

| Topic | Decision |
|-------|----------|
| Screen order | **Keep today:** Mode → Settings* → Login → Play (*Tournament skips settings) |
| Modes | Quick Play (1P) · Team Battle (2P) · Tournament (group) |
| Levels | QP/TB: **20** placeholders each · Tournament: existing ~10, **no** level pick |
| Login | Always **RFID** or **Play without RFID** → random names, **no name form** |
| Level labels | UI shows **1, 2, 3…** (HUD + results); backend keeps file ids |
| Countdown | **Both** TV overlay + floor `countdown.led` |
| Video | One bg loop: `frontend/public/media/background.mp4` |
| Landscape | Only |

---

## Implementation status (Hex shell)

### Done (this pass)
- [x] Mode rename: Quick Play / Team Battle / Tournament  
- [x] Settings: 1–20 grid (no category/difficulty picker)  
- [x] Placeholder playlists in `frontend/src/levelPlaylists.js`  
- [x] Login: Play without RFID → instant random names  
- [x] Tournament/all modes: `formatLevelLabel` on HUD + results  
- [x] Video background on mode / settings / login / results  
- [x] Short how-to copy on settings  

### Next on Hex
- [ ] Polish restyle closer to mock JPEGs (typography / cards)  
- [ ] Swap placeholder 20-level lists when team delivers  
- [x] MP Phase A — lives-only hazards, 3-ring HUD swatches, normal-level SFX  
- [x] MP Phase B — either-player wave advance + discard (see `docs/MP_PHASE_B_TEST_LEVELS.md`)  
- [ ] Floor effects HW RCA (separate)  

### Later (other games)
Copy this shell to Grid / Hoops / Climb / Laser (Laser = 2 modes only).

## Product Q&A (2026-09-17 MP Phase A)

- Team Battle **DEDUCT = lives only** (no score) — **final for now** (Hex / Climb / Grid).
- Keep **red cooldown** vs **DEDUCT one-shot** asymmetry.
- Climb DK packs may omit DEDUCT today; later levels may add it — OK.
- Hex **normal** levels: hurt SFX on red/DEDUCT hits; score SFX on scoreable hits (P1 and P2).
- Stale “2P red hits both scores” comments updated to lives-only wording.
