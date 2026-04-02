import os
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
    PromptTemplate,
    Settings,
)
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.postprocessor.voyageai_rerank import VoyageAIRerank


class CADVideoRAG:
    def __init__(self, persist_dir: str = "./cad_video_index"):
        Settings.llm = Anthropic(
            model="claude-3-5-haiku-20241022",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        Settings.embed_model = VoyageEmbedding(
            model_name="voyage-3", voyage_api_key=os.environ.get("VOYAGE_API_KEY")
        )

        if not os.path.exists(persist_dir):
            raise FileNotFoundError(
                "Index not found. Please run Phase 1 Data Preparation first."
            )

        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        self.index = load_index_from_storage(storage_context)

        self.reranker = VoyageAIRerank(
            api_key=os.environ.get("VOYAGE_API_KEY"), model="rerank-2.5", top_k=3
        )

        self.qa_prompt = PromptTemplate(
            "Kontekst znajduje się poniżej.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Jesteś asystentem CAD. Odpowiedz na pytanie użytkownika na podstawie kontekstu.\n"
            "KRYTYCZNE: Na końcu odpowiedzi musisz podać link do wideo w formacie Markdown.\n"
            "Format: [Obejrzyj: {video_title} od {start_time}]({video_url})\n"
            "Pytanie: {query_str}\n"
            "Odpowiedź: "
        )

        self.query_engine = self.index.as_query_engine(
            similarity_top_k=10,
            node_postprocessors=[self.reranker],
            text_qa_template=self.qa_prompt,
        )

    def search(self, query: str) -> str:
        """QUERY: Returns the formatted string response."""
        response = self.query_engine.query(query)
        return str(response)
