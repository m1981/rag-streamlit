import os
from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.voyageai import VoyageEmbedding
from core import database as db
from core.chunker import TranscriptChunker

INDEX_DIR = os.environ.get("INDEX_DIR", "./cad_video_index")


def run_indexing_pipeline(progress_callback=None) -> None:
    """COMMAND: Processes all pending transcripts and updates the Vector Store."""

    pending_transcripts = db.get_pending_transcripts()
    if not pending_transcripts:
        return

    # 1. Setup AI Clients
    llm = Anthropic(
        model="claude-3-5-haiku-20241022", api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    Settings.embed_model = VoyageEmbedding(
        model_name="voyage-3", voyage_api_key=os.environ.get("VOYAGE_API_KEY")
    )

    chunker = TranscriptChunker(window_seconds=60)
    active_prompt = db.get_active_prompt()

    # 2. Load or Create Index
    if os.path.exists(INDEX_DIR):
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        index = load_index_from_storage(storage_context)
    else:
        index = VectorStoreIndex([])

    # 3. Process each transcript
    for i, transcript in enumerate(pending_transcripts):
        if progress_callback:
            progress_callback(i, len(pending_transcripts), transcript.title)

        chunks = chunker.process_raw_text(transcript.raw_text)
        documents = []

        for chunk in chunks:
            # Ask Claude to summarize
            full_prompt = f"{active_prompt}\n\nSurowy transkrypt:\n{chunk.chunk_text}"
            response = llm.complete(full_prompt)
            chunk.llm_summary = str(response)

            # Create LlamaIndex Document
            doc = Document(
                text=f"Podsumowanie: {chunk.llm_summary}\n\nOryginalny tekst: {chunk.chunk_text}",
                metadata={
                    "video_title": transcript.title,
                    "start_time": chunk.start_time_str,
                    "video_url": chunk.url,
                },
            )
            documents.append(doc)

        # Insert into Vector Store
        for doc in documents:
            index.insert(doc)

        # Mark as processed in SQLite
        db.update_transcript_status(transcript.id, "processed")

    # 4. Persist Vector Store to disk
    index.storage_context.persist(persist_dir=INDEX_DIR)
