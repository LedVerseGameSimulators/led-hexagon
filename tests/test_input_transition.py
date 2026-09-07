"""Regression tests for level-transition input lifecycle and phantom presses."""

from __future__ import annotations

import threading
import time

import pytest

from api import game_manager
from game_play.game_running import LedTable


def _transition_game():
    game = object.__new__(game_manager.GameInstance)
    game.running = True
    game.current_level_id = "001"
    game.current_state = {
        "game_over": False,
        "result": None,
        "life": 20,
        "display_lives": 5,
    }
    game.led_table = LedTable(wall_light_arr_len=100, led_row=16, led_col=26)
    game.zone = (0, 16, 0, 26)
    game.input_lock = threading.Lock()
    game._sim_pressed = set()
    game._suppress_until_release = set()
    game._hint_pressed = set()
    game.accepting_input = True
    game.phase = "playing"
    game.goal_cells = {(4, 5)}
    game.goal2_cells = set()
    game.red_cells = {(2, 3)}
    game.deduct_cells = set()
    game.hint_cells = set()
    game.scored_active = set()
    game.scored_active2 = set()
    game.max_life = 20
    game.life = 20
    game.score = 5
    game.score2 = 0
    game.multiplayer = False
    game.last_life_loss_time = 0.0
    game._life_count_time = 1.2
    game._memory_mode = False
    game.pending_respawn = []
    game._session_over = False
    game._end_reason = None
    game.play = None
    game.flashes = {}
    game.p2_next_cells = set()
    game.revealed_colors = {}
    game.revealed_live_red = set()
    return game


def test_transition_gate_blocks_stale_input_until_new_level_is_ready():
    game = _transition_game()
    scored = []
    game.try_score_cell = lambda row, col, total_pass=None: scored.append((row, col))

    game.begin_level_transition()

    assert game.apply_input(4, 5, "press") is False
    assert scored == []
    assert game.goal_cells == set()
    assert game.red_cells == set()

    game.finish_level_transition()

    assert game.apply_input(4, 5, "press") is True
    assert scored == []

    game.process_frame_input(
        goal_cells={(4, 5)},
        goal2_cells=set(),
        red_cells=set(),
        deduct_cells=set(),
    )

    assert scored == [(4, 5)]


def test_transition_clears_hardware_only_pressed_state():
    game = _transition_game()
    game.led_table.state_table[2][3] = 1
    assert (2, 3) not in game._sim_pressed

    game.begin_level_transition()

    assert not any(any(row) for row in game.led_table.state_table)
    assert game.scored_active == set()
    assert game.red_cells == set()


def test_held_cell_suppressed_across_level_transition_no_phantom_penalty():
    """Stale HW hold at arm time must not score/hurt until release then fresh press."""
    game = _transition_game()

    game.begin_level_transition()
    game.led_table.state_table[2][3] = 1
    game.finish_level_transition()
    assert (2, 3) in game._suppress_until_release

    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )

    assert game.life == 20
    assert game.score == 5

    game.led_table.state_table[2][3] = 0
    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert (2, 3) not in game._suppress_until_release

    game.last_life_loss_time = 0.0
    game.led_table.state_table[2][3] = 1
    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )

    assert game.life == 19
    assert game.score == 4


def test_fresh_red_press_still_rate_limits():
    game = _transition_game()
    game.finish_level_transition()
    game.last_life_loss_time = 0.0

    game.led_table.state_table[2][3] = 1
    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert game.life == 19

    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert game.life == 19

    game.last_life_loss_time = 0.0
    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert game.life == 18


def test_fresh_sim_press_after_release_from_baseline_suppress():
    game = _transition_game()
    game.begin_level_transition()
    game.led_table.state_table[2][3] = 1
    game.finish_level_transition()

    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert game.life == 20

    game.apply_input(2, 3, "release")
    game.last_life_loss_time = 0.0
    game.apply_input(2, 3, "press")
    game.process_frame_input(
        goal_cells=set(),
        goal2_cells=set(),
        red_cells={(2, 3)},
        deduct_cells=set(),
    )
    assert game.life == 19


def test_attempt_seam_gates_input_through_load_and_setup(monkeypatch):
    from pathlib import Path

    game = _transition_game()
    path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "levels" / "score_once.led"
    original_loader = game_manager._load_level_file
    phases = []

    def tracking_loader(level_path):
        phases.append(("load", game.accepting_input))
        return original_loader(level_path)

    def setup_consumer(groups, level):
        phases.append(("setup", game.accepting_input))

    def play_consumer(groups):
        phases.append(("play", game.accepting_input))

    monkeypatch.setattr(game_manager, "_load_level_file", tracking_loader)

    game_manager._run_level_attempt(
        str(path),
        led_table=game.led_table,
        level_id="001",
        setup_consumer=setup_consumer,
        play_consumer=play_consumer,
        transition_consumer=game.begin_level_transition,
        ready_consumer=game.finish_level_transition,
    )

    assert phases == [("load", False), ("setup", False), ("play", True)]


def test_l1_to_l2_phantom_red_no_life_loss(client, monkeypatch):
    """Integration: held sim tile through L1→L2 must not drain life on L2 open."""
    from tests.test_effects_session_loop import (
        FIXTURE_LEVELS,
        _poll_state,
        _start_session,
        _wait_phase,
    )

    levels = [
        str(FIXTURE_LEVELS / "fast_clear.led"),
        str(FIXTURE_LEVELS / "score_once.led"),
    ]
    game_id = _start_session(client, monkeypatch, levels=levels, life="20")
    _wait_phase(client, game_id, "playing", timeout=8.0)

    from api.game_manager import get_manager

    game = get_manager().get_game(game_id)
    assert game is not None
    game.led_table.state_table[2][3] = 1

    _wait_phase(client, game_id, "level_clear", timeout=8.0)
    _wait_phase(client, game_id, "countdown", timeout=8.0)
    state = _wait_phase(client, game_id, "playing", timeout=8.0)

    life_before = state.get("life", 20)
    score_before = state.get("score", 0)
    time.sleep(1.5)
    mid = _poll_state(client, game_id)
    assert mid.get("life") == life_before
    assert mid.get("score") == score_before
