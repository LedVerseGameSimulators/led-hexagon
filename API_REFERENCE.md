# API Reference — LED Hexagon

Lightweight reference for every FastAPI endpoint in `api/main.py`. Not
exhaustive request/response schemas — see `api/models.py` for full Pydantic
models and `api/main.py` for implementation detail.

Base URL (dev): `http://localhost:8004`. Onsite: `http://192.168.1.105:8004`
(per `ONSITE_LAN_INTEGRATION_PLAN.md`).

---

## Game lifecycle

### `POST /login`
Look up a player by RFID card ID.
- **Body:** `{ card_id: string }`
- **Response:** `{ success, player?: { custom_id, name, phone, time_left, card_id }, error? }`

### `POST /start-game`
Create and start a new game instance (marathon session). Clears any prior
running game first (kiosk model — see `GameManager.clear_all()`).
- **Body:** `{ card_id: string, level: int | string, difficulty: "easy"|"normal"|"hard" }`
  (`level` is numeric 17–26 for extra/test levels, or a named level like
  `"DK01"`/`"YC03"` for the main library)
- **Response:** `{ success, game_id?, ws_url?, error? }`

### `GET /game-state`
Current state of the first active game (used by the simulator when it
doesn't yet know a specific `game_id`).
- **Response:** `{ success, game_id?, state? }` or `{ success: false, error }`
  if no active games.

### `GET /game-state/{game_id}`
State of one specific game (simulator polls its own game after start).
- **Response:** `{ success, game_id, state }` — `state` includes score,
  score2, life, time_elapsed/time_left, `led_display` (3-ring cells),
  `game_over`, `game_over_reason`, `current_level`, `levels_cleared`, etc.

### `GET /active-game`
Resume support: returns the currently-running, not-yet-game-over game (if
any) with full config, so the frontend can resume the simulator after a
page reload instead of restarting login.
- **Response:** `{ success, game_id, card_id, level, difficulty, state }` or
  `{ success: false }` if nothing is active.

### `POST /game-input`
Player input from the simulator (or a browser click) — press/release a hex
tile.
- **Body:** `{ row: int, col: int, type: "press"|"release", game_id?: string }`
  (`game_id` optional — falls back to the first active game if omitted)
- **Response:** `{ success, score }`

### `POST /save-score`
Persist a finished session to the leaderboard/scores table.
- **Body (key fields):** `{ card_id, card_id2?, multiplayer, level,
  end_level, score, score2, final_score, final_score2, life, lives_start,
  result, time_used, levels_cleared, difficulty, started_at }`
- **Response:** `{ success, error? }`

### `POST /logout`
End a game session (calls `GameManager.stop_game`) and record its score.
- **Body:** `{ card_id: string, game_id: string }`
- **Response:** `{ success, error? }`

### `GET /result/{game_id}`
Final result + per-level leaderboard for a finished (or still-existing)
game.
- **Response:** `{ success, score, player_name, time_used, difficulty, leaderboard: [{rank,name,score,timestamp}], error? }`

### `GET /levels`
All levels, grouped into 4 categories (fast — directory/extension scan
only, no shelve read).
- **Response:** `{ success, levels: [...], categories: { extra, basic,
  advanced, pro }, count }`. Each level: `{ id, name, path, category,
  multiplayer, file_type }`. `basic` = `.ledb` 2P (DK/YCDK series);
  `extra`/`advanced`/`pro` = `.led` 1P.

### `WS /game/{game_id}`
Real-time game state stream (score, LEDs, etc.) to the client; accepts
input messages back (input feed-through is a TODO in the current code —
primary input path is `POST /game-input`).

---

## RFID / settings

### `GET /game-settings`
Load static-ish game settings (grid dims, wall layout, timeout, max score)
from the `led_parameter` shelve, with hardcoded fallback if the shelve read
fails.
- **Response:** `{ success, wall_layout, grid_dims: {rows, cols}, timeout_seconds, max_score }`

### `POST /settings`
Runtime overrides pushed from the central RFID server (default difficulty,
session length). Written to a local `runtime_overrides.json`, read at
marathon-start time — does **not** touch the original `led_parameter`
shelve.
- **Body:** `{ default_difficulty?: string, session_minutes?: int }`
- **Response:** `{ success, overrides }`

### `GET /settings`
Read back the current runtime overrides file (`{}` if none set yet).
- **Response:** `{ default_difficulty?, session_minutes? }`

---

## Scores / health / diagnostics

### `GET /scores?since=<ISO timestamp>`
Scores recorded after `since` — used by the RFID server's cross-game
leaderboard poller (default `since = 2000-01-01T00:00:00`, i.e. "all").
- **Response:** `{ success, game, scores: [...] }`

### `GET /leaderboard/{level}?limit=10`
Top scores for one specific level.
- **Response:** `{ success, level, entries: [...] }`

### `GET /health`
Basic health/liveness check, includes `GameManager` stats.
- **Response:** `{ status: "ok", game, stats }`

### `GET /hw-debug`
Live hardware-loop diagnostics: whether `USE_SERIAL_HD` is on, active games
with their HW draw counts/timestamps, and any zombie threads from
`clear_all()`. Useful for confirming hardware frames are actually being
drawn during a session (`hw_draw_count` incrementing).
- **Response:** `{ use_serial_hd, active_games, games: [{game_id, running, score, hw_draw_count, last_hw_draw}], zombie_threads }`
