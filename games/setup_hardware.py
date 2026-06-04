"""
LED Hex — Hardware Mode Setup
==============================
Run this ONCE on the Windows PC to:
  1. Scan all available COM ports and show which ones look like LED hardware
  2. Update the shelve settings with the correct COM port
  3. Enable USE_SERIAL_HD = True in model/setting.py

Usage:
    python setup_hardware.py           <- interactive, scans ports + updates settings
    python setup_hardware.py --status  <- just show current settings, no changes
    python setup_hardware.py --disable <- switch back to simulator-only mode
"""

import sys
import os
import shelve
import re

# ── Helper: make sure we run from the right directory ────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

SETTING_FILE   = "./setting/led_parameter"
MODEL_FILE     = "./model/setting.py"

# ─────────────────────────────────────────────────────────────────────────────

def scan_com_ports():
    """Return a list of (name, description) for all serial ports available."""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        return [(p.device, p.description or "") for p in sorted(ports)]
    except ImportError:
        print("  [!] pyserial not installed — run: pip install pyserial")
        return []


def show_current_settings():
    print("\n── Current shelve settings (setting/led_parameter) ──────────────────")
    try:
        with shelve.open(SETTING_FILE) as f:
            print(f"  Grid size         : {f.get('value_width')} cols × {f.get('value_high')} rows")
            print(f"  list_com_name     : {f.get('list_com_name')}")
            print(f"  list_com_info     : {f.get('list_com_info')}")
            print(f"  list_wall_com_info: {f.get('list_wall_com_info')}")
    except Exception as e:
        print(f"  ERROR reading shelve: {e}")

    print("\n── model/setting.py ──────────────────────────────────────────────────")
    try:
        with open(MODEL_FILE) as fh:
            for line in fh:
                if "USE_SERIAL_HD" in line:
                    print(f"  {line.rstrip()}")
    except Exception as e:
        print(f"  ERROR reading {MODEL_FILE}: {e}")


def set_use_serial_hd(enabled: bool):
    """Patch USE_SERIAL_HD in model/setting.py."""
    value = "True" if enabled else "False"
    comment = "hardware serial enabled" if enabled else "simulator mode: no physical hardware"
    try:
        with open(MODEL_FILE, "r") as fh:
            content = fh.read()
        new_content = re.sub(
            r'USE_SERIAL_HD\s*=\s*(True|False).*',
            f'USE_SERIAL_HD = {value}   # {comment}',
            content
        )
        with open(MODEL_FILE, "w") as fh:
            fh.write(new_content)
        print(f"\n  ✔  model/setting.py → USE_SERIAL_HD = {value}")
    except Exception as e:
        print(f"\n  ERROR patching {MODEL_FILE}: {e}")


def update_com_port(com_name: str, num_leds: int = 33):
    """
    Update the shelve settings to use the given COM port.
    num_leds: how many floor LED tiles are on this COM port (default 33 = original setting).
    Format stored: [['WCH USB-SERIAL Ch A (COM9)', '1', '33', 'normal_led']]
                    com_name                        start  end   type
    """
    with shelve.open(SETTING_FILE, writeback=True) as f:
        f["list_com_name"]  = [com_name]
        f["list_com_info"]  = [[com_name, "1", str(num_leds), "normal_led"]]
        # wall/screen lights stay empty unless you have those too
        if not f.get("list_wall_com_info"):
            f["list_wall_com_info"] = []
        if not f.get("list_screen_com_info"):
            f["list_screen_com_info"] = []
    print(f"\n  ✔  shelve updated → COM port = {com_name}, tiles 1–{num_leds}")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    if "--status" in sys.argv:
        show_current_settings()
        print()
        return

    if "--disable" in sys.argv:
        set_use_serial_hd(False)
        show_current_settings()
        print("\nSimulator mode re-enabled. Run run_simulator.py normally.\n")
        return

    print("=" * 60)
    print(" LED Hex — Hardware Mode Setup")
    print("=" * 60)

    show_current_settings()

    # ── Scan ports ───────────────────────────────────────────────────────────
    print("\n── Available COM ports ───────────────────────────────────────────────")
    ports = scan_com_ports()
    if not ports:
        print("  No COM ports found. Check USB cable and drivers.")
        print("  Install WCH CH340/CH341 driver if missing:")
        print("  https://www.wch-ic.com/downloads/CH341SER_EXE.html")
        return

    for i, (dev, desc) in enumerate(ports):
        marker = "  ← looks like LED hardware" if ("WCH" in desc or "CH340" in desc or "CH341" in desc or "USB-SERIAL" in desc.upper()) else ""
        print(f"  [{i+1}] {dev:12s}  {desc}{marker}")

    # ── Let user pick ────────────────────────────────────────────────────────
    print()
    choice = input("Enter the number of the COM port for the LED floor tiles (or press Enter to skip): ").strip()
    if not choice:
        print("No port selected. Exiting without changes.")
        return

    try:
        idx = int(choice) - 1
        selected_com, selected_desc = ports[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    # ── Ask for tile count ───────────────────────────────────────────────────
    tile_input = input(f"How many floor LED tiles on {selected_com}? (press Enter for 33): ").strip()
    num_leds = int(tile_input) if tile_input.isdigit() else 33

    # ── Apply changes ────────────────────────────────────────────────────────
    print()
    update_com_port(selected_com, num_leds)
    set_use_serial_hd(True)

    # ── Confirm ──────────────────────────────────────────────────────────────
    print()
    show_current_settings()

    print()
    print("=" * 60)
    print(" Hardware mode enabled!")
    print(" Now run:  python run_simulator.py")
    print()
    print(" The game will talk to the physical tiles AND show the")
    print(" browser simulator at http://127.0.0.1:8765")
    print()
    print(" To go back to simulator-only mode:")
    print("   python setup_hardware.py --disable")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
