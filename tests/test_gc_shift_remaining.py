"""Pro 04-style gc-shift: remaining/jump use all level goal colors."""

from __future__ import annotations

from types import SimpleNamespace

from api import game_manager

CYAN = [[0, 254, 0], [0, 255, 255], [0, 255, 255]]
MAGENTA = [[0, 254, 0], [255, 0, 255], [255, 0, 255]]
DEDUCT = [[0, 254, 0], [254, 0, 48], [254, 0, 48]]


def _floor(*, cells, color, start=0.0, end=600.0):
    return SimpleNamespace(
        type=game_manager._FLOOR_LIGHT,
        start_member=set(cells),
        start_time_sec=start,
        end_time_sec=end,
        color=color,
    )


def _wall(*, color, start=0.0, end=600.0):
    return SimpleNamespace(
        type=game_manager._WALL_LIGHT,
        start_member={(0, 0)},
        start_time_sec=start,
        end_time_sec=end,
        color=color,
    )


def test_level_goal_colors_unions_all_indicator_phases():
    groups = {
        "ind_cyan": _wall(color=CYAN, start=0.0, end=60.0),
        "ind_mag": _wall(color=MAGENTA, start=60.0, end=600.0),
    }
    colors = game_manager._level_goal_colors(groups)
    assert game_manager._group_main_color(CYAN) in colors
    assert game_manager._group_main_color(MAGENTA) in colors


def test_remaining_counts_prior_phase_scoreables_after_gc_shift():
    """After cyan→magenta, leftover cyan tiles must still block level clear."""
    groups = {
        "ind_cyan": _wall(color=CYAN, start=0.0, end=60.0),
        "ind_mag": _wall(color=MAGENTA, start=60.0, end=600.0),
        "cyan_left": _floor(cells=[(2, 2), (2, 3)], color=CYAN, start=0.0, end=600.0),
        "mag_future": _floor(cells=[(5, 5)], color=MAGENTA, start=70.0, end=600.0),
    }
    level_goal_colors = game_manager._level_goal_colors(groups)
    remaining = game_manager._count_remaining_scoreable(groups, level_goal_colors)

    live_gc = game_manager._group_main_color(MAGENTA)
    # Old bug: only live gc → cyan leftovers ignored → remaining == 1 (magenta only)
    # or 0 if magenta wave not yet started with empty start_member check.
    old_style = 0
    for g in groups.values():
        if getattr(g, "type", None) != game_manager._FLOOR_LIGHT:
            continue
        sm = getattr(g, "start_member", None)
        if not sm:
            continue
        mc = game_manager._group_main_color(g.color)
        if game_manager._rgb_is_deduct(mc):
            continue
        if mc == live_gc:
            old_style += len(sm)

    assert old_style == 1  # only magenta future tile
    assert remaining == 3  # cyan leftovers + magenta future


def test_next_wave_finds_future_color_after_prior_phase_cleared():
    groups = {
        "ind_cyan": _wall(color=CYAN, start=0.0, end=60.0),
        "ind_mag": _wall(color=MAGENTA, start=60.0, end=600.0),
        "mag_wave": _floor(cells=[(4, 4)], color=MAGENTA, start=70.0, end=600.0),
    }
    level_goal_colors = game_manager._level_goal_colors(groups)
    assert game_manager._next_scoreable_wave_start(groups, 65.0, level_goal_colors) == 70.0


def test_deduct_floor_not_counted_as_scoreable():
    groups = {
        "ind": _wall(color=CYAN),
        "deduct": _floor(cells=[(1, 1)], color=DEDUCT),
        "goal": _floor(cells=[(3, 3)], color=CYAN),
    }
    level_goal_colors = game_manager._level_goal_colors(groups)
    assert game_manager._count_remaining_scoreable(groups, level_goal_colors) == 1
