"""
Personal Research Portal — Streamlit multi-page app entrypoint.
Uses Phase 2 RAG pipeline, manifest, and eval outputs.
"""
import streamlit as st

# Ensure we can import pipeline from repo root
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.rag.pipeline import RAGPipeline  # noqa: E402

st.set_page_config(
    page_title="Personal Research Portal",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="auto",
)

st.title("Personal Research Portal - Sleep and Well-being Research")
st.markdown(
    "Use the sidebar to navigate: **Search**, **History**, **Artifacts**, and **Evaluation**."
)
st.info(
    "Search: ask research questions and get cited answers. "
    "History: browse saved threads. Artifacts: view and export evidence tables. "
    "Evaluation: view metrics and re-run evaluation."
)
