import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.app.utils import load_manifest, load_threads
from src.app.artifact_generator import generate_evidence_table

st.title("History")
st.caption("Browse saved research threads and generate evidence tables from any thread.")

threads = load_threads()
if not threads:
    st.info("No research threads yet. Start by asking a question on the **Search** page.")
    st.stop()

manifest = load_manifest()
for thread in threads:
    ts = thread.get("timestamp", 0)
    try:
        time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "—"
    except (OSError, ValueError):
        time_str = "—"
    query = thread.get("query", "")
    answer = thread.get("answer", "")
    chunks = thread.get("chunks", [])
    n_sources = len({c.get("source_id") for c in chunks if c.get("source_id")}) or len(chunks)
    preview = (answer[:300] + "...") if len(answer) > 300 else answer

    with st.expander(f"{time_str} — {query[:60]}{'...' if len(query) > 60 else ''} ({n_sources} sources)"):
        st.markdown("**Query:** " + query)
        st.markdown("**Answer:**")
        st.markdown(answer)
        # Citations with resolved source titles
        citations = thread.get("citations", [])
        if citations:
            st.markdown("**Citations:**")
            for cit in citations:
                # Parse (source_id, chunk_id) for title lookup
                sid = cit.strip("()").split(",")[0].strip() if cit else ""
                item = manifest.get(sid) or {}
                title = item.get("title", sid)
                st.caption(f" {cit} → {title}")
        if st.button("Generate Artifact", key=f"gen_{thread.get('thread_id', id(thread))}"):
            rows = generate_evidence_table(
                query,
                answer,
                chunks,
                thread.get("citations", []),
                manifest,
            )
            st.session_state["pending_artifact"] = {"rows": rows, "query": query}
            st.switch_page("pages/3_Artifacts.py")
