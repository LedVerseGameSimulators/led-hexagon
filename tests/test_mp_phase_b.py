"""Phase B multiplayer: either-player wave advance + vacuous-empty latch."""

from __future__ import annotations

from types import SimpleNamespace

from api import game_manager

P1_COLOR = [[0, 254, 0], [0, 0, 254], [0, 0, 254]]
P2_COLOR = [[0, 254, 0], [254, 128, 0], [254, 128, 0]]


def _floor(*, cells, color, start=0.0, end=600.0):
    return SimpleNamespace(
        type=game_manager._FLOOR_LIGHT,
        start_member=set(cells),
        start_time_sec=start,
        end_time_sec=end,
        color=color,
    )


def _mp_game():
    game = game_manager.GameInstance("mp-b", "card", "DK01", "normal")
    game.multiplayer = True
    game._memory_mode = True
    game._mp_p1_had_wave_tiles = False
    game._mp_p2_had_wave_tiles = False
    game.pending_respawn = []
    game.scored_active = set()
    game.scored_active2 = set()
    game.revealed_colors = {}
    game.revealed_live_red = set()
    return game


def test_vacuous_empty_p2_does_not_advance_while_p1_has_tiles():
    game = _mp_game()
    goal_cells = {(1, 1)}
    goal2_cells = set()
    assert game_manager._mp_wave_ready(game, goal_cells, goal2_cells) is False


def test_p1_clear_advances_when_p2_never_had_wave_tiles():
    game = _mp_game()
    game._mp_p1_had_wave_tiles = True
    assert game_manager._mp_wave_ready(game, set(), set()) is True


def test_p2_vacuous_empty_does_not_count_as_cleared():
    game = _mp_game()
    game._mp_p2_had_wave_tiles = False
    goal_cells = {(2, 2)}
    goal2_cells = set()
    assert game_manager._mp_wave_ready(game, goal_cells, goal2_cells) is False


def test_p1_clear_discards_p2_current_wave_leftovers():
    game = _mp_game()
    groups = {
        "p2_left": _floor(cells=[(3, 3), (3, 4)], color=P2_COLOR, start=0.0, end=60.0),
        "p2_future": _floor(cells=[(5, 5)], color=P2_COLOR, start=70.0, end=600.0),
    }
    gc = game_manager._group_main_color(P1_COLOR)
    gc2 = game_manager._group_main_color(P2_COLOR)
    dropped = game_manager._mp_discard_side_current_wave(
        game, groups, 30.0, gc, gc2, 2
    )
    assert dropped == {(3, 3), (3, 4)}
    assert groups["p2_left"].start_member == set()
    assert (5, 5) in groups["p2_future"].start_member


def test_discard_clears_pending_respawn_and_memory_reveals():
    game = _mp_game()
    cell = (4, 4)
    group = _floor(cells=[cell], color=P2_COLOR)
    groups = {"p2": group}
    gc = game_manager._group_main_color(P1_COLOR)
    gc2 = game_manager._group_main_color(P2_COLOR)
    game.pending_respawn.append([group, cell, 9999.0])
    game.revealed_colors[cell] = [[0, 0, 0], [1, 2, 3], [1, 2, 3]]
    game.revealed_live_red.add(cell)

    dropped = game_manager._mp_discard_side_current_wave(
        game, groups, 10.0, gc, gc2, 2
    )

    assert dropped == {cell}
    assert game.pending_respawn == []
    assert cell not in game.revealed_colors
    assert cell not in game.revealed_live_red


def test_wave_clearing_sides_lists_only_sides_that_had_tiles():
    game = _mp_game()
    game._mp_p1_had_wave_tiles = True
    game._mp_p2_had_wave_tiles = False
    assert game_manager._mp_wave_clearing_sides(game, set(), {(1, 1)}) == [1]


def test_same_color_2p_checkerboard_split_on_discard():
    shared = [[0, 254, 0], [0, 255, 255], [0, 255, 255]]
    p1_cell = (2, 2)  # even sum -> P1
    p2_cell = (2, 3)  # odd sum -> P2
    groups = {"shared": _floor(cells=[p1_cell, p2_cell], color=shared)}
    game = _mp_game()
    gc = gc2 = game_manager._group_main_color(shared)

    dropped = game_manager._mp_discard_side_current_wave(
        game, groups, 5.0, gc, gc2, 2
    )

    assert dropped == {p2_cell}
    assert p1_cell in groups["shared"].start_member
    assert p2_cell not in groups["shared"].start_member


def test_1p_wave_ready_requires_both_sides_empty():
    game = game_manager.GameInstance("1p", "card", 1, "normal")
    game.multiplayer = False
    assert game_manager._mp_wave_ready(game, {(1, 1)}, set()) is False
    # 1P uses the frame callback branch, not _mp_wave_ready — smoke that
    # helpers do not false-positive for non-MP callers.
    assert game._mp_p1_had_wave_tiles is False


def test_latch_fields_reset_on_level_reset():
    game = _mp_game()
    game._mp_p1_had_wave_tiles = True
    game._mp_p2_had_wave_tiles = True
    game.reset_for_level()
    assert game._mp_p1_had_wave_tiles is False
    assert game._mp_p2_had_wave_tiles is False
