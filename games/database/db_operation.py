"""
SQLite-backed drop-in replacement for the original MySQL DBOperation.

The original connected to a remote MySQL server at the physical hardware controller
(192.168.225.50). Here we store everything in a local SQLite file at
./setting/ledplaydb.sqlite so no external database server is required.

All public method signatures are identical to the original.
"""
import os
import sqlite3

_DB_PATH = os.path.join("setting", "ledplaydb.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS custom_info (
    custom_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_num   TEXT,
    name        TEXT,
    public      TEXT,
    time_left   REAL,
    card_id     TEXT,
    server_meta TEXT
);

CREATE TABLE IF NOT EXISTS recharge_record (
    record_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    custom_id  INTEGER,
    money      REAL,
    game_time  REAL,
    date       TEXT
);

CREATE TABLE IF NOT EXISTS custom_comsume (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    custom_id    INTEGER,
    comsume_id   INTEGER,
    member       INTEGER,
    game_time    REAL,
    comsume_time TEXT
);

CREATE TABLE IF NOT EXISTS game_comsume (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    time         TEXT,
    game_time    REAL,
    game_group   INTEGER,
    player_group INTEGER
);

CREATE TABLE IF NOT EXISTS game_group (
    game_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    num           INTEGER,
    player_num    INTEGER,
    game_lever    TEXT,
    member_info   TEXT
);

CREATE TABLE IF NOT EXISTS player_group (
    player_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_num      INTEGER,
    player_info     TEXT
);

CREATE TABLE IF NOT EXISTS part_game_over (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_name   TEXT,
    game_lever  TEXT,
    player_group INTEGER,
    time_use    REAL,
    pass_time   REAL,
    game_scode  TEXT
);

CREATE TABLE IF NOT EXISTS game_player_group (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    game_group   INTEGER,
    game_lever   TEXT,
    time_use     REAL,
    pass_time    REAL,
    player_group INTEGER,
    scode        TEXT
);
"""


def _migrate_custom_info(cursor, conn):
    """
    Production MySQL `custom_info` has two trailing columns after `time_left` (e.g. card id
    and server/sync fields). Game code uses result[0][-3] to read `time_left`, which only
    lines up when there are exactly two columns after time_left in SELECT * order.
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='custom_info'"
    )
    if not cursor.fetchone():
        return
    cursor.execute("PRAGMA table_info(custom_info)")
    cols = {row[1] for row in cursor.fetchall()}
    if "card_id" not in cols:
        cursor.execute("ALTER TABLE custom_info ADD COLUMN card_id TEXT")
    if "server_meta" not in cols:
        cursor.execute("ALTER TABLE custom_info ADD COLUMN server_meta TEXT")
    conn.commit()


class DBOperation:

    # ── connection ────────────────────────────────────────────────────────────

    def __init__(self, ip_address='localhost'):
        os.makedirs("setting", exist_ok=True)
        self.mydb = sqlite3.connect(_DB_PATH, check_same_thread=False)
        self.mydb.row_factory = sqlite3.Row
        self.cursor = self.mydb.cursor()
        self.cursor.executescript(_SCHEMA)
        self.mydb.commit()
        _migrate_custom_info(self.cursor, self.mydb)
        # Expose same table_name attribute the original provided
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.table_name = [r[0] for r in self.cursor.fetchall()]

    def close_db(self):
        try:
            self.cursor.close()
            self.mydb.close()
        except Exception:
            pass

    # ── last insert id ────────────────────────────────────────────────────────

    def select_last_insert_id(self):
        return self.cursor.lastrowid

    # ── generic helpers ───────────────────────────────────────────────────────

    def get_table_name(self):
        return self.table_name

    def get_table_title(self, table):
        self.cursor.execute(f"SELECT * FROM {table} LIMIT 0")
        return [d[0] for d in self.cursor.description]

    def search_from_table(self, table):
        self.cursor.execute(f"SELECT * FROM {table}")
        result = self.cursor.fetchall()
        return [tuple(r) for r in result]

    # ── custom_info ───────────────────────────────────────────────────────────

    def insert_to_table_custom_tb(self, phone, name, rank, time_left, card_id=None,
                                  server_meta=None):
        self.cursor.execute(
            "INSERT INTO custom_info (phone_num, name, public, time_left, card_id, server_meta)"
            " VALUES (?,?,?,?,?,?)",
            (phone, name, rank, time_left, card_id, server_meta))
        self.mydb.commit()
        return self.cursor.rowcount

    def search_custom_tb_by_id(self, custom_id):
        self.cursor.execute("SELECT * FROM custom_info WHERE custom_id=?", (custom_id,))
        return [tuple(r) for r in self.cursor.fetchall()]

    def search_custom_by_phone(self, phone_num):
        self.cursor.execute("SELECT * FROM custom_info WHERE phone_num=?", (phone_num,))
        return [tuple(r) for r in self.cursor.fetchall()]

    def search_custom_by_field(self, field, value):
        self.cursor.execute(f"SELECT * FROM custom_info WHERE {field}=?", (value,))
        return [tuple(r) for r in self.cursor.fetchall()]

    def search_custom_tb_by_id_and_phone(self, custom_id, phone_num):
        self.cursor.execute(
            "SELECT * FROM custom_info WHERE custom_id=? AND phone_num=?",
            (custom_id, phone_num))
        return [tuple(r) for r in self.cursor.fetchall()]

    def update_custom_tb_delete(self, custom_id, phone_num, name, public, time_left):
        self.cursor.execute(
            "UPDATE custom_info SET phone_num=?, name=?, public=?, time_left=? WHERE custom_id=?",
            (phone_num, name, public, time_left, custom_id))
        self.mydb.commit()
        return self.cursor.rowcount

    def update_custom_info_by_id(self, custom_id, phone_num=None, name=None,
                                  public=None, time_left=None):
        parts, vals = [], []
        if phone_num  is not None: parts.append("phone_num=?");  vals.append(phone_num)
        if name       is not None: parts.append("name=?");       vals.append(name)
        if public     is not None: parts.append("public=?");     vals.append(public)
        if time_left  is not None: parts.append("time_left=?");  vals.append(time_left)
        if not parts:
            return 0
        vals.append(custom_id)
        self.cursor.execute(f"UPDATE custom_info SET {', '.join(parts)} WHERE custom_id=?",
                            vals)
        self.mydb.commit()
        return self.cursor.rowcount

    # ── recharge_record ───────────────────────────────────────────────────────

    def search_recharge_tb_by_id(self, custom_id):
        self.cursor.execute("SELECT * FROM recharge_record WHERE custom_id=?", (custom_id,))
        return [tuple(r) for r in self.cursor.fetchall()]

    def insert_to_table_recharge_record(self, custom_id, money, game_time, date):
        self.cursor.execute(
            "INSERT INTO recharge_record (custom_id, money, game_time, date) VALUES (?,?,?,?)",
            (custom_id, money, game_time, date))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── custom_comsume ────────────────────────────────────────────────────────

    def insert_custom_comsume(self, custom_id, game_consume_id, person_num,
                               game_time, consume_time):
        self.cursor.execute(
            "INSERT INTO custom_comsume (custom_id, comsume_id, member, game_time, comsume_time)"
            " VALUES (?,?,?,?,?)",
            (custom_id, game_consume_id, person_num, game_time, consume_time))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── game_comsume ──────────────────────────────────────────────────────────

    def insert_game_comsume(self, consume_start_time, consume_time,
                             game_group_id, player_group_id):
        self.cursor.execute(
            "INSERT INTO game_comsume (time, game_time, game_group, player_group)"
            " VALUES (?,?,?,?)",
            (consume_start_time, consume_time, game_group_id, player_group_id))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── game_group ────────────────────────────────────────────────────────────

    def insert_game_group(self, num, player_num, game_lever, member_info):
        self.cursor.execute(
            "INSERT INTO game_group (num, player_num, game_lever, member_info)"
            " VALUES (?,?,?,?)",
            (num, player_num, game_lever, member_info))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── player_group ──────────────────────────────────────────────────────────

    def insert_player_group(self, player_num, player_info):
        self.cursor.execute(
            "INSERT INTO player_group (player_num, player_info) VALUES (?,?)",
            (player_num, player_info))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── part_game_over ────────────────────────────────────────────────────────

    def insert_part_game_over(self, game_name, game_lever, player_group,
                               time_use, pass_time, game_scode):
        self.cursor.execute(
            "INSERT INTO part_game_over"
            " (game_name, game_lever, player_group, time_use, pass_time, game_scode)"
            " VALUES (?,?,?,?,?,?)",
            (game_name, game_lever, player_group, time_use, pass_time, game_scode))
        self.mydb.commit()
        return self.cursor.rowcount

    # ── game_player_group ─────────────────────────────────────────────────────

    def insert_game_player_group(self, game_group, game_lever, time_use,
                                  pass_time, player_group, game_scode):
        self.cursor.execute(
            "INSERT INTO game_player_group"
            " (game_group, game_lever, time_use, pass_time, player_group, scode)"
            " VALUES (?,?,?,?,?,?)",
            (game_group, game_lever, time_use, pass_time, player_group, game_scode))
        self.mydb.commit()
        return self.cursor.rowcount

    def search_game_result(self):
        self.cursor.execute("""
            SELECT gp.game_lever, gp.time_use, gp.pass_time, gp.scode,
                   p.player_info, g.member_info, gp.player_group
            FROM game_player_group gp
            JOIN player_group p ON gp.player_group = p.player_group_id
            JOIN game_group   g ON gp.game_group   = g.game_group_id
            ORDER BY gp.scode DESC
        """)
        return [tuple(r) for r in self.cursor.fetchall()]

    def search_game_result2(self, num=1):
        self.cursor.execute("""
            SELECT gp.scode, p.player_info
            FROM game_player_group gp
            JOIN player_group p ON gp.player_group = p.player_group_id
            ORDER BY gp.scode DESC
            LIMIT ?
        """, (num,))
        return [tuple(r) for r in self.cursor.fetchall()]

    def search_game_result_order_by_time(self, num=1):
        self.cursor.execute("""
            SELECT gp.scode, gp.pass_time, p.player_info
            FROM game_player_group gp
            JOIN player_group p ON gp.player_group = p.player_group_id
            ORDER BY gp.pass_time DESC
            LIMIT ?
        """, (num,))
        return [tuple(r) for r in self.cursor.fetchall()]
