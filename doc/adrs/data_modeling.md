## ADR 003: SQLite for Phase 1 State Management
**Status:** Accepted
**Context:** Phase 1 (Data Preparation) requires tracking the state of raw transcripts (`unprocessed`, `processed`, `outdated`). We considered using text files (JSON/Markdown) for human readability.
**Decision:** We will use a local SQLite database (`phase1_data.db`) managed via Python's built-in `sqlite3` library, rejecting text files and heavy ORMs (like SQLAlchemy).
**Consequences:**
*   *Positive:* Trivial state management. Updating 80 transcripts to `outdated` when an LLM prompt changes requires one SQL query instead of 80 file I/O operations. Enforces data integrity (e.g., `UNIQUE` constraint on YouTube URLs).
*   *Negative:* The raw data is no longer easily readable in a standard text editor; it requires the Streamlit UI or an SQLite viewer to inspect.

## ADR 004: Python Dataclasses over Strict DTOs
**Status:** Accepted
**Context:** We need to pass data between the SQLite database, the ETL pipeline, and the UI. Enterprise patterns often dictate strict Data Transfer Objects (DTOs) and Entity models.
**Decision:** We reject strict DTOs because there is no network boundary in our local application. We will use Python `@dataclass` (`TranscriptModel`, `TimeChunkModel`) as lightweight data models.
**Consequences:**
*   *Positive:* Eliminates "tuple hell" (e.g., `row[3]`) from SQL queries, providing dot-notation access and type hinting with minimal boilerplate.
*   *Negative:* None for a monolithic local application.
