"""Effects session-loop integration tests (TESTING_CONTRACT T1–T8)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_LEVELS = REPO_ROOT / "tests" / "fixtures" / "levels"


def _poll_state(client, game_id: str, timeout: float = 15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/game-state/{game_id}")
        data = resp.json()
        if data.get("success"):
            return data["state"]
        time.sleep(0.02)
    raise TimeoutError(f"game-state/{game_id} never became available")


def _wait_phase(client, game_id: str, phase: str, timeout: float = 15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _poll_state(client, game_id, timeout=1.0)
        if state.get("phase") == phase:
            return state
        time.sleep(0.02)
    raise TimeoutError(f"Timed out waiting for phase={phase!r}")


def _wait_until(client, game_id: str, predicate, timeout: float = 15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _poll_state(client, game_id, timeout=1.0)
        if predicate(state):
            return state
        time.sleep(0.02)
    raise TimeoutError("Timed out waiting for condition")


def _start_session(client, monkeypatch, *, levels=None, session_sec: str = "120", life: str = "20"):
    if levels is not None:
        monkeypatch.setattr(
            "api.game_manager._build_level_sequence",
            lambda _start: list(levels),
        )
    monkeypatch.setenv("HEX_TEST_SESSION_SEC", session_sec)
    monkeypatch.setenv("HEX_TEST_LIFE", life)
    resp = client.post(
        "/start-game",
        json={"card_id": "TEST001", "level": "fast_clear", "difficulty": "easy"},
    )
    data = resp.json()
    assert data.get("success"), data
    return data["game_id"]


def test_t1_session_start_reaches_playing(client, monkeypatch):
    """T1: countdown then playing with accepting_input=true."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "fast_clear.led")],
    )
    _wait_phase(client, game_id, "countdown", timeout=8.0)
    state = _wait_phase(client, game_id, "playing", timeout=8.0)
    assert state.get("accepting_input") is True


def test_t7_input_gated_during_countdown(client, monkeypatch):
    """T7: presses ignored while accepting_input=false."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "score_once.led")],
    )
    state = _wait_phase(client, game_id, "countdown", timeout=8.0)
    assert state.get("accepting_input") is False
    score_before = state.get("score", 0)
    client.post(
        "/game-input",
        json={"game_id": game_id, "row": 2, "col": 4, "type": "press"},
    )
    time.sleep(0.05)
    mid = _poll_state(client, game_id)
    assert mid.get("phase") == "countdown"
    assert mid.get("score", 0) == score_before


def test_t8_playing_accepts_input(client, monkeypatch):
    """T8: valid press during playing changes score."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "score_once.led")],
    )
    _wait_phase(client, game_id, "playing", timeout=8.0)
    before = _poll_state(client, game_id).get("score", 0)
    client.post(
        "/game-input",
        json={"game_id": game_id, "row": 2, "col": 4, "type": "press"},
    )
    after = _wait_until(
        client,
        game_id,
        lambda st: st.get("score", 0) > before,
        timeout=8.0,
    )
    assert after.get("accepting_input") is True
    assert after.get("score", 0) > before


def test_t2_countdown_between_levels(client, monkeypatch):
    """T2: level_clear → countdown → playing on next level."""
    levels = [
        str(FIXTURE_LEVELS / "fast_clear.led"),
        str(FIXTURE_LEVELS / "fast_clear.led"),
    ]
    game_id = _start_session(client, monkeypatch, levels=levels)
    _wait_phase(client, game_id, "playing", timeout=8.0)
    _wait_phase(client, game_id, "level_clear", timeout=8.0)
    _wait_phase(client, game_id, "countdown", timeout=8.0)
    state = _wait_phase(client, game_id, "playing", timeout=8.0)
    assert state.get("levels_cleared", 0) >= 1


def test_t3_level_fail_restart_same_level(client, monkeypatch, manager):
    """T3: life=0 (>10 s left) → fail → countdown → playing, score preserved."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "score_once.led")],
        life="1",
    )
    _wait_phase(client, game_id, "playing", timeout=8.0)
    game = manager.get_game(game_id)
    assert game is not None
    game.score = 3
    game.life = 0
    _wait_phase(client, game_id, "level_fail", timeout=8.0)
    _wait_phase(client, game_id, "countdown", timeout=8.0)
    state = _wait_phase(client, game_id, "playing", timeout=8.0)
    assert state.get("score") == 3


def test_t4_session_end_on_timer_no_countdown(client, monkeypatch):
    """T4: timer expire → clear/session_end, no countdown afterward."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "score_once.led")],
        session_sec="1",
    )
    _wait_phase(client, game_id, "playing", timeout=8.0)
    _wait_until(
        client,
        game_id,
        lambda st: st.get("game_over") is True,
        timeout=12.0,
    )
    final = _poll_state(client, game_id)
    assert final.get("phase") in ("session_end", "level_clear")
    assert final.get("game_over") is True


def test_t5_session_end_life_le_10s_no_fail_panel(client, monkeypatch, manager):
    """T5: life=0 with ≤10 s left → clear/session_end, not level_fail."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "score_once.led")],
        session_sec="120",
        life="1",
    )
    _wait_phase(client, game_id, "playing", timeout=8.0)
    game = manager.get_game(game_id)
    game.session_start = time.time() - (game.game_time_sec - 5.0)
    game.life = 0
    _wait_until(
        client,
        game_id,
        lambda st: st.get("game_over") is True,
        timeout=10.0,
    )
    final = _poll_state(client, game_id)
    assert final.get("phase") in ("session_end", "level_clear")
    phases_seen = []
    # Fail panel must not be the terminal phase
    assert final.get("phase") != "level_fail"


def test_t6_last_level_cleared_session_end(client, monkeypatch):
    """T6: final level clear → session end without another countdown."""
    game_id = _start_session(
        client,
        monkeypatch,
        levels=[str(FIXTURE_LEVELS / "fast_clear.led")],
    )
    _wait_phase(client, game_id, "playing", timeout=8.0)
    _wait_phase(client, game_id, "level_clear", timeout=8.0)
    _wait_until(
        client,
        game_id,
        lambda st: st.get("game_over") is True,
        timeout=10.0,
    )
    final = _poll_state(client, game_id)
    assert final.get("game_over") is True
    assert final.get("phase") in ("session_end", "level_clear")


def test_effect_led_fixture_shape(load_level_archive):
    """Regression: effect archives are 5×9 with 33 members per group."""
    for name in ("countdown.led", "level_clear.led", "level_fail.led"):
        groups, game = load_level_archive(f"tests/fixtures/effects/{name}")
        assert game.row == 5 and game.col == 9
        if name == "countdown.led":
            assert len(groups) == 3
        else:
            assert len(groups) == 1
        for group in groups.values():
            assert len(group.start_member) == 33


@pytest.fixture(scope="session")
def load_level_archive():
    import shelve
    import tempfile
    import zipfile

    repo = REPO_ROOT

    def load(relative_path: str):
        path = repo / relative_path
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path, "r") as archive:
                archive.extractall(tmpdir)
            for root, _, files in os.walk(tmpdir):
                if not any(
                    f.startswith("game_file") and f.split(".", 1)[-1] in ("dat", "db")
                    for f in files
                ):
                    continue
                with shelve.open(os.path.join(root, "game_file"), flag="r") as db:
                    game = db.get("para_key_game")
                    groups = db.get("dict_group")
                    if game is not None and groups is not None:
                        return groups, game
        raise AssertionError(f"Could not load {path}")

    return load
