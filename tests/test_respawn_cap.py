"""2P respawn cap: max 8 reappearances per tile."""

from __future__ import annotations

import time
from types import SimpleNamespace

from api import game_manager


def _active_group(cell):
    return SimpleNamespace(
        start_member={(cell[0], cell[1])},
        start_time_sec=0.0,
        end_time_sec=600.0,
    )


def test_respawn_cap_stops_after_eight_enqueues():
    game = game_manager.GameInstance("g", "card", 1, "normal")
    game.multiplayer = True
    cell = (4, 5)
    group = _active_group(cell)
    game.dict_group = {"g1": group}

    for _ in range(game_manager._MAX_RESPAWNS_PER_CELL):
        group.start_member.add(cell)
        game._consume_cell(cell[0], cell[1], total_pass=1.0)

    assert game.respawn_counts[cell] == game_manager._MAX_RESPAWNS_PER_CELL
    assert len(game.pending_respawn) == game_manager._MAX_RESPAWNS_PER_CELL

    group.start_member.add(cell)
    game._consume_cell(cell[0], cell[1], total_pass=2.0)
    assert len(game.pending_respawn) == game_manager._MAX_RESPAWNS_PER_CELL


def test_respawn_counts_reset_on_level_reset():
    game = game_manager.GameInstance("g", "card", 1, "normal")
    game.multiplayer = True
    game.respawn_counts[(1, 1)] = 5
    game.pending_respawn.append([None, (1, 1), time.time() + 10])

    game.reset_for_level()

    assert game.respawn_counts == {}
    assert game.pending_respawn == []


def test_1p_never_enqueues_respawn():
    game = game_manager.GameInstance("g", "card", 1, "normal")
    game.multiplayer = False
    cell = (2, 3)
    group = _active_group(cell)
    game.dict_group = {"g1": group}

    game._consume_cell(cell[0], cell[1], total_pass=1.0)

    assert game.pending_respawn == []
    assert game.respawn_counts == {}
