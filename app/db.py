import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    gender TEXT NOT NULL DEFAULT 'unspecified',
    image_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backgrounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    image_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS composites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character1_id INTEGER NOT NULL REFERENCES characters(id),
    character2_id INTEGER NOT NULL REFERENCES characters(id),
    background_id INTEGER NOT NULL REFERENCES backgrounds(id),
    image_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(character1_id, character2_id, background_id)
);

CREATE TABLE IF NOT EXISTS voices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gender TEXT NOT NULL DEFAULT 'unspecified',
    reference_audio_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dialogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    character1_id INTEGER NOT NULL REFERENCES characters(id),
    character2_id INTEGER NOT NULL REFERENCES characters(id),
    line1 TEXT NOT NULL,
    line2 TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS voice_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    voice_id INTEGER NOT NULL REFERENCES voices(id),
    audio_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(text, voice_id)
);

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composite_id INTEGER NOT NULL REFERENCES composites(id),
    dialogue_id INTEGER NOT NULL REFERENCES dialogues(id),
    voice_line1_id INTEGER NOT NULL REFERENCES voice_lines(id),
    voice_line2_id INTEGER NOT NULL REFERENCES voice_lines(id),
    duration_sec INTEGER NOT NULL DEFAULT 20,
    video_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]


# ---------- characters ----------

def create_character(name: str, description: str, gender: str, image_path: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO characters (name, description, gender, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, description, gender, image_path, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM characters WHERE id = ?", (cur.lastrowid,)).fetchone())


def list_characters() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM characters ORDER BY id DESC").fetchall())


def get_character(character_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone())


def delete_character(character_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))


# ---------- backgrounds ----------

def create_background(name: str, description: str, image_path: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO backgrounds (name, description, image_path, created_at) VALUES (?, ?, ?, ?)",
            (name, description, image_path, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM backgrounds WHERE id = ?", (cur.lastrowid,)).fetchone())


def list_backgrounds() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM backgrounds ORDER BY id DESC").fetchall())


def get_background(background_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM backgrounds WHERE id = ?", (background_id,)).fetchone())


def delete_background(background_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM backgrounds WHERE id = ?", (background_id,))


# ---------- composites ----------

def find_composite(character1_id: int, character2_id: int, background_id: int) -> dict | None:
    """Match the character pair regardless of which slot each one is in, so swapping who is
    인물1 vs 인물2 still finds a composite already registered with the pair in the other order."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM composites WHERE background_id = ? AND "
            "((character1_id = ? AND character2_id = ?) OR (character1_id = ? AND character2_id = ?))",
            (background_id, character1_id, character2_id, character2_id, character1_id),
        ).fetchone()
        return row_to_dict(row)


def create_composite(character1_id: int, character2_id: int, background_id: int, image_path: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO composites (character1_id, character2_id, background_id, image_path, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (character1_id, character2_id, background_id, image_path, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM composites WHERE id = ?", (cur.lastrowid,)).fetchone())


def list_composites() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM composites ORDER BY id DESC").fetchall())


def get_composite(composite_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM composites WHERE id = ?", (composite_id,)).fetchone())


# ---------- voices ----------

def create_voice(name: str, gender: str, reference_audio_path: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO voices (name, gender, reference_audio_path, created_at) VALUES (?, ?, ?, ?)",
            (name, gender, reference_audio_path, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM voices WHERE id = ?", (cur.lastrowid,)).fetchone())


def list_voices() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM voices ORDER BY id DESC").fetchall())


def get_voice(voice_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM voices WHERE id = ?", (voice_id,)).fetchone())


def delete_voice(voice_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM voices WHERE id = ?", (voice_id,))


# ---------- dialogues ----------

def create_dialogue(keyword: str, character1_id: int, character2_id: int, line1: str, line2: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO dialogues (keyword, character1_id, character2_id, line1, line2, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (keyword, character1_id, character2_id, line1, line2, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM dialogues WHERE id = ?", (cur.lastrowid,)).fetchone())


def update_dialogue_lines(dialogue_id: int, line1: str, line2: str) -> dict | None:
    with get_conn() as conn:
        conn.execute("UPDATE dialogues SET line1 = ?, line2 = ? WHERE id = ?", (line1, line2, dialogue_id))
        return row_to_dict(conn.execute("SELECT * FROM dialogues WHERE id = ?", (dialogue_id,)).fetchone())


def get_dialogue(dialogue_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM dialogues WHERE id = ?", (dialogue_id,)).fetchone())


def list_dialogues() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM dialogues ORDER BY id DESC").fetchall())


# ---------- voice_lines ----------

def find_voice_line(text: str, voice_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM voice_lines WHERE text = ? AND voice_id = ?", (text, voice_id)
        ).fetchone()
        return row_to_dict(row)


def create_voice_line(text: str, voice_id: int, audio_path: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO voice_lines (text, voice_id, audio_path, created_at) VALUES (?, ?, ?, ?)",
            (text, voice_id, audio_path, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM voice_lines WHERE id = ?", (cur.lastrowid,)).fetchone())


def get_voice_line(voice_line_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM voice_lines WHERE id = ?", (voice_line_id,)).fetchone())


# ---------- videos ----------

def create_video(composite_id: int, dialogue_id: int, voice_line1_id: int, voice_line2_id: int,
                  duration_sec: int) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO videos (composite_id, dialogue_id, voice_line1_id, voice_line2_id, duration_sec, "
            "status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (composite_id, dialogue_id, voice_line1_id, voice_line2_id, duration_sec, now_iso()),
        )
        return row_to_dict(conn.execute("SELECT * FROM videos WHERE id = ?", (cur.lastrowid,)).fetchone())


def update_video_status(video_id: int, status: str, video_path: str | None = None,
                         error_message: str | None = None) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE videos SET status = ?, video_path = COALESCE(?, video_path), error_message = ? WHERE id = ?",
            (status, video_path, error_message, video_id),
        )
        return row_to_dict(conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone())


def get_video(video_id: int) -> dict | None:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone())


def list_videos() -> list[dict]:
    with get_conn() as conn:
        return rows_to_list(conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall())
