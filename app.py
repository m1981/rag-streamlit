import streamlit as st
import streamlit as st
from core import database as db
from core.database import TranscriptModel


# 1. Initialize DB on startup
db.init_db()

st.title("🛠️ Phase 1: Data Preparation")

# --- TAB 1: Add New Transcript ---
tab1, tab2, tab3 = st.tabs(["Add Transcript", "Edit Prompt", "Run Indexer"])

with tab1:
    st.subheader("Add New Video")
    with st.form("add_form"):
        title = st.text_input("Tutorial Subject")
        url = st.text_input("YouTube URL")
        raw_text = st.text_area("Raw Transcript Text", height=200)

        if st.form_submit_button("Save to Database"):
            if title and url and raw_text:
                # Create the Data Model
                new_data = TranscriptModel(title=title, url=url, raw_text=raw_text)

                # Save it
                success = db.save_transcript(new_data)

                if success:
                    st.success("Saved successfully!")
                else:
                    st.error("This URL already exists in the database.")
            else:
                st.warning("Please fill out all fields.")

# --- TAB 2: Edit LLM Prompt ---
with tab2:
    st.subheader("LLM Enrichment Prompt")
    current_prompt = db.get_active_prompt()

    new_prompt = st.text_area("Instructions for Claude", value=current_prompt, height=150)

    if st.button("Update Prompt"):
        db.save_new_prompt(new_prompt)
        st.warning(
            "Prompt updated. All previously processed videos are now marked as 'outdated' and will be re-indexed.")

# --- TAB 3: Run Pipeline ---
with tab3:
    st.subheader("ETL Pipeline")
    pending = db.get_pending_transcripts()

    st.write(f"**{len(pending)}** videos waiting to be processed.")

    if st.button("Run Indexing Pipeline") and pending:
        progress_bar = st.progress(0)

        for i, transcript in enumerate(pending):
            st.write(f"Processing: {transcript.title}...")

            # 1. Chunking logic here...
            # 2. LLM logic here...
            # 3. LlamaIndex logic here...

            # 4. Mark as done in DB
            db.update_transcript_status(transcript.id, 'processed')

            # Update UI
            progress_bar.progress((i + 1) / len(pending))

        st.success("Indexing complete!")