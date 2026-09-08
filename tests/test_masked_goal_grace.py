"""Masked-goal grace (Climb parity) for Hex level completion."""

from __future__ import annotations

import time

from api import game_manager


def _apply_grace(game, *, total_pass, remaining, goals, goals2, next_start):
    if (
        total_pass > 1.5
        and remaining > 0
        and not goals
        and not goals2
        and next_start is None
    ):
        now_mono = time.monotonic()
        if game._no_reachable_goal_since is None:
            game._no_reachable_goal_since = now_mono
            return "waiting"
        if (
            now_mono - game._no_reachable_goal_since
            >= game_manager._MASKED_GOAL_GRACE
        ):
            game._level_cleared = True
            return "clear"
        return "waiting"
    game._no_reachable_goal_since = None
    return "reset"


def test_masked_goal_grace_constant_default():
    assert game_manager._MASKED_GOAL_GRACE >= 1.0


def test_masked_goal_grace_clears_after_timeout(monkeypatch):
    game = game_manager.GameInstance("g", "card", 1, "normal")
    clock = {"t": 100.0}
    monkeypatch.setattr(game_manager.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(game_manager, "_MASKED_GOAL_GRACE", 1.0)

    assert (
        _apply_grace(
            game,
            total_pass=60.0,
            remaining=2,
            goals=set(),
            goals2=set(),
            next_start=None,
        )
        == "waiting"
    )
    clock["t"] = 101.0
    assert (
        _apply_grace(
            game,
            total_pass=61.0,
            remaining=2,
            goals=set(),
            goals2=set(),
            next_start=None,
        )
        == "clear"
    )
    assert game._level_cleared is True


def test_masked_goal_grace_resets_when_goals_reappear(monkeypatch):
    game = game_manager.GameInstance("g", "card", 1, "normal")
    clock = {"t": 50.0}
    monkeypatch.setattr(game_manager.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(game_manager, "_MASKED_GOAL_GRACE", 1.0)

    _apply_grace(
        game,
        total_pass=60.0,
        remaining=2,
        goals=set(),
        goals2=set(),
        next_start=None,
    )
    assert (
        _apply_grace(
            game,
            total_pass=60.2,
            remaining=2,
            goals={(1, 1)},
            goals2=set(),
            next_start=None,
        )
        == "reset"
    )
    assert game._no_reachable_goal_since is None
