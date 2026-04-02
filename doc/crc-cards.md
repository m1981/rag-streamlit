
### 2. CRC Cards (Class-Responsibility-Collaborator)

In Python, we often use a mix of Object-Oriented classes and functional modules. I have created CRC cards for our core Classes (including our Dataclasses) and included our functional modules (`database` and `etl_engine`) as they act as Singleton Services in our architecture.

#### Data Models (The "State" Carriers)

| Class Name | `TranscriptModel` (@dataclass) |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Encapsulates a single row from the SQLite `transcripts` table. | • `database.py` (Creates and consumes it) |
| • Holds the raw text, YouTube URL, and processing status. | • `1_Data_Preparation.py` (Instantiates it from UI input) |
| • Provides type-safety and dot-notation access (no raw tuples). | • `etl_engine.py` (Reads it to start processing) |

| Class Name | `TimeChunkModel` (@dataclass) |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Encapsulates a specific time-window (e.g., 60s) of a transcript. | • `TranscriptChunker` (Creates it) |
| • Maintains the exact start time and URL for accurate video linking. | • `etl_engine.py` (Passes it to the LLM) |
| • Holds the raw text and the LLM-generated summary. | |

#### Domain Logic & Orchestration

| Class Name | `TranscriptChunker` |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Parses raw Polish YouTube transcripts using Regex. | • `TimeChunkModel` (Instantiates them) |
| • Strips out noise (e.g., `[Muzyka]`) and fixes shortened URLs. | • `etl_engine.py` (Calls it) |
| • Applies "Smart Boundary" logic: groups lines into chunks, ensuring no chunk exceeds the defined time window (default 60s). | |
| • Handles edge cases (long silences, rapid speech, exact boundaries). | |

| Class Name | `CADVideoRAG` |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Initializes the Anthropic LLM and Voyage AI Embedding models. | • `app.py` (Instantiates and caches it) |
| • Loads the local LlamaIndex Vector Store from disk. | • LlamaIndex Core (VectorStoreIndex) |
| • Configures the Voyage AI Reranker for high-accuracy retrieval. | • Anthropic / Voyage APIs |
| • Executes semantic search queries and formats the output with Markdown video links. | |

#### Functional Modules (Acting as Services)

*Note: Because we used Pythonic CQS, these are implemented as modules with functions rather than instantiated classes, but they fulfill the exact same architectural role as a "Repository" or "Service" class.*

| Module Name | `database.py` (CQS Repository) |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Initializes the SQLite schema (`transcripts` and `app_config` tables). | • `TranscriptModel` (Maps SQL rows to this) |
| • **Commands:** Saves new transcripts, updates statuses, saves new LLM prompts. | • `1_Data_Preparation.py` (Calls commands/queries) |
| • **Queries:** Fetches pending transcripts, fetches the active LLM prompt. | • `etl_engine.py` (Calls commands/queries) |
| • Enforces Business Rule 3: Invalidates processed transcripts when the prompt changes. | • SQLite3 (Standard Library) |

| Module Name | `etl_engine.py` (Phase 1 Orchestrator) |
| :--- | :--- |
| **Responsibilities** | **Collaborators** |
| • Acts as the master Command to run the Phase 1 pipeline. | • `database.py` (Fetches pending, updates status) |
| • Fetches pending transcripts and the active prompt from the database. | • `TranscriptChunker` (Chunks the text) |
| • Passes chunks to Claude 3.5 Haiku for semantic enrichment. | • `TimeChunkModel` (Updates with LLM summary) |
| • Combines raw text, summaries, and metadata into LlamaIndex Documents. | • LlamaIndex Core (Embeds and saves to disk) |
| • Emits progress updates back to the UI via a callback function. | • `1_Data_Preparation.py` (Triggers the pipeline) |
