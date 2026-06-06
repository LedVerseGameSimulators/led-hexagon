# LED Hex — Status (summary)

> **Canonical doc:** [`LED_HEX_DEVELOPMENT_PLAYBOOK.md`](./LED_HEX_DEVELOPMENT_PLAYBOOK.md) — done/pending checklists, runbook, 3-ring notes, hardware path.

**Last updated:** 2026-06-07 · **Simulator:** ✅ · **Hardware I/O:** ⏳ pending

---

## Quick status

| Area | Status |
|------|--------|
| Headless API + 3-ring simulator | ✅ |
| 67 levels, 2P `.ledb`, respawn | ✅ |
| `breath_color` / ring rendering fix | ✅ |
| Ports 8002 / 8767 / 5175 | ✅ |
| Serial floor driver | ⏳ in `games/led/`, mocked in API |

---

## Architecture (current ports)

```
React (:5175) → FastAPI (:8002) → Play.running() → HeadlessLedTable (3 rings)
     iframe ↓
Simulator (:8767) ← ws_bridge ← /game-state + /game-input
```

---

## Run

```bash
cd led-hexagon && ./scripts/start-dev.sh
```

See [`LED_HEX_DEVELOPMENT_PLAYBOOK.md`](./LED_HEX_DEVELOPMENT_PLAYBOOK.md) for full detail.
