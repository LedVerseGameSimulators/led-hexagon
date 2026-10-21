"""Step 0: hex_scores RFID play-fact columns and poll cursor (A1)."""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def scores_db(monkeypatch):
    tmp = tempfile.mkdtemp()
    setting = Path(tmp) / "setting"
    setting.mkdir()
    db_path = setting / "ledplaydb.sqlite"
    import api.database as db_mod
    monkeypatch.setattr(db_mod, "_SCORES_DB", str(db_path))
    db_mod._db = None
    db = db_mod.get_db()
    yield db, db_path
    db_mod._db = None


def test_record_and_get_scores_since_includes_rfid_fields(scores_db):
    db, _path = scores_db
    ts_before = "2020-01-01T00:00:00"
    ok = db.record_game_score({
        "card_id": "CARD1",
        "card_id2": "CARD2",
        "multiplayer": True,
        "level": "1",
        "score": 100,
        "score2": 80,
        "play_mode": "team_battle",
        "session_id": 10,
        "group_id": 5,
        "roster_size_at_play": 4,
        "roster_player_ids": [1, 2, 3, 4],
        "session_id2": 11,
        "group_id2": 6,
        "roster_size_at_play2": 3,
        "roster_player_ids2": [7, 8, 9],
    })
    assert ok
    rows = db.get_scores_since(ts_before)
    assert len(rows) == 1
    row = rows[0]
    assert row["play_mode"] == "team_battle"
    assert row["session_id"] == 10
    assert row["group_id"] == 5
    assert row["roster_size_at_play"] == 4
    assert row["roster_player_ids"] == "[1, 2, 3, 4]"
    assert row["session_id2"] == 11
    assert row["group_id2"] == 6
    assert row["roster_size_at_play2"] == 3
    assert row["roster_player_ids2"] == "[7, 8, 9]"


def test_get_scores_since_uses_gte_cursor(scores_db):
    db, _path = scores_db
    db.record_game_score({"card_id": "A", "level": "1", "score": 1})
    rows = db.get_scores_since("2099-01-01T00:00:00")
    assert len(rows) == 0
    # Same-second re-read: ts >= since must return the row when since equals ts
    ts = db.get_scores_since("2000-01-01T00:00:00")[0]["ts"]
    again = db.get_scores_since(ts)
    assert len(again) >= 1
    assert again[0]["ts"] == ts
