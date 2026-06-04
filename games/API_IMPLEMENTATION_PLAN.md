# API Implementation Plan: LED Hex

**Status:** Primary implementation target (has simulator for testing)

---

## Files Used in API

### Required (will be imported)
- ✅ `game_play/Play.py` — Main game loop
- ✅ `game_play/game_hw.py` — LED hardware control
- ✅ `database/db_operation.py` — Database queries
- ✅ `model/setting.py` — Game constants/settings
- ✅ `source/` — Level data files
- ✅ `simulator/` — Local testing (NOT deployed)

### Not Needed (skipped in API)
- ❌ `gui/gui_game_main.py` — Tkinter display (React replaces)
- ❌ `gui/gui_player_login.py` — Login UI (React replaces)
- ❌ `gui/gui_editor_game.py` — Editor (React replaces)
- ❌ `gui/gui_editor_game2.py` — Editor (React replaces)
- ❌ All other `gui/` files — UI only (React replaces)
- ❌ `main.py` — Old entry point (API is new entry)

---

## API Structure

```
/api/led_hex/
├─ main.py              # FastAPI app (game-agnostic)
├─ game_manager.py      # Play object lifecycle
├─ models.py            # Pydantic schemas
├─ database.py          # DB wrapper
├─ config.py            # Game config (points to LED Hex)
└─ requirements.txt     # Dependencies
```

---

## Deployment

1. **Phase 1: Build (18 hrs)**
   - [ ] Write FastAPI endpoints (/login, /start-game, /game WS, /result)
   - [ ] Wrap Play.py execution
   - [ ] Test with simulator

2. **Phase 2: Test (4 hrs)**
   - [ ] Verify game logic unchanged
   - [ ] Verify LED control works
   - [ ] Verify scoring/database works

3. **Phase 3: Deploy to Other 4 Games (8 hrs)**
   - Copy API code
   - Change config.py per game
   - No other changes needed

---

## Timeline

**LED Hex API:** 18-22 hours (with simulator testing)
**Deploy to others:** 2 hours each × 4 = 8 hours
**Total:** ~30 hours for all 5 games

---

## Key Insight

API is game-agnostic. Loads whatever `Play.py` + `source/` is in configured path.
Same API code runs all 5 games. Only `config.py` changes per game.

---

**Status:** Ready to implement
