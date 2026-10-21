"""Round 2: logout must not write scores; legacy hex_scores gets life column."""
import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def scores_db(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    setting = Path(tmpdir) / "setting"
    setting.mkdir()
    db_path = setting / "ledplaydb.sqlite"
    import api.database as db_mod

    monkeypatch.setattr(db_mod, "_SCORES_DB", str(db_path))
    db_mod._db = None
    db = db_mod.get_db()
    yield db, db_path
    db_mod._db = None


def test_logout_does_not_record_score(client, monkeypatch, scores_db):
    db, _path = scores_db
    import api.main as main_mod

    monkeypatch.setattr(main_mod, "db", db)
    record_calls = []
    real_record = db.record_game_score

    def spy(info):
        record_calls.append(info)
        return real_record(info)

    monkeypatch.setattr(db, "record_game_score", spy)
    monkeypatch.setattr(
        main_mod.game_manager,
        "stop_game",
        lambda _gid: {"success": True, "state": {"score": 999}},
    )

    before = len(db.get_scores_since("1970-01-01T00:00:00"))
    resp = client.post(
        "/logout",
        json={"card_id": "CARD-A", "game_id": "test-game"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert record_calls == []
    assert len(db.get_scores_since("1970-01-01T00:00:00")) == before


def test_legacy_table_without_life_gets_life_column(monkeypatch, tmp_path):
    setting = tmp_path / "setting"
    setting.mkdir()
    db_path = setting / "ledplaydb.sqlite"
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE hex_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT,
            level TEXT,
            score INTEGER,
            ts TEXT
        )
        """
    )
    con.commit()
    con.close()

    import api.database as db_mod

    monkeypatch.setattr(db_mod, "_SCORES_DB", str(db_path))
    db_mod._db = None
    db = db_mod.get_db()

    info = con = sqlite3.connect(db_path)
    cols = [row[1] for row in info.execute("PRAGMA table_info(hex_scores)")]
    info.close()
    assert "life" in cols

    check = sqlite3.connect(db_path)
    check.execute(
        "INSERT INTO hex_scores (card_id, level, score, life, ts) "
        "VALUES ('LEG', '1', 10, 2, '2020-01-01T00:00:00')"
    )
    check.commit()
    row = check.execute(
        "SELECT life FROM hex_scores WHERE card_id='LEG'"
    ).fetchone()
    check.close()
    assert row[0] == 2
    assert db is not None  # init completed
