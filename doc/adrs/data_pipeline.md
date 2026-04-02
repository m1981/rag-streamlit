## ADR 006: Time-Based "Smart Boundary" Chunking
**Status:** Accepted
**Context:** Standard RAG pipelines use Token-based chunking. However, our data is video transcripts where timestamps are critical. Furthermore, our initial "Greedy" time-chunking algorithm absorbed lines across long silences, destroying chronological accuracy.
**Decision:** We reject Token-based chunking. We implemented a custom `TranscriptChunker` using Regex to parse Polish YouTube transcripts. Through TDD, we refined this to a "Smart Boundary" algorithm: the system checks if a new line exceeds the 60-second window *before* appending it, ensuring long silences trigger a clean split.
**Consequences:**
*   *Positive:* Guarantees that the LLM summary perfectly aligns with the video timeline, allowing the Phase 2 UI to generate accurate `?t=XX` YouTube links.
*   *Negative:* Requires custom Regex parsing logic that must be updated if the source transcript format changes (e.g., moving from `.srt` to `.vtt`).

### ADR 009: LLM-Driven Data Enrichment in ETL
**Status:** Accepted
**Context:** Raw auto-generated YouTube transcripts (especially for visual CAD tutorials) lack semantic context. A transcript might say "Now click here and drag," which is useless for a vector search engine looking for "How to extrude a cylinder."
**Decision:** Instead of embedding the raw transcript text directly, we use an LLM (Claude 3.5 Haiku) *during the ETL phase* to act as a data transformer. The LLM reads the messy, unpunctuated Polish transcript and generates a clean, keyword-rich summary of the visual actions taking place. We embed this summary alongside the raw text.
**Consequences:**
*   *Positive:* Drastically improves semantic search accuracy. Solves the "missing visual context" problem inherent in video transcripts.
*   *Negative:* Adds a dependency on an external LLM API during the data preparation phase and increases the time required to index a new video.

### ADR 010: Idempotent Processing and Prompt-Based Cache Invalidation
**Status:** Accepted
**Context:** The Knowledge Engineer will work iteratively, tweaking the LLM Enrichment Prompt to get better summaries. If the pipeline crashes, or if the prompt changes, we need a safe way to re-run the ETL process without duplicating data or paying for unnecessary API calls.
**Decision:** We implemented an idempotent ETL pipeline using SQLite state tracking (`unprocessed`, `processed`, `outdated`).
*   **Rule 1:** The pipeline skips `processed` transcripts.
*   **Rule 2:** If the Knowledge Engineer updates the LLM Enrichment Prompt, the system automatically executes a cascade update, marking all `processed` transcripts as `outdated`.
**Consequences:**
*   *Positive:* Guarantees that the entire Vector Index is semantically consistent with the *current* active prompt. Prevents API cost overruns by safely resuming interrupted indexing runs.
*   *Negative:* Changing a single comma in the prompt will force a complete re-indexing of all 80 videos, which takes time and consumes API credits.

### ADR 012: Regex-Based Data Cleansing
**Status:** Accepted
**Context:** The raw input data contains YouTube-specific artifacts (e.g., shortened `.be` URLs, `[Muzyka]` tags) and lacks standard punctuation.
**Decision:** We implemented a custom Regex parser inside the `TranscriptChunker` to strip noise tags, reconstruct full `https://youtu.be/` URLs, and extract integer seconds for mathematical time-chunking.
**Consequences:**
*   *Positive:* Ensures clean data enters the LLM, saving tokens and reducing hallucinations.
*   *Negative:* The Regex pattern `\[(\d{2}:\d{2})\]\((.*?)\)\s*(.*)` is tightly coupled to the specific copy-paste format of the current transcript source. If the source format changes, the parser will fail silently (ignoring lines) and require a code update.
