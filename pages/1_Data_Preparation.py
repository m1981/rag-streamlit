import streamlit as st
from core import database as db
from core.database import TranscriptModel
from core.etl_engine import run_indexing_pipeline

st.set_page_config(page_title="Data Prep", page_icon="🗄️")
st.title("🗄️ Phase 1: Data Preparation")

tab1, tab2, tab3 = st.tabs(["➕ Add Transcript", "📝 Edit Prompt", "⚙️ Run Indexer"])

# --- TAB 1: ADD ---
with tab1:
    st.subheader("Add New Video")
    with st.form("add_form", clear_on_submit=True):
        title = st.text_input("Tutorial Subject")
        url = st.text_input("YouTube URL")
        raw_text = st.text_area("Raw Transcript Text", height=200)

        if st.form_submit_button("Save to Database"):
            if title and url and raw_text:
                model = TranscriptModel(title=title, url=url, raw_text=raw_text)
                if db.save_transcript(model):
                    st.success("Saved successfully!")
                else:
                    st.error("This URL already exists in the database.")
            else:
                st.warning("Please fill out all fields.")

# --- TAB 2: PROMPT ---
with tab2:
    st.subheader("LLM Enrichment Prompt")
    current_prompt = db.get_active_prompt()
    new_prompt = st.text_area(
        "Instructions for Claude", value=current_prompt, height=150
    )

    if st.button("Update Prompt"):
        db.save_new_prompt(new_prompt)
        st.warning(
            "Prompt updated. Previously processed videos are marked as 'outdated' and will be re-indexed."
        )

# --- TAB 3: ETL PIPELINE ---
with tab3:
    st.subheader("ETL Pipeline")
    pending = db.get_pending_transcripts()

    st.write(f"**{len(pending)}** videos waiting to be processed.")

    if st.button("Run Indexing Pipeline") and pending:
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Callback to update Streamlit UI from the Domain layer
        def update_ui(current, total, title):
            progress = (current) / total
            progress_bar.progress(progress)
            status_text.text(f"Processing ({current + 1}/{total}): {title}")

        with st.spinner("Running ETL Pipeline..."):
            run_indexing_pipeline(progress_callback=update_ui)

        progress_bar.progress(1.0)
        status_text.text("Indexing complete!")
        st.success("All videos processed and added to Vector Store.")

        # Clear Streamlit cache so Phase 2 loads the new data
        st.cache_resource.clear()
