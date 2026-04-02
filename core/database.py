import sqlite3
import os
from dataclasses import dataclass
from typing import List, Optional

# Configurable for testing (TDD)
DB_FILE = os.environ.get("DB_FILE", "phase1_data.db")


# --- DATA MODELS ---
@dataclass
class TranscriptModel:
    title: str
    url: str
    raw_text: str
    status: str = "unprocessed"
    id: Optional[int] = None


# --- INITIALIZATION ---
def init_db() -> None:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                raw_text TEXT NOT NULL,
                status TEXT DEFAULT 'unprocessed'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config(
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO app_config (key, value)
            VALUES ('llm_prompt', 'Napisz krótkie podsumowanie operacji CAD z tego fragmentu.')
        """)


# --- COMMANDS (Mutate State, Return None/Bool) ---
def save_transcript(model: TranscriptModel) -> bool:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transcripts (title, url, raw_text, status) VALUES (?, ?, ?, ?)",
                (model.title, model.url, model.raw_text, model.status),
            )
            return True
    except sqlite3.IntegrityError:
        return False


def update_transcript_status(transcript_id: int, new_status: str) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transcripts SET status = ? WHERE id = ?",
            (new_status, transcript_id),
        )


def save_new_prompt(new_prompt_text: str) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE app_config SET value = ? WHERE key = 'llm_prompt'",
            (new_prompt_text,),
        )
        cursor.execute(
            "UPDATE transcripts SET status = 'outdated' WHERE status = 'processed'"
        )


# --- QUERIES (Return Data, Zero Side Effects) ---
def get_pending_transcripts() -> List[TranscriptModel]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, url, raw_text, status FROM transcripts WHERE status IN ('unprocessed', 'outdated')"
        )
        return [
            TranscriptModel(id=r[0], title=r[1], url=r[2], raw_text=r[3], status=r[4])
            for r in cursor.fetchall()
        ]


def get_active_prompt() -> str:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'llm_prompt'")
        result = cursor.fetchone()
        return result[0] if result else ""
