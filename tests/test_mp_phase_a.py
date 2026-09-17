"""Phase A multiplayer: lives-only hazards + 3-ring goal HUD payload."""

from __future__ import annotations

from pathlib import Path

from api import game_manager
from api.game_manager import GameManager, GAMES_ROOT


GOAL_FULL = [[10, 20, 30], [40, 50, 60], [70, 80, 90]]
GOAL2_FULL = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def _hazard_game(*, multiplayer: bool, memory: bool = False):
    game = game_manager.GameInstance("phase-a", "card", "DK01", "normal")
    game.multiplayer = multiplayer
    game.accepting_input = True
    game._memory_mode = memory
    game.score = 10
    game.score2 = 8
    game.life = 20
    game.last_life_loss_time = 0.0
    game._life_count_time = 0.0  # disable rate-limit for unit asserts
    game.red_cells = set()
    game.deduct_cells = set()
    game.hint_cells = set()
    game.goal_cells = set()
    game.goal2_cells = set()
    game.scored_active = set()
    game.scored_active2 = set()
    game.revealed_live_red = set()
    game.revealed_colors = {}
    game._hint_pressed = set()
    game._hint_score_cost = 5
    game._reveal_duration = 2.0
    game._reveal_until = 0.0
    game._reveal2_until = 0.0
    game._deduct_color_full = [[254, 0, 48], [254, 0, 48], [254, 0, 48]]
    game._goal_color_full = GOAL_FULL
    game._goal2_color_full = GOAL2_FULL
    game.goal_color = GOAL_FULL[1]
    game.goal2_color = GOAL2_FULL[1]
    game.dict_group = {}
    game.flashes = {}
    game.pending_respawn = []
    game.respawn_counts = {}
    game.play = None
    return game


def test_dk01_ledb_exists_and_create_game_sets_multiplayer():
    ledb = Path(GAMES_ROOT) / "source" / "---" / "DK01.ledb"
    assert ledb.is_file(), f"missing {ledb}"

    mgr = GameManager()
    try:
        gid = mgr.create_game("card-mp", "DK01", "normal")
        game = mgr.get_game(gid)
        assert game is not None
        assert game.multiplayer is True
    finally:
        mgr.clear_all()


def test_mp_goal_color_payload_publishes_3_rings():
    game = _hazard_game(multiplayer=True)
    payload = game._mp_goal_color_payload()
    assert payload["goal_color"] == GOAL_FULL[1]
    assert payload["goal2_color"] == GOAL2_FULL[1]
    assert payload["goal_color_rings"] == GOAL_FULL
    assert payload["goal2_color_rings"] == GOAL2_FULL


def test_mp_goal_color_payload_null_when_1p():
    game = _hazard_game(multiplayer=False)
    payload = game._mp_goal_color_payload()
    assert payload == {
        "goal_color": None,
        "goal2_color": None,
        "goal_color_rings": None,
        "goal2_color_rings": None,
    }


def test_mp_goal_color_payload_falls_back_to_flat_mid():
    game = _hazard_game(multiplayer=True)
    game._goal_color_full = None
    game._goal2_color_full = None
    game.goal_color = [11, 22, 33]
    game.goal2_color = [44, 55, 66]
    payload = game._mp_goal_color_payload()
    assert payload["goal_color"] == [11, 22, 33]
    assert payload["goal2_color"] == [44, 55, 66]
    assert payload["goal_color_rings"] == [[11, 22, 33]] * 3
    assert payload["goal2_color_rings"] == [[44, 55, 66]] * 3


def test_mp_plain_red_via_helper_life_only_scores_flat():
    game = _hazard_game(multiplayer=True)
    game.red_cells = {(1, 1)}
    game.try_score_cell(1, 1)
    assert game.life == 19
    assert game.score == 10
    assert game.score2 == 8


def test_mp_non_memory_deduct_life_only_scores_flat():
    game = _hazard_game(multiplayer=True, memory=False)
    game.deduct_cells = {(2, 2)}
    game.try_score_cell(2, 2)
    assert game.life == 19
    assert game.score == 10
    assert game.score2 == 8
    assert (2, 2) in game.scored_active


def test_mp_memory_deduct_via_helper_life_only_scores_flat():
    game = _hazard_game(multiplayer=True, memory=True)
    game.deduct_cells = {(3, 3)}
    game.try_score_cell(3, 3)
    assert game.life == 19
    assert game.score == 10
    assert game.score2 == 8
    assert (3, 3) in game.revealed_live_red


def test_mp_hint_penalty_still_scores_unchanged():
    """Out of scope for Phase A — confirm hint still deducts score, not life."""
    game = _hazard_game(multiplayer=True, memory=True)
    game.hint_cells = {(4, 4)}
    game.try_score_cell(4, 4, total_pass=0.0)  # phase 0 → P1
    assert game.score == 5
    assert game.score2 == 8
    assert game.life == 20

    game2 = _hazard_game(multiplayer=True, memory=True)
    game2.hint_cells = {(4, 5)}
    game2.try_score_cell(4, 5, total_pass=2.0)  # phase 1 → P2
    assert game2.score == 10
    assert game2.score2 == 3
    assert game2.life == 20


def test_1p_red_still_score_and_life():
    game = _hazard_game(multiplayer=False)
    game.red_cells = {(5, 5)}
    game.try_score_cell(5, 5)
    assert game.life == 19
    assert game.score == 9
    assert game.score2 == 8


def test_1p_non_memory_deduct_still_score_and_life():
    game = _hazard_game(multiplayer=False, memory=False)
    game.deduct_cells = {(6, 6)}
    game.try_score_cell(6, 6)
    assert game.life == 19
    assert game.score == 9
    assert game.score2 == 8


class _FakeAudio:
    def __init__(self):
        self.hurt = 0
        self.score = 0

    def play_hurt_sfx(self):
        self.hurt += 1

    def play_score_sfx(self):
        self.score += 1


def test_normal_non_memory_deduct_plays_hurt_sfx():
    game = _hazard_game(multiplayer=True, memory=False)
    audio = _FakeAudio()
    game._audio = audio
    game.deduct_cells = {(7, 7)}
    game.try_score_cell(7, 7)
    assert audio.hurt == 1
    assert audio.score == 0


def test_normal_red_plays_hurt_sfx_via_helper():
    game = _hazard_game(multiplayer=True, memory=False)
    audio = _FakeAudio()
    game._audio = audio
    game.red_cells = {(8, 8)}
    game.try_score_cell(8, 8)
    assert audio.hurt == 1


def test_normal_p1_and_p2_scoreable_play_score_sfx():
    game = _hazard_game(multiplayer=True, memory=False)
    audio = _FakeAudio()
    game._audio = audio
    game.goal_cells = {(9, 1)}
    game.goal2_cells = {(9, 2)}
    game.try_score_cell(9, 1)
    game.try_score_cell(9, 2)
    assert audio.score == 2
    assert audio.hurt == 0
