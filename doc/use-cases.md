### 1. Domain Understanding
**Context:** An internal, iterative data preparation and ETL (Extract, Transform, Load) tool designed to process raw CAD video transcripts into an LLM-enriched vector database.
**Core Value Proposition:** Enables the Knowledge Engineer to incrementally ingest data, rapidly iterate on LLM summarization prompts, and validate data quality in small batches before executing a full-scale, paid API processing run on the entire 80-video dataset.

### 2. Domain Glossary
| Term | Definition |
| :--- | :--- |
| **Source Transcript** | The raw text, timestamps, and associated metadata (URL, Subject) for a single CAD tutorial video. |
| **Enrichment Prompt** | The specific set of instructions sent to the LLM (Claude) dictating how to summarize a transcript chunk. |
| **Time Chunk** | A segmented portion of a Source Transcript grouped by a specific time window (e.g., 60 seconds) rather than token count. |
| **Vector Index** | The local database (LlamaIndex/Chroma) storing the embedded, enriched chunks for use in Phase 2. |
| **Knowledge Engineer** | The primary actor (you) responsible for curating the data and tuning the system. |

### 3. Business Rules and Constraints
*   **BR-1 (Time-Bound Chunking):** Transcripts must be segmented into Time Chunks to preserve the chronological context of the video tutorial.
*   **BR-2 (Idempotent Processing):** The indexing pipeline must track which Source Transcripts have been successfully processed. It must skip previously processed transcripts unless a forced re-index is explicitly requested.
*   **BR-3 (Prompt Dependency):** If the Enrichment Prompt is modified, previously processed Source Transcripts must be flagged for re-processing to ensure semantic consistency across the Vector Index.

### 4. Scope Definition (In/Out List)
| Topic | In | Out |
| :--- | :--- | :--- |
| Manual entry of transcript text and metadata | X | |
| Local storage of raw transcripts (SQLite/File System) | X | |
| Configuration of the LLM Enrichment Prompt | X | |
| Execution of the ETL/Indexing pipeline | X | |
| Semantic searching and video playback | | X (Handled in Phase 2) |
| Automated web scraping of YouTube transcripts | | X |

### 5. Fully Dressed Use Cases

**Use Case 1: Manage Source Transcript**
*   **Primary Actor:** Knowledge Engineer
*   **Scope:** Phase 1 Data Preparation Tool
*   **Level:** User Goal
*   **Stakeholders & Interests:**
    *   *Knowledge Engineer:* Wants to easily input and organize raw tutorial data for future processing.
*   **Preconditions:** System has access to the local storage directory/database.
*   **Minimal Guarantees:** System rejects malformed data without corrupting existing records.
*   **Success Guarantees:** The Source Transcript and its metadata are securely saved to local storage and marked as "Unprocessed".
*   **Trigger:** Knowledge Engineer requests to add a new tutorial transcript.

**Main Success Scenario (MSS):**
1. Knowledge Engineer provides the raw transcript text, tutorial subject, and video URL.
2. System validates the URL format and ensures the transcript text contains parseable timestamps.
3. System saves the Source Transcript to local storage.
4. System confirms successful storage to the Knowledge Engineer.

**Extensions:**
*   **2a. Invalid Timestamp Format:**
    *   2a1. System detects the transcript lacks recognizable time markers.
    *   2a2. System alerts the Knowledge Engineer of the formatting error.
    *   2a3. Use case ends in failure.
*   **2b. Duplicate URL:**
    *   2b1. System detects the provided URL already exists in local storage.
    *   2b2. System prompts Knowledge Engineer to overwrite or cancel.
    *   2b3. Knowledge Engineer chooses to overwrite.
    *   2b4. System updates the existing record and returns to MSS step 4.

**Technology and Data Variations:**
*   **Step 3:** Local storage can be implemented via a local SQLite database or structured JSON files within a designated dataset folder.


**Use Case 2: Configure Enrichment Prompt**
*   **Primary Actor:** Knowledge Engineer
*   **Scope:** Phase 1 Data Preparation Tool
*   **Level:** User Goal
*   **Stakeholders & Interests:**
    *   *Knowledge Engineer:* Wants to refine how the LLM interprets the CAD instructions to improve Phase 2 search accuracy.
*   **Preconditions:** None.
*   **Minimal Guarantees:** Previous prompt remains active if the new prompt fails to save.
*   **Success Guarantees:** The new Enrichment Prompt is saved and set as the active instruction set for future indexing runs.
*   **Trigger:** Knowledge Engineer requests to update the LLM instructions.

**Main Success Scenario (MSS):**
1. System presents the currently active Enrichment Prompt.
2. Knowledge Engineer provides the updated Enrichment Prompt text.
3. System saves the new Enrichment Prompt.
4. System flags all previously processed Source Transcripts as "Outdated" based on *BR-3*.
5. System confirms the update.

**Extensions:**
*   **2a. Empty Prompt:**
    *   2a1. System detects the provided prompt is blank.
    *   2a2. System rejects the update and alerts the Knowledge Engineer.
    *   2a3. Use case ends in failure.


**Use Case 3: Execute Indexing Pipeline**
*   **Primary Actor:** Knowledge Engineer
*   **Scope:** Phase 1 Data Preparation Tool
*   **Level:** User Goal
*   **Stakeholders & Interests:**
    *   *Knowledge Engineer:* Wants to transform raw transcripts into searchable vector data without paying to re-process already completed files.
*   **Preconditions:** At least one Source Transcript exists in local storage. Active API keys for LLM and Embedding services are configured.
*   **Minimal Guarantees:** System saves progress after every successfully processed Source Transcript. A failure on file $N$ does not corrupt files $1$ through $N-1$.
*   **Success Guarantees:** All eligible Source Transcripts are chunked, enriched, embedded, and saved to the Vector Index.
*   **Trigger:** Knowledge Engineer requests to run the indexing process.

**Main Success Scenario (MSS):**
1. System identifies all Source Transcripts marked as "Unprocessed" or "Outdated" (*BR-2*).
2. System segments a Source Transcript into Time Chunks based on *BR-1*.
3. System enriches each Time Chunk using the active Enrichment Prompt via the external LLM service.
4. System generates vector embeddings for the enriched chunks via the external Embedding service.
5. System appends the embedded chunks to the Vector Index.
6. System marks the Source Transcript as "Processed".
7. System and Knowledge Engineer repeat steps 2-6 until all identified transcripts are processed.
8. System presents a summary report of the indexing run.

**Extensions:**
*   **1a. No Eligible Transcripts:**
    *   1a1. System detects all transcripts are already marked "Processed".
    *   1a2. System informs the Knowledge Engineer that the index is up to date.
    *   1a3. Use case ends in success.
*   **3a. LLM Service Timeout / Rate Limit:**
    *   3a1. System detects a failure from the external LLM service.
    *   3a2. System applies exponential backoff and retries the request.
    *   3a3. System successfully receives the response and returns to MSS step 4.
*   **3b. LLM Service Persistent Failure:**
    *   3b1. System exhausts retry attempts for the LLM service.
    *   3b2. System halts the pipeline.
    *   3b3. System alerts the Knowledge Engineer of the specific failure point.
    *   3b4. Use case ends in failure (progress up to this point is retained per Minimal Guarantees).

**Technology and Data Variations:**
*   **Step 5:** The Vector Index can be persisted to disk using LlamaIndex's default local storage context or a local ChromaDB instance.
