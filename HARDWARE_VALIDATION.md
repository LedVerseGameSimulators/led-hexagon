# Hardware Validation — LED Hexagon

> **Read this before an on-site hardware session.** It states what hardware
> integration exists, what has and hasn't been validated on the real floor,
> and gives a concrete checklist to run through on-site.
>
> **This is a FIRST-TIME real-hardware validation, not a re-test.** Unlike
> some of the other 4 games, LED Hexagon's hardware driver has never been run
> against a physical floor at all. Everything below is unverified until this
> session happens.

---

## 1. What hardware integration exists

- **Grid:** 16 rows × 26 columns (416 hex tiles).
- **Protocol — UNIQUE to this game among the 5:** every other game's LED
  buffer cell is a flat `[R, G, B]` (3 bytes/tile). Hexagon's cell is
  **3 concentric rings per hex tile** — `[[R,G,B], [R,G,B], [R,G,B]]`
  (outer, mid, inner) — **9 bytes/tile**. `draw_screen_by_com` loops
  `k in range(2, -1, -1)` over the 3 rings internally; do not flatten this
  format anywhere in the pipeline (see `ONSITE.md` "What NOT to touch").
- **COM ports — discrepancy to resolve on-site:** `ONSITE.md` Step 4/5 and
  the dev `led_parameter` shelve say **3** COM port entries. The parent
  `HARDWARE_INTEGRATION_PLAN.md` (Game 5 section) says **4 ports on real
  hardware**, noting "dev shelve shows 1" for a different field (rows/cols
  test config, not port count). Treat neither number as ground truth —
  confirm the actual count on the real floor's `led_parameter` shelve
  (`games/setting/led_parameter`, key `list_com_info`) during Step 4 of the
  checklist below, and update this doc with the real count once confirmed.
- **Mechanism:**
  - `USE_SERIAL_HD` env var (`api/game_manager.py`) gates all hardware code
    paths. Default `0` (sim-only); set to `1` to drive the real floor.
  - `_hw_init()` — called once per game start when `USE_SERIAL_HD=1`. Reads
    `games/setting/led_parameter` (`list_com_info`, `led_layout_type`,
    `value_high`/`value_width`, `floor_layout_coors_no_use`), calls
    `led.led_control.init_layout(layout_type, rows, cols, no_use)` and
    `led.led_control.init_com(list_com_info)` to open the serial port(s).
  - Per-frame output: `_hw_led_control.draw_screen_by_com(_hw_layout_type, grid)`
    — pushes the same 3-ring `led_display` buffer the simulator renders,
    throttled to `_HW_DRAW_INTERVAL` (~22 fps default, `HW_DRAW_INTERVAL` env
    override).
  - Per-frame input: `_hw_led_control.update_screen_state_by_com(...)` reads
    floor sensor state into `state_table`, feeding the same scoring path as
    simulator clicks.
  - All hardware calls are wrapped in `_hw_serial_lock` (single lock shared
    across reads/writes) and gated by `USE_SERIAL_HD and _hw_led_control is
    not None`, so sim-only runs never touch the `led` module.
  - `game_hw.GameHW` (original decompiled wrapper for floor + wall + screen
    outputs) is the reference the current `_hw_init`/draw/read code was
    modeled on; wall/screen LED outputs are disabled in all current levels
    and not targeted here.

## 2. Validation history

| When | What happened | Evidence |
|------|----------------|----------|
| Pre-hardware | Simulator-only implementation reaches ~90% completion: full 3-ring headless game loop, 67 levels (extra/basic/advanced/pro), `.ledb` 2P support, HP/scoring/leaderboard. Tag `sim-ready-2026-06-07`. Hardware serial I/O **not yet integrated**. | `LOCKED.md`, `docs/STATUS_HARDWARE.md` |
| Later commit ("Hardware integration: fix decompiler slice bugs + add USE_SERIAL_HD mode") | `_hw_init()`, `USE_SERIAL_HD`, per-frame `draw_screen_by_com`/`update_screen_state_by_com` calls, `games/test_hardware.py` diagnostic added to `api/game_manager.py`. Written **by analogy** from led-hoops' and led-climb's real-hardware findings (their driver code had already been confirmed against physical floors) — hexagon's own copy of this pattern has **never been run against real hardware itself**. | `api/game_manager.py`, `games/test_hardware.py` |
| This session | Gameplay/mechanics work layered on top of the still-unvalidated hardware code: memory-mode (YC-tier levels — reveal/hide of goal tiles, single shared hint-tile that alternates color every `_reveal_duration` (5s) to signal whose turn it is in 2P), blank-on-stop fix (`_hw_blank_floor`, see §4 below). | `api/game_manager.py` (`_memory_mode`, `hint_cells`, `_reveal_duration`, `_hw_blank_floor`) |

**Bottom line:** unlike hoops/climb, **no part of the hardware driver for
this game has ever touched a physical LED floor.** The 3-ring protocol, the
16×26 coordinate mapping, the COM port count, and the sensor read path are
all "should work by analogy to the other games" — none of it is confirmed.
This on-site session is the first real test.

## 3. Real risk area: 3-ring color order (outer/mid/inner)

This is the single biggest hexagon-specific risk, and the reason this game
needs a more careful visual check than the other 4 (which only have one LED
per tile).

- `led_display[i*cols+j]` is built as `[[R,G,B],[R,G,B],[R,G,B]]` meaning
  **[outer, mid, inner]** in that order, matching game logic (goal color on
  outer ring for visibility, etc. — check `_normalize_rings` in
  `api/game_manager.py` for the exact construction).
- `draw_screen_by_com` is assumed to write the 3 rings to the physical
  tile's 3 LEDs in the **same outer→mid→inner order**. This assumption has
  never been checked against a real hex tile. If the physical wiring or the
  decompiled `led_control` driver actually expects mid→outer→inner, or
  inner→mid→outer, or any other order, **every tile will show visually
  swapped ring colors** even though tile *positions* are completely correct
  — this would look like a color bug, not a wiring bug, and could be
  mis-diagnosed as a game-logic issue if the ring-order risk isn't already
  known going in.

**How to sanity-check this concretely on-site (do this, don't skip it):**

1. Pick one level file with a hex cell that has 3 *visibly distinct* ring
   colors (not black/off on any ring). A DK-series `.ledb` 2P level is a
   good candidate since P1/P2 goal indicators and hint tiles often differ
   in color from the base decor — or use `games/test_hardware.py`'s test
   pattern if it supports per-ring colors (check the script; if it only
   sends solid green on all 3 rings, that only proves wiring, not order —
   you'll need a real level or a small ad-hoc test script that sends 3
   different colors per ring, e.g. outer=red, mid=green, inner=blue, to one
   known tile).
2. Start the game (or run the ad-hoc 3-color test) and physically look at
   that one hex tile.
3. Confirm: the outer ring glows the color you sent as ring index 0, the
   middle ring glows ring index 1's color, and the inner ring glows ring
   index 2's color — in that exact spatial order, not reversed or
   scrambled.
4. If the order is wrong, the fix is a reordering in the `_ld2`/ring-flatten
   step right before `draw_screen_by_com` in the per-frame HW block
   (`api/game_manager.py`, search `_ld2 = [[led_display...`) — reverse or
   permute the 3-element ring list to match what the hardware actually
   expects, and re-run this same check. Do not touch anything else in that
   block.

## 4. Blank-on-stop fix (this session, unvalidated)

`_hw_blank_floor(led_table)` (added `api/game_manager.py`, right after
`_hw_init()`) sends one all-black frame — **all 3 rings, all `[0,0,0]`** —
using the exact same `draw_screen_by_com` call already used for normal
frames, gated the same way (`USE_SERIAL_HD and _hw_led_control is not
None`). It is called at every place a session/game ends:

1. Empty level-sequence early-return (can't run any level).
2. Normal marathon session-end (timeout / life-exhausted / sequence
   complete) — right after `game.update_state(game_over=True, ...)`.
3. The `_run_game` exception-catch path (session ends abnormally on error).
4. `stop_game()` — manual stop via the `/logout` endpoint.
5. `clear_all()` — called at the start of every new game to stop any prior
   one; blanks each game being cleared (after joining its thread, so it
   doesn't race that thread's own last in-flight draw).

This is new code, gated safely, and syntax-checked (`ast.parse`), but **it
has never been run against a real floor.** Confirm on-site that
`draw_screen_by_com` actually blanks all 3 rings on every physical tile, not
just the ones affected by whatever was drawn last.

## 5. Memory-mode mechanic — also never seen on real hardware

Separate from the hardware-driver risk above: the YC-tier memory-mode
mechanic itself (reveal/hide of goal tiles, single shared hint-tile that
alternates color every 5s in 2P levels to indicate whose turn it is, teal
placeholder color `[0,62,62]` on all 3 rings while a tile is hidden) was
built and tested **only in the browser simulator**. It has never been
displayed on a physical hex tile at all — separate from whether the ring
order or blank-on-stop works, confirm the reveal/hide timing and hint-tile
alternation are visually legible on the real floor (breath/flash effects
plus 3-ring color changes can look different at full physical scale and
viewing distance than in a browser canvas).

**Reveal-on-hit (current behavior):** after a press in memory mode, that
cell stays painted for its current life instead of blanking — scored goals
keep their true color (no re-score until respawn/new wave), static deduct
stays red and keeps hurting like moving red (both scores + shared HP in
2P), and blank/decor get a checked look (darker teal `[0,40,40]` when the
true color was camouflage teal). Reveal marks clear on respawn, auto-jump
to the next wave, or a fresh active life at that coordinate.

**Do not modify this mechanic's code during on-site validation** — if it
doesn't look right, note exactly what's wrong (timing off? teal not
visible? wrong player's color showing?) and report it; it should be fixed
in a follow-up session with the actual floor available for iteration, not
patched blind.

## 6. On-site validation checklist

Run these in order. Record **PASS/FAIL** for each — don't just say "done."

- [ ] **Environment:** Start the API with `USE_SERIAL_HD=1` (see `ONSITE.md`
      Step 8). Confirm the startup log shows
      `Hardware ready: N port(s), 16×26, layout=1` (or whatever
      `led_layout_type` the real shelve has) — not `Hardware init failed: ...`.
      Note the actual port count `N` here and reconcile with the "3 vs 4
      ports" discrepancy in §1.
- [ ] **Diagnostic script:** Run `python games/test_hardware.py` (Windows:
      `python`, not `python3`). Confirm: all COM ports open OK, the full
      16×26 grid lights (check corners and edges, not just a few tiles near
      the first COM port — a wiring/mapping gap would show as some tiles
      never lighting), and stepping on tiles prints
      `PRESS detected: row=X col=Y` matching the tile you actually stepped on.
- [ ] **Grid mapping — full floor:** Beyond the diagnostic script, verify a
      real level (not just the green test pattern) lights the correct
      *shape* on the full 16×26 floor — pick a level with an easily
      recognizable pattern and visually confirm no rows/columns are
      offset, mirrored, or truncated.
- [ ] **3-ring color order (see §3):** Pick one hex cell with 3 distinct
      ring colors from a known level (or an ad-hoc 3-color test), and
      visually confirm outer/mid/inner match on the physical tile. This is
      the single most important check in this file — do not skip it or
      wave it through on a quick glance.
- [ ] **Memory-mode mechanic (see §5):** Run a YC-tier level. Confirm goal
      tiles reveal (true color) then hide (teal placeholder) on the
      expected cadence, and in a 2P `.ledb` YC level, confirm the single
      hint tile visibly alternates between P1's and P2's color roughly
      every 5 seconds and that a press is credited to whichever player's
      color was showing at press time.
- [ ] **Full marathon session, real hardware, end-to-end, including a real
      2P level:** Play one complete marathon session (card scan or guest
      login → level sequence → session end) on the physical floor,
      including at least one DK-series or YCDK `.ledb` 2-player level with
      two people actually playing. Confirm:
  - [ ] Score increments correctly for P1 and P2 independently on scoring
        tiles (physical + simulator UI agree).
  - [ ] Life/HP decrements correctly on red/DEDUCT tiles; life=0 mid-session
        (with time remaining) triggers a level restart with refilled HP,
        not a hard game-over.
  - [ ] 2P tile respawn (8-second delay on `.ledb` levels) behaves
        correctly on the real floor's timing, not just in the simulator.
  - [ ] Session ends correctly on: timeout, true game-over (life=0 with
        <10s left), or full level-sequence completion — correct
        `game_over_reason`/`result` shows in the UI.
- [ ] **Blank-on-stop fix (§4):** Confirm the floor goes fully dark — **all
      3 rings, all 416 tiles** — within ~1s of each of:
  - [ ] A level/session ending via timeout (no manual stop).
  - [ ] A true game-over (life=0, <10s left).
  - [ ] Manually stopping via `/logout` (or a Stop-Game control in the UI)
        mid-level.
  - [ ] Starting a **new** game while a stale pattern is showing on the
        floor (skip the blank steps above once to reproduce the stuck
        state, then start a new game) — confirm `clear_all()`'s blank fires
        before the new game's first real frame.
  - [ ] No regression: floor still draws normally, all 3 rings, during
        active gameplay (throttle/lock unaffected by the added blank calls).

Report each checklist item as **PASS** or **FAIL** with a one-line note, not
a blanket "hardware works."
