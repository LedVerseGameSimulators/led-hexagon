"""Per-product constants. This is the only file that differs between game repos."""

SLUG = "hexagon"          # kiosk profile slug (open-ui.bat call in START_GAME.bat), release/zip names
DISPLAY_NAME = "LED Hexagon"
API_PORT = 8004           # must match frontend/src/config.js
BRIDGE_PORT = 8767
# Ports freed on STOP (same set STOP_GAME.bat frees; 5177 = legacy vite preview).
STOP_PORTS = (8004, 8767, 5177)
