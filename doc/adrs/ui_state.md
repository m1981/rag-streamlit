### ADR 011: Streamlit State and Singleton Management
**Status:** Accepted
**Context:** Streamlit's architecture reruns the entire Python script from top to bottom on every user interaction. If not handled correctly, this would cause the app to reload the LlamaIndex from disk and re-initialize the Anthropic/Voyage API clients on every keystroke.
**Decision:** We explicitly manage state using Streamlit's native decorators and dictionaries:
*   **Singletons (`@st.cache_resource`):** Used to instantiate the `CADVideoRAG` engine. This ensures the Vector Index and API clients are loaded into memory exactly once upon app startup.
*   **Ephemeral State (`st.session_state`):** Used to store the chat history (`messages` array) so it survives the top-to-bottom reruns.
**Consequences:**
*   *Positive:* The UI remains highly responsive. The heavy lifting (loading the DB) is bypassed during standard user interactions.
*   *Negative:* If the Knowledge Engineer runs Phase 1 and updates the Vector Index, Phase 2 will not see the new data until the Streamlit cache is explicitly cleared (`st.cache_resource.clear()`) or the server is restarted. *(Note: We implemented this cache-clearing step at the end of the Phase 1 pipeline).*
