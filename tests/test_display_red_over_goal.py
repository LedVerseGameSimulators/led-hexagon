"""Moving red display priority over scoreables and memory teal."""

from __future__ import annotations

from types import SimpleNamespace

from api import game_manager


def _floor_group(*, cells, color, start=0.0, end=600.0, speed=1.0):
    return SimpleNamespace(
        type=game_manager._FLOOR_LIGHT,
        start_member=set(cells),
        start_time_sec=start,
        end_time_sec=end,
        speed=speed,
        color=color,
    )


def _wall_indicator(color):
    return SimpleNamespace(
        type=game_manager._WALL_LIGHT,
        start_member={(0, 0)},
        start_time_sec=0.0,
        end_time_sec=600.0,
        color=color,
    )


RED_FULL = [[0, 254, 0], [254, 0, 0], [254, 0, 0]]
GOAL_FULL = [[0, 254, 0], [0, 0, 254], [0, 0, 254]]
TEAL = game_manager._TEAL_HIDDEN


def test_display_red_wins_over_goal_overlap_normal_mode():
    overlap = (3, 4)
    dgroup = {
        "goal": _floor_group(cells=[overlap], color=GOAL_FULL, speed=0),
        "red": _floor_group(cells=[overlap], color=RED_FULL, speed=1.0),
        "ind": _wall_indicator(GOAL_FULL),
    }
    gc = game_manager._group_main_color(GOAL_FULL)
    winners = game_manager._build_display_winners(
        dgroup,
        total_pass=10.0,
        gc=gc,
        gc2=None,
        rows=16,
        cols=26,
    )
    led_display = [TEAL[:] for _ in range(16 * 26)]
    game_manager._apply_display_hazards(led_display, winners, 26)

    painted = led_display[overlap[0] * 26 + overlap[1]]
    assert game_manager._group_main_color(painted) == (254, 0, 0)


def test_display_red_wins_over_teal_hidden_goal_overlap():
    overlap = (5, 6)
    dgroup = {
        "goal": _floor_group(cells=[overlap], color=GOAL_FULL, speed=0),
        "red": _floor_group(cells=[overlap], color=RED_FULL, speed=1.0),
        "ind": _wall_indicator(GOAL_FULL),
    }
    gc = game_manager._group_main_color(GOAL_FULL)
    winners = game_manager._build_display_winners(
        dgroup,
        total_pass=10.0,
        gc=gc,
        gc2=None,
        rows=16,
        cols=26,
    )
    hazard_overlay = game_manager._display_hazard_cells(winners)
    assert overlap in hazard_overlay

    led_display = [TEAL[:] for _ in range(16 * 26)]
    # Memory teal hide would paint teal first; hazard overlay skips that cell.
    if overlap not in hazard_overlay:
        led_display[overlap[0] * 26 + overlap[1]] = TEAL
    game_manager._apply_display_hazards(led_display, winners, 26)

    painted = led_display[overlap[0] * 26 + overlap[1]]
    assert game_manager._group_main_color(painted) == (254, 0, 0)


def test_interaction_still_prefers_goal_over_red_at_overlap():
    """DK09-style: goal-colored red tile scores, not penalized."""
    overlap = (2, 2)
    red_goal = [[0, 254, 0], [254, 0, 0], [254, 0, 0]]
    dgroup = {
        "goal": _floor_group(cells=[overlap], color=red_goal, speed=0),
        "ind": _wall_indicator(red_goal),
    }
    gc = game_manager._group_main_color(red_goal)
    winners = game_manager._build_display_winners(
        dgroup,
        total_pass=5.0,
        gc=gc,
        gc2=None,
        rows=16,
        cols=26,
    )
    rank, category, _ = winners[overlap]
    assert category == "goal"
    assert rank == game_manager._DISPLAY_RANK_GOAL
