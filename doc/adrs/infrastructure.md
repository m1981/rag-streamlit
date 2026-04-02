## ADR 001: Adoption of the "YAGNI" Local AI Stack
**Status:** Accepted
**Context:** We need to build a RAG (Retrieval-Augmented Generation) system for a small dataset (80 CAD tutorial videos, approx. 150k words). Standard enterprise RAG architectures often default to heavy cloud infrastructure (Pinecone, Qdrant, LangChain agents, heavy LLMs like GPT-4).
**Decision:** We will ruthlessly apply the YAGNI (You Aren't Gonna Need It) principle.
*   **Vector DB:** Local LlamaIndex storage (saved to disk) instead of a cloud vector database.
*   **LLM:** Claude 3.5 Haiku (fast, cheap, highly capable of Polish translation/summarization) instead of Opus/GPT-4.
*   **Embeddings/Reranker:** Voyage AI (`voyage-3`, `rerank-2.5`) for high-accuracy semantic matching.
**Consequences:**
*   *Positive:* Zero infrastructure maintenance. The entire app can be zipped and shared. Costs are kept to fractions of a penny per query.
*   *Negative:* If the dataset grows to 10,000+ videos, local memory limits will be hit, requiring a migration to a dedicated Vector DB.

## ADR 007: `uv` for Project and Dependency Management
**Status:** Accepted
**Context:** Python dependency management has historically been fragmented (pip, virtualenv, poetry, pipenv).
**Decision:** We will use `uv` and `pyproject.toml` as the sole package and environment manager.
**Consequences:**
*   *Positive:* Blistering fast dependency resolution. Automatic virtual environment management (`uv run`). Modern, standardized `pyproject.toml` configuration.
*   *Negative:* `uv` is a newer tool (built by Astral), meaning some older developers might be unfamiliar with its commands compared to standard `pip`.
