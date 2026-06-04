# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: tourist_record_main.py
import os
import shelve
import gui.language as language
from tourist_record.gui_game_result_tourist import GameResult
from tourist_record.tourist_info import Tourist
import subprocess, sqlite3
from datetime import datetime

class TouristRecord:
    PATH_DATA = "./data/local_data.db"
    KEY_TOURIST = "key_tourist"

    # ── game_results schema (rich leaderboard table) ──────────────────────
    _GAME_RESULTS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS game_results (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        played_at       TEXT    NOT NULL,
        game_name       TEXT    NOT NULL,
        level           TEXT,
        player_count    INTEGER,
        players         TEXT,
        duration_min    REAL,
        time_played_sec REAL,
        score           REAL,
        score_p1        REAL,
        score_p2        REAL,
        lives_start     INTEGER,
        lives_left      INTEGER
    );
    """

    def __init__(self):
        return

    def connect(self):
        os.makedirs(os.path.dirname(TouristRecord.PATH_DATA), exist_ok=True)
        self.conn = sqlite3.connect(TouristRecord.PATH_DATA)
        print("数据库打开成功")
        cursor = self.conn.cursor()
        self.cursor = cursor

    def close(self):
        self.cursor.close()
        self.conn.close()

    def get_row_count(self):
        cursor = self.cursor
        table_name = "COMPANY"
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        return row_count

    def delete_table(self):
        sql = "DROP TABLE COMPANY"
        self.cursor.execute(sql)
        self.conn.commit()

    def create_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS COMPANY\n               (NAME           TEXT    NOT NULL,\n               SCODE            REAL     NOT NULL,\n               DATETIME        DATETIME NOT NULL);\n               ")
        self.cursor.executescript(self._GAME_RESULTS_SCHEMA)
        print("数据表创建成功")
        self.conn.commit()

    def add(self, tourist):
        sql = "INSERT INTO COMPANY (NAME, SCODE, DATETIME) VALUES (?, ?, ?)"
        val = (tourist.name, tourist.scode, tourist.date)
        self.cursor.execute(sql, val)
        self.conn.commit()

    def add_game_result(self, game_name, level, player_count, players,
                        duration_min, time_played_sec, score,
                        score_p1=None, score_p2=None,
                        lives_start=None, lives_left=None):
        """Write one rich game result row to the leaderboard table."""
        self.cursor.executescript(self._GAME_RESULTS_SCHEMA)
        self.cursor.execute(
            """INSERT INTO game_results
               (played_at, game_name, level, player_count, players,
                duration_min, time_played_sec, score, score_p1, score_p2,
                lives_start, lives_left)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             game_name, level, player_count, players,
             duration_min, time_played_sec, score, score_p1, score_p2,
             lives_start, lives_left))
        self.conn.commit()

    def get_leaderboard(self, limit=200):
        """Return all game results ordered by score descending."""
        try:
            self.cursor.executescript(self._GAME_RESULTS_SCHEMA)
            self.cursor.execute(
                """SELECT id, played_at, game_name, level, player_count, players,
                          duration_min, time_played_sec, score, score_p1, score_p2,
                          lives_start, lives_left
                   FROM game_results
                   ORDER BY score DESC, played_at DESC
                   LIMIT ?""", (limit,))
            cols = [d[0] for d in self.cursor.description]
            return [dict(zip(cols, row)) for row in self.cursor.fetchall()]
        except Exception:
            return []

    def search(self, limit=1):
        sql = "SELECT NAME,SCODE,DATETIME  FROM COMPANY ORDER BY SCODE DESC, DATETIME DESC LIMIT " + str(limit)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

    def search_rst_datetime(self, limit=1):
        sql = "SELECT NAME,SCODE,DATETIME  FROM COMPANY ORDER BY DATETIME DESC LIMIT " + str(limit)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

    def dispaly(self, parent, result=None, title=language.GAME_RESULT, game_time=1, game_player_num=1, cur_scode=0, parent_game_running=None):
        GameResult(parent, result, title, game_time, game_player_num, cur_scode, parent_game_running)
        return

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/tourist_record/tourist_record_main.pyc
