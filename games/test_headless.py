#!/usr/bin/env python3
"""
Test LED Hex game_running.py for headless compatibility
Verify: no Tkinter errors, mock LedTable works, game logic intact
"""

import sys
import os

# Add game path
game_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, game_root)

print(f"✓ Game path: {game_root}")
print(f"✓ Python version: {sys.version}")
print()

# Test 1: Import game_running module
print("TEST 1: Import game_running module")
try:
    from game_play import game_running
    print("✓ Import successful, no Tkinter errors")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check mock LedTable exists
print("\nTEST 2: Verify mock LedTable class")
try:
    assert hasattr(game_running, 'LedTable'), "LedTable class not found"
    print("✓ Mock LedTable class exists")
except AssertionError as e:
    print(f"✗ {e}")
    sys.exit(1)

# Test 3: Instantiate mock LedTable
print("\nTEST 3: Instantiate mock LedTable")
try:
    led_table = game_running.LedTable(
        root=None,
        wall_light_arr_len=100,
        led_row=10,
        led_col=10,
        table_display=False
    )
    print(f"✓ LedTable instantiated")
    print(f"  - wall_light_arr_len: {led_table.wall_light_arr_len}")
    print(f"  - led_row: {led_table.led_row}")
    print(f"  - led_col: {led_table.led_col}")
    print(f"  - table_display: {led_table.table_display}")
except Exception as e:
    print(f"✗ LedTable instantiation failed: {e}")
    sys.exit(1)

# Test 4: Call mock LedTable methods
print("\nTEST 4: Call mock LedTable methods")
try:
    led_table.update_led()
    led_table.redraw_led_table_default()
    print("✓ Mock methods execute without error")
except Exception as e:
    print(f"✗ Mock method call failed: {e}")
    sys.exit(1)

# Test 5: Check for Tkinter imports in game_running
print("\nTEST 5: Verify no Tkinter imports")
try:
    import inspect
    source = inspect.getsource(game_running)

    forbidden = ['tkinter', 'Tkinter', 'from gui', 'import gui', 'messagebox', 'gui_setting']
    found = []

    for term in forbidden:
        if term in source:
            found.append(term)

    if found:
        print(f"✗ Found forbidden imports/terms: {found}")
        sys.exit(1)
    else:
        print("✓ No Tkinter imports detected")
except Exception as e:
    print(f"✗ Source inspection failed: {e}")
    sys.exit(1)

# Test 6: Check GameRunning class exists
print("\nTEST 6: Verify GameRunning class")
try:
    assert hasattr(game_running, 'GameRunning'), "GameRunning class not found"
    print("✓ GameRunning class exists")
except AssertionError as e:
    print(f"✗ {e}")
    sys.exit(1)

print("\n" + "="*50)
print("ALL TESTS PASSED ✓")
print("="*50)
print("\nSummary:")
print("- game_running module imports without errors")
print("- Mock LedTable class works correctly")
print("- No Tkinter dependencies detected")
print("- GameRunning class is intact")
print("\nResult: LED Hex is headless-compatible!")
