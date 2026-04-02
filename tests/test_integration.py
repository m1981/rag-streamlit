import pytest
from core import database as db
from core.database import TranscriptModel
from core.chunker import TranscriptChunker


# ==========================================
# 1. TEST ENVIRONMENT SETUP (The Fixture)
# ==========================================


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """
    This fixture runs before EVERY test.
    It redirects the database and vector store to a temporary folder
    so we don't destroy your real Phase 1 data during testing.
    """
    # 1. Redirect SQLite to a temp file
    test_db_path = tmp_path / "test_phase1.db"
    monkeypatch.setattr("core.database.DB_FILE", str(test_db_path))

    # 2. Redirect LlamaIndex to a temp folder
    test_index_path = tmp_path / "test_vector_index"
    monkeypatch.setattr("core.etl_engine.INDEX_DIR", str(test_index_path))

    # 3. Initialize the fresh test database
    db.init_db()

    yield  # The test runs here

    # Teardown happens automatically because `tmp_path` is cleared by pytest.


# ==========================================
# 2. INTEGRATION TESTS
# ==========================================


def test_cqs_prompt_update_invalidates_processed_transcripts():
    """
    Tests Business Rule 3: Changing the prompt must mark processed items as outdated.
    Notice how clean the AAA pattern is because of CQS.
    """
    # --- ARRANGE (Using Commands) ---
    # Insert a transcript that has ALREADY been processed
    db.save_transcript(
        TranscriptModel(
            title="Old Video",
            url="https://youtu.be/123",
            raw_text="[00:00](.be/123?t=0) Test",
            status="processed",
        )
    )

    # Verify our Arrange step worked using a Query
    assert len(db.get_pending_transcripts()) == 0

    # --- ACT (Using a Command) ---
    # We change the prompt. This should trigger the invalidation.
    db.save_new_prompt("Nowe instrukcje dla LLM")

    # --- ASSERT (Using a Query) ---
    # Because get_pending_transcripts is a pure Query, we can call it safely.
    pending = db.get_pending_transcripts()

    assert len(pending) == 1
    assert pending[0].status == "outdated"
    assert pending[0].title == "Old Video"


def test_chunker_and_database_integration():
    """
    Tests that raw text saved to the database is correctly retrieved
    and parsed by the Chunker into 60-second windows using Smart Boundaries.
    """
    # --- ARRANGE (Using Commands) ---
    raw_polish_transcript = """
    [00:14](.be/bkcsR2XFU48?t=14) Witam w przewodniku
    [00:16](.be/bkcsR2XFU48?t=16) Omówię podstawy
    [01:20](.be/bkcsR2XFU48?t=80) Teraz obracamy kamerę
    [01:25](.be/bkcsR2XFU48?t=85) Używając myszki
    """

    db.save_transcript(
        TranscriptModel(
            title="Korpus Tutorial",
            url="https://youtu.be/bkcsR2XFU48",
            raw_text=raw_polish_transcript.strip(),
        )
    )

    # --- ACT ---
    pending = db.get_pending_transcripts()
    transcript_to_process = pending[0]

    chunker = TranscriptChunker(window_seconds=60)
    chunks = chunker.process_raw_text(transcript_to_process.raw_text)

    # --- ASSERT ---
    assert len(chunks) == 2, "Should be split into two chunks"

    # Check Chunk 1 (00:14 to 00:16)
    # It closes BEFORE 01:20 because 01:20 exceeds the 60s window from 00:14
    assert chunks[0].start_time_str == "00:14"
    assert chunks[0].start_seconds == 14
    assert "Witam w przewodniku" in chunks[0].chunk_text
    assert "Omówię podstawy" in chunks[0].chunk_text
    assert (
        "Teraz obracamy kamerę" not in chunks[0].chunk_text
    )  # Ensure it didn't bleed over!

    # Check Chunk 2 (Starts exactly at 01:20)
    assert chunks[1].start_time_str == "01:20"
    assert chunks[1].start_seconds == 80
    assert "Teraz obracamy kamerę" in chunks[1].chunk_text
    assert "Używając myszki" in chunks[1].chunk_text


def test_prevent_duplicate_urls():
    """
    Tests the SQLite UNIQUE constraint on URLs.
    """
    # --- ARRANGE ---
    model1 = TranscriptModel(title="Vid 1", url="https://youtu.be/abc", raw_text="...")
    model2 = TranscriptModel(
        title="Vid 2", url="https://youtu.be/abc", raw_text="..."
    )  # Same URL

    # --- ACT ---
    success1 = db.save_transcript(model1)
    success2 = db.save_transcript(model2)

    # --- ASSERT ---
    assert success1 is True
    assert success2 is False  # Command should gracefully fail and return False

    # Query to ensure only one was saved
    pending = db.get_pending_transcripts()
    assert len(pending) == 1
    assert pending[0].title == "Vid 1"


def test_chunker_long_silence_gap():
    """
    If there is a massive gap between spoken lines, the new line
    should NOT be absorbed into the old chunk. It should start a new one.
    """
    chunker = TranscriptChunker(window_seconds=60)
    raw_text = """
    [00:00](.be/abc?t=0) Krok pierwszy
    [05:00](.be/abc?t=300) Krok drugi po długiej przerwie
    """

    chunks = chunker.process_raw_text(raw_text.strip())

    assert len(chunks) == 2, "Should split into two chunks due to the 5-minute gap"

    # Chunk 1 should ONLY have the 00:00 text
    assert chunks[0].start_time_str == "00:00"
    assert "Krok pierwszy" in chunks[0].chunk_text
    assert "Krok drugi" not in chunks[0].chunk_text  # THIS WILL FAIL CURRENTLY

    # Chunk 2 should start at 05:00
    assert chunks[1].start_time_str == "05:00"
    assert "Krok drugi" in chunks[1].chunk_text


def test_chunker_rapid_fire_speech():
    """
    Multiple lines within the 60-second window should be grouped together.
    """
    chunker = TranscriptChunker(window_seconds=60)
    raw_text = """
    [00:01](.be/abc?t=1) Raz
    [00:15](.be/abc?t=15) Dwa
    [00:30](.be/abc?t=30) Trzy
    [00:45](.be/abc?t=45) Cztery
    [00:59](.be/abc?t=59) Pięć
    """

    chunks = chunker.process_raw_text(raw_text.strip())

    assert len(chunks) == 1, "All lines are under 60s, should be 1 chunk"
    assert chunks[0].start_time_str == "00:01"
    assert "Raz Dwa Trzy Cztery Pięć" in chunks[0].chunk_text


def test_chunker_pure_noise_or_empty():
    """
    If the transcript contains only ignored tags or is empty,
    it should gracefully return an empty list.
    """
    chunker = TranscriptChunker(window_seconds=60)

    # Test 1: Only noise
    noise_text = """
    [00:00](.be/abc?t=0) [Muzyka]
    [00:15](.be/abc?t=15) [Muzyka]
    """
    assert len(chunker.process_raw_text(noise_text.strip())) == 0

    # Test 2: Completely empty
    assert len(chunker.process_raw_text("")) == 0


def test_chunker_exact_boundary_match():
    """
    A line exactly at the window boundary (e.g., 60s delta)
    should start a new chunk.
    """
    chunker = TranscriptChunker(window_seconds=60)
    raw_text = """
    [00:00](.be/abc?t=0) Start
    [01:00](.be/abc?t=60) Dokładnie minuta
    """

    chunks = chunker.process_raw_text(raw_text.strip())

    assert len(chunks) == 2
    assert chunks[0].start_time_str == "00:00"
    assert chunks[1].start_time_str == "01:00"
    assert "Dokładnie minuta" in chunks[1].chunk_text
