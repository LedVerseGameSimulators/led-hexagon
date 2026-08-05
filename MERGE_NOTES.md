# Onsite merge notes — led-hexagon — 2026-08-03

**Branch:** `merge/onsite-takeaway-2026-08-03`  
**Base:** `main` @ `be34581`  
**Source zip:** `led-hexagon-onsite-updated-2026-08-03.zip`  
**Extract:** `.onsite-analysis/led-hexagon/led-hexagon/`

## Summary

Small delta merge porting onsite hardware serial-flag wiring (dark-floor fix),
operator one-click start/stop, and venue shelve editable flags. Memory mode,
3-ring protocol, and frontend remain unchanged (verified identical after CRLF
normalize).

## Changes ported (TAKE from onsite)

| File | Change |
|------|--------|
| `api/game_manager.py` | `_hw_init()` forces `Setting.USE_SERIAL_HD = True` when env `USE_SERIAL_HD=1` — fixes dark floor (led_control gates on Setting, not env alone) |
| `games/test_hardware.py` | Same Setting override + diagnostic print |
| `START_GAME.bat` | One-click operator start (ports 8004/8767/5177, `USE_SERIAL_HD=1`) |
| `STOP_GAME.bat` | Clean shutdown by window title + port kill |
| `OPERATOR_GUIDE.md` | Studio operator instructions (COM9, 33 tiles) |
| `games/setting/led_parameter.*` | `game_time_editable_sw` and `life_value_editable_sw` → **True** (venue ops need editable time/lives) |
| `HARDWARE_VALIDATION.md` | Amended (not replaced): COM9 venue confirmation + Setting gate / dark-floor fix notes |

## Kept local (not overwritten)

| File | Reason |
|------|--------|
| `.gitignore` | Local tracks shelve; onsite ignores all `*.dat` |
| `games/model/setting.py` | Default `USE_SERIAL_HD = False` (safer for sim); force in `_hw_init` at runtime |
| `games/led/*` | 3-ring protocol identical |
| `frontend/src/**` | Identical to onsite |
| `HARDWARE_VALIDATION.md` reveal-on-hit § | Local ahead of onsite — preserved |
| `games/setting/runtime_overrides.json` | Local only |
| `games/setting/ledplaydb.sqlite` | Runtime DB — not committed |
| `frontend/.env` | Deploy-only RFID URL |

## Blockers

None. All planned hunks applied cleanly.

## Tests

| Test | Result |
|------|--------|
| `python3 games/test_headless.py` | **PASS** (6/6) |
| `pytest` | No pytest suite in repo |
| `py_compile api/game_manager.py games/test_hardware.py` | **PASS** |

## Deploy notes

- Site: `git pull` on this branch (or after merge to `main`).
- Copy/create `frontend/.env` with site RFID IP (do not commit).
- Keep venue `ledplaydb.sqlite` for leaderboard history.
- Use `START_GAME.bat` / `STOP_GAME.bat` on the Hexagon PC.
- 9 unicode-named asset paths failed Mac extract — not gameplay-critical; restore from zip on Windows if needed.

## Hardware revalidation checklist

See `HARDWARE_VALIDATION.md` §6. Priority checks after deploy:

- [ ] Sim: `USE_SERIAL_HD=0` still works
- [ ] HW: `USE_SERIAL_HD=1` → floor lights before gameplay (Setting sync)
- [ ] Memory mode reveal-on-hit on real floor
- [ ] Group + RFID on kiosk
- [ ] `STOP_GAME.bat` clean shutdown
