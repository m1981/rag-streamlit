## ADR 002: "Clean-Lite" Architecture for Streamlit
**Status:** Accepted
**Context:** Streamlit's top-to-bottom execution model makes rapid UI development easy but often leads to "spaghetti code" where database calls, LLM initialization, and UI rendering are mixed. This makes testing impossible and causes performance issues (e.g., reloading the LLM on every keystroke).
**Decision:** We will use a "Clean-Lite" architecture. The system is strictly divided into a Presentation Layer (`app.py`, `pages/`) and a Domain Layer (`core/`). The Domain Layer contains zero Streamlit code. Streamlit will use `@st.cache_resource` to hold Domain engine instances in memory.
**Consequences:**
*   *Positive:* The core logic is highly testable via standard `pytest`. If we ever migrate away from Streamlit to FastAPI/React, the `core/` folder remains 100% unchanged.
*   *Negative:* Requires slightly more boilerplate than a standard single-file Streamlit script.

## ADR 005: Command Query Separation (CQS) for Integration Testing
**Status:** Accepted
**Context:** Integration tests involving real databases and vector stores are notoriously flaky if assertions accidentally mutate state.
**Decision:** We will strictly enforce the CQS pattern at the function level in the `core/` layer. A function is either a Command (mutates state, returns None/Bool) or a Query (returns data, zero side effects).
**Consequences:**
*   *Positive:* Enables clean AAA (Arrange, Act, Assert) testing. We can run integration tests against temporary SQLite files and Vector directories without needing complex `MagicMock` setups.
*   *Negative:* Developers must be disciplined not to mix reads and writes in the same function (e.g., no "get_and_update" functions).

## ADR 008: Two-Phase System Architecture (Offline ETL vs. Real-time RAG)
**Status:** Accepted
**Context:** We need to process raw video transcripts and serve them to users via a chat interface. Doing both simultaneously (e.g., fetching a video, summarizing it, and searching it at runtime) would result in massive latency and high API costs per user query.
**Decision:** We split the system into two strictly separated lifecycles:
*   **Phase 1 (Offline ETL):** A Knowledge Engineer uses a control panel to ingest, chunk, enrich, and embed the data into a static Vector Index.
*   **Phase 2 (Online RAG):** The end-user chat interface only reads from the pre-computed Vector Index.
**Consequences:**
*   *Positive:* Phase 2 search is lightning fast (only limited by the LLM generation time). API costs for Anthropic are incurred only once during Phase 1, rather than on every user search.
*   *Negative:* The search index is not real-time. If a new video is added, it cannot be searched until the Knowledge Engineer manually runs the Phase 1 pipeline.
