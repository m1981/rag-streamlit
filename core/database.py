import sqlite3
from dataclasses import dataclass
from typing import List, Optional


# ==========================================
# 1. DATA MODELS
# ==========================================

@dataclass
class TranscriptModel:
    title: str
    url: str
    raw_text: str
    status: str = 'unprocessed'  # 'unprocessed', 'processed', 'outdated'
    id: Optional[int] = None


# ==========================================
# 2. DATABASE CONFIGURATION & INIT
# ==========================================

DB_FILE = "phase1_data.db"


def init_db():
    """
    Creates the database file and tables if they don't exist.
    Run this once when your Streamlit app starts.
    """
    # Using 'with' automatically commits the transaction
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Table 1: Transcripts
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS transcripts
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           title
                           TEXT
                           NOT
                           NULL,
                           url
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           raw_text
                           TEXT
                           NOT
                           NULL,
                           status
                           TEXT
                           DEFAULT
                           'unprocessed'
                       )
                       ''')

        # Table 2: Configuration (Key-Value store for your LLM Prompt)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS app_config
                       (
                           key
                           TEXT
                           PRIMARY
                           KEY,
                           value
                           TEXT
                       )
                       ''')

        # Insert a default prompt if one doesn't exist
        cursor.execute('''
                       INSERT
                       OR IGNORE INTO app_config (key, value) 
            VALUES ('llm_prompt', 'Napisz krótkie podsumowanie operacji CAD z tego fragmentu.')
                       ''')


# ==========================================
# 3. REPOSITORY FUNCTIONS (For Streamlit & ETL)
# ==========================================

def save_transcript(model: TranscriptModel) -> bool:
    """Saves a new transcript. Returns False if URL already exists."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transcripts (title, url, raw_text, status) VALUES (?, ?, ?, ?)",
                (model.title, model.url, model.raw_text, model.status)
            )
            return True
    except sqlite3.IntegrityError:
        # This catches the UNIQUE(url) constraint violation
        return False


def get_pending_transcripts() -> List[TranscriptModel]:
    """Fetches transcripts that need to be processed by the LLM."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, url, raw_text, status FROM transcripts WHERE status IN ('unprocessed', 'outdated')"
        )

        models = []
        for row in cursor.fetchall():
            models.append(TranscriptModel(
                id=row[0], title=row[1], url=row[2], raw_text=row[3], status=row[4]
            ))
        return models


def update_transcript_status(transcript_id: int, new_status: str):
    """Marks a transcript as 'processed' after successful indexing."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transcripts SET status = ? WHERE id = ?",
            (new_status, transcript_id)
        )


# --- Prompt Management Functions ---

def get_active_prompt() -> str:
    """Retrieves the current LLM instructions."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = 'llm_prompt'")
        result = cursor.fetchone()
        return result[0] if result else ""


def save_new_prompt(new_prompt_text: str):
    """
    Saves the new prompt AND marks all previously processed
    transcripts as 'outdated' so they get re-indexed.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # 1. Update the prompt
        cursor.execute(
            "UPDATE app_config SET value = ? WHERE key = 'llm_prompt'",
            (new_prompt_text,)
        )

        # 2. Invalidate old data (Business Rule 3)
        cursor.execute(
            "UPDATE transcripts SET status = 'outdated' WHERE status = 'processed'"
        )