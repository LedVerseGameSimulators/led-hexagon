# Will the headless impl work on the real LED floor?

> **Hex playbook:** [`LED_HEX_DEVELOPMENT_PLAYBOOK.md`](./LED_HEX_DEVELOPMENT_PLAYBOOK.md)  
> **All games:** [Hoops](../led-hoops/docs/HOOPS_DEVELOPMENT_PLAYBOOK.md) · [Climb](../led-climb/docs/CLIMB_DEVELOPMENT_PLAYBOOK.md)

Short answer: **yes, mostly** — the game logic is I/O-agnostic. It operates on
two arrays:

- `state_table[row][col]` — input (1 = tile pressed)
- the LED display buffer — output (per-cell colors; **3 rings per hex tile**)

In **sim mode** today:
- input = simulator click → `/game-input` → `led_table.press_cell` → `state_table`
- output = `led_display` (built each frame) → API state → ws_bridge → canvas

In **hardware mode** the SAME logic runs; only the I/O source/sink changes:
- input = `led_control.read(com, state_table, …)` fills `state_table` from floor sensors
- output = `led_display` → `led_control` serial → physical LEDs

The decompiled hardware hooks already exist (gated by `Setting.USE_SERIAL_HD`):
- `led_control.init_com(list_com_info)` — open serial ports
- `led_control.init_layout(type, 16, 26, no_use_coords)` — map grid ↔ physical LEDs
- `led_control.read(com, state_table, start_num, read_size)` — sensors → state_table
- `game_hw.GameHW` — wraps init/draw/read for floor + wall + screen

## What already fits (no change)

- ✅ **Game logic** — scoring, movement, breath, consume, HP, time, goal-color.
- ✅ **3-ring display buffer** — `led_display` carries outer/mid/inner per cell; flatten to 9 bytes/tile for serial.
- ✅ **state_table as the input contract**
- ✅ **Settings from `led_parameter`**

## What must be ADDED for hardware (the I/O bridge)

1. **Init:** `led_control.init_com` + `init_layout` at game start.
2. **Per-frame input:** `led_control.read` → refresh `state_table`.
3. **Per-frame output:** push `led_display` to serial (9 bytes per hex tile).
4. **Toggle:** `USE_SERIAL_HD=True` or env-driven flag.

## Recommended design: I/O driver abstraction

```
loop frame:
    driver.read_input(state_table)
    play.update(...)
    build led_display (breath/flash, 3 rings)
    driver.write_output(led_display)
```

- **SimDriver** (today): `/game-input` + ws_bridge
- **HardwareDriver**: `led_control.read` + serial write

## Risks on real hardware

- **3-ring byte order** — outer → mid → inner per tile; verify on floor
- **Coordinate mapping** — `list_com_info` index ↔ (row,col)
- **Serial throughput** — up to 416 tiles × 9 bytes; tune loop pacing
- **Sensor debounce** — `scored_active` helps; verify held tiles
- **`read()` reverse-index bug** — test on hardware (see HARDWARE_DEPLOYMENT.md)

## Bottom line

Logic is decoupled from I/O. Hardware = `HardwareDriver` + calibration on-site.
