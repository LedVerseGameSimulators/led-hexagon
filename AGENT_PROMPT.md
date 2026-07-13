# On-Site Agent Prompt — LED Hexagon

> Hand this whole file to a fresh Claude Code agent running **on the
> physical Windows machine** after the `led-hexagon` zip has been unzipped
> there. It is self-contained — the agent does not need this conversation's
> history.

---

## Your situation

You are running as Claude Code **on a Windows PC** that is one of 6
machines on a LAN for an on-site Activerse deployment. This machine drives
the **LED Hexagon** game: a 16-row × 26-column physical hex-tile floor
where **each tile has 3 concentric LED rings** (outer/mid/inner — this is
different from the other 4 games, which have one LED per cell), wired to
several USB-serial adapters, plus a FastAPI + React frontend headless-ported
from a decompiled Chinese arcade game.

**This is a first-time real-hardware validation for this game — not a
re-test.** The hardware driver code (`_hw_init()`, `USE_SERIAL_HD`,
`led.led_control` calls) was written by analogy from led-hoops/led-climb's
real-hardware findings, but has never itself been run against a physical
floor. Treat everything as unverified until you verify it yourself.

The `led-hexagon` repo has been unzipped to (adjust if the actual extract
path differs — check with the person on-site if unsure):

```
C:\activerse\led-hexagon\
```

All commands below assume:
- **Windows**, so use `python` (not `python3`), `pip`, and prefer
  **Command Prompt** (`cmd`) as shown in `ONSITE.md`, with the PowerShell
  equivalent noted where it differs (e.g. `set VAR=1` in cmd vs
  `$env:VAR="1"` in PowerShell).
- Run the terminal **as Administrator** (needed for COM port / driver
  access).
- Do not touch the RFID server, SQL server, or any other service already
  running on this PC unless a doc below explicitly tells you to.
- Do not modify the `games/setting/led_parameter` shelve.
- Do not flatten the 3-ring `led_display` cell format anywhere — it is
  `[[R,G,B],[R,G,B],[R,G,B]]` per hex tile, intentionally different from
  the other 4 games' flat `[R,G,B]`.

## What to read, in this order

1. **`ONSITE.md`** (repo root) — single-machine setup: Python version
   check, `pip install -r requirements.txt`, verifying the `led_parameter`
   shelve (COM port config, layout type, grid dims), verifying all COM
   ports are visible to Windows, running `games\test_hardware.py`, starting
   the API with `USE_SERIAL_HD=1`, starting `ws_bridge.py` and the
   frontend. Follow every step in order; do not skip verification steps.
2. **`ONSITE_LAN_INTEGRATION_PLAN.md`** (repo root) — the cross-machine
   network layer: static IP for this machine (`192.168.1.105` per the plan,
   unless told otherwise), port map (this machine's API is `8004`, WS
   bridge `8767`, UI `5177`), Windows Firewall inbound rule for port 8004,
   and what changes from `localhost` to a real IP so the central RFID
   server (`activerse-rfid`, machine 6) can reach this one. This document
   covers ONLY the network layer — it does not repeat `ONSITE.md`'s
   single-machine steps.
3. **`HARDWARE_VALIDATION.md`** (repo root) — what hardware integration
   exists (16×26 grid, 3-ring-per-tile protocol, COM port setup), that this
   is a first-time validation, and the concrete on-site checklist you'll
   execute next. Pay particular attention to §3 (3-ring color order) and §5
   (memory-mode mechanic) — both are genuinely novel risk areas, not
   routine checks.

Read all three fully before running anything.

## What to do

1. Follow `ONSITE.md` steps 1–9 to extract/verify the repo, install Python
   and Node dependencies, verify the `led_parameter` shelve and all COM
   ports, run `games\test_hardware.py`, and start all 3 services (API with
   `USE_SERIAL_HD=1`, `ws_bridge.py`, frontend).
2. Follow the relevant parts of `ONSITE_LAN_INTEGRATION_PLAN.md` to set
   this machine's static IP, open the firewall port (8004), and confirm
   it's reachable from another machine on the LAN if one is available to
   test with (skip network-reachability checks only if no other machine is
   up yet — note that in your report, don't just skip silently).
3. Execute the **on-site validation checklist** in `HARDWARE_VALIDATION.md`
   §6, in order. Do NOT rush through the 3-ring color-order check or the
   memory-mode visual check — both are genuinely new and have never been
   confirmed on real hardware before. Specifically:
   - Confirm `USE_SERIAL_HD=1` boots cleanly (`Hardware ready: N port(s),
     16×26, layout=X` in the log, not `Hardware init failed`). Note the
     actual COM port count `N` — there is a known discrepancy between docs
     (3 vs 4 ports) that needs resolving against the real shelve.
   - Run `games\test_hardware.py` and confirm all COM ports open, the FULL
     16×26 grid lights (not just tiles near the first port), and stepping
     on tiles reports the correct row/col.
   - **3-ring color order** — pick one hex cell with 3 distinct ring colors
     from a known level (or an ad-hoc test sending different colors to
     each ring), and visually confirm outer/mid/inner rings show the
     correct color in the correct physical position on the real tile. A
     swapped/reversed ring order would look like a color bug even though
     tile positions are correct — this is the single highest-risk item in
     this checklist.
   - **Memory-mode mechanic** (YC-tier levels: goal-tile reveal/hide, teal
     placeholder while hidden, single shared hint-tile alternating P1/P2
     color every ~5s in 2P levels) — this was built and only ever tested in
     the browser simulator this session. Confirm it displays and times
     correctly on the physical floor. If it looks wrong, do NOT try to fix
     the mechanic yourself — report exactly what you observed (timing,
     wrong color, wrong player) for a follow-up session.
   - Playing one full marathon session end-to-end on the real floor,
     **including a real 2-player DK-series or YCDK `.ledb` level with two
     people actually playing**, confirming score/life/session-end behave
     correctly both physically and in the UI.
   - Confirming the blank-on-stop fix (`_hw_blank_floor` in
     `api/game_manager.py`) actually blanks **all 3 rings** on the physical
     floor on timeout, true game-over, manual stop (`/logout`), and before
     a new game starts (`clear_all()`) — this fix was written this session
     and has never been run against real hardware.

## How to report back

Do **not** report "done" or "hardware works" as a summary. For every
checklist item in `HARDWARE_VALIDATION.md` §6, report explicit **PASS** or
**FAIL** with a one-line observation, with enough detail that someone can
debug remotely without being back on-site, e.g.:

```
[PASS] USE_SERIAL_HD=1 boot — log showed "Hardware ready: 3 port(s), 16x26, layout=1"
[PASS] test_hardware.py — all 3 ports opened, full 16x26 grid lit green, all
       tested presses registered correct row/col
[FAIL] 3-ring color order — sent outer=red/mid=green/inner=blue to tile (3,10);
       physical tile showed outer=blue/mid=green/inner=red — REVERSED order
[PASS] Memory-mode — YC03 reveal/hide cadence matched simulator; hint tile
       alternated P1 orange / P2 purple every ~5s as expected on DK02
[FAIL] Blank-on-stop, Stop-Game case — floor stayed lit after /logout call,
       no blank observed; timeout and clear_all cases did blank correctly
...
```

If the 3-ring order is reversed or scrambled, do not attempt a fix yourself
unless `HARDWARE_VALIDATION.md` §3 gives you an explicit go-ahead for a
specific, narrow change — report the exact observed vs expected order per
ring instead, so it can be fixed precisely.
