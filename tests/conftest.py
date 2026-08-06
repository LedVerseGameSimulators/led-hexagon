"""Pytest setup for LED Hexagon effects session-loop tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
GAMES_ROOT = REPO_ROOT / "games"

for path in (REPO_ROOT, GAMES_ROOT):
    path_string = str(path)
    if path_string not in sys.path:
        sys.path.insert(0, path_string)

os.environ.setdefault("USE_SERIAL_HD", "0")
os.environ.setdefault("ENABLE_AUDIO", "0")
os.environ.setdefault("HEX_EFFECTS_DIR", str(REPO_ROOT / "tests" / "fixtures" / "effects"))
os.environ.setdefault("HEX_TEST_SESSION_SEC", "120")
os.environ.setdefault("HEX_TEST_LIFE", "20")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app)


@pytest.fixture
def manager():
    from api.game_manager import get_manager

    return get_manager()
