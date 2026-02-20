import streamlit as st
import sys
from pathlib import Path

# Ensure repo root on path (pages are in src/app/pages/)
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.app.utils import load_manifest, run_query, save_thread
from src.app.artifact_generator import generate_evidence_table

st.title("Search")
st.caption("Ask a research question and get cited answers.")

# Single-column layout: query input and Search button
query = st.text_input("Ask a research question", placeholder="e.g. What is the relationship between sleep duration and anxiety?")
search_clicked = st.button("Search")

if search_clicked and query.strip():
    with st.status("Running query…", expanded=True) as status:
        try:
            result = run_query(query.strip(), enhanced=True)
            st.session_state["last_result"] = result
            status.update(label="Done.", state="complete")
        except Exception as e:
            st.error(f"Query failed: {e}")
            status.update(label="Error.", state="error")
            st.stop()

# Display answer, sources, references, trust box, save confirmation, and Generate Evidence Table
result = st.session_state.get("last_result")
if result:
    answer = result.get("answer", "")
    chunks = result.get("chunks", [])
    citations = result.get("citations", [])
    reference_list = result.get("reference_list", "")
    query_used = result.get("query", "")

    st.subheader("Answer")
    st.markdown(answer)

    # Always show references/citations (required: every answer has citations)
    st.subheader("References / citations")
    if reference_list.strip():
        st.text(reference_list)
    elif citations:
        st.write("Cited chunks: " + ", ".join(citations))
    else:
        st.caption("No sources cited (no citations in answer and no reference list returned).")

    # Sources: expandable, per-chunk with source_id, chunk_id, snippet, title
    manifest = load_manifest()
    with st.expander("Sources (retrieved chunks)", expanded=False):
        for c in chunks:
            sid = c.get("source_id", "")
            cid = c.get("chunk_id", "")
            text = (c.get("text") or "")[:200]
            if len((c.get("text") or "")) > 200:
                text += "..."
            item = manifest.get(sid) or {}
            title = item.get("title", "—")
            st.markdown(f"**{sid}** · `{cid}` · {title}")
            st.caption(text)
            st.divider()

    # Trust: missing-evidence warning box — only when the answer clearly says
    # the evidence does *not* contain the info (not for mild "additional sources" caveats)
    lower = answer.lower()
    if "the provided evidence does not contain" in lower:
        suggestion = "Consider adding sources that cover this topic."
        for part in answer.split("."):
            if "additional sources" in part.lower():
                suggestion = part.strip() + "."
                break
        st.warning(
            "The corpus does not contain sufficient evidence for this claim. "
            f"Suggested next step: {suggestion}"
        )

    # Save thread and confirmation (after first render of this result we save once)
    save_key = "saved_for_" + str(hash(query_used + answer[:50]))
    if save_key not in st.session_state:
        try:
            save_thread(
                query_used,
                chunks,
                answer,
                citations=citations,
                reference_list=reference_list,
            )
            st.session_state[save_key] = True
        except Exception:
            pass
    if st.session_state.get(save_key):
        st.success("Thread saved.")

    # Generate Evidence Table button -> artifact rows into session state, navigate to Artifacts
    if st.button("Generate Evidence Table"):
        manifest = load_manifest()
        rows = generate_evidence_table(query_used, answer, chunks, citations, manifest)
        st.session_state["pending_artifact"] = {"rows": rows, "query": query_used}
        st.switch_page("pages/3_Artifacts.py")

elif search_clicked and not query.strip():
    st.info("Please enter a question.")
