import streamlit as st
from dotenv import load_dotenv
from core.rag_engine import CADVideoRAG
from core import database as db

load_dotenv()
db.init_db()  # Ensure DB exists

st.set_page_config(page_title="CAD Search", page_icon="🔍")


# --- CACHE THE DOMAIN ENGINE ---
@st.cache_resource
def load_engine():
    try:
        return CADVideoRAG()
    except FileNotFoundError:
        return None


rag_engine = load_engine()

st.title("🛠️ CAD Video Assistant")

if not rag_engine:
    st.warning(
        "⚠️ No vector index found. Please go to 'Data Preparation' in the sidebar and run the indexer."
    )
    st.stop()

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Cześć! W czym mogę pomóc w programie CAD?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- EVENT HANDLING ---
if user_query := st.chat_input("np. Jak obrócić kamerę?"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Szukam w materiałach wideo..."):
            answer = rag_engine.search(user_query)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
