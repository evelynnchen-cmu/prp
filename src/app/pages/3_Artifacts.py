import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Pages live in src/app/pages/ → 4 parents to get repo root
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.app.utils import load_manifest, load_threads, ARTIFACTS_DIR
from src.app.artifact_generator import generate_evidence_table, export_evidence_table

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

st.title("Artifacts")
st.caption("View and export evidence tables (CSV, Markdown, PDF).")

rows = None
source_label = None

# Task 5.1: Pending artifact from Search or History
if st.session_state.get("pending_artifact"):
    payload = st.session_state["pending_artifact"]
    rows = payload.get("rows", [])
    source_label = payload.get("query", "Current search")
    # Keep in session for export; optionally clear pending so next visit shows thread list
    st.session_state["current_artifact_rows"] = rows

# If no pending, show thread dropdown and generate from selected thread
if rows is None:
    threads = load_threads()
    if not threads:
        st.info("No research threads yet. Run a search and click **Generate Evidence Table**, or ask a question on the Search page first.")
        st.stop()

    st.subheader("Generate from a saved thread")
    options = {f"{t.get('query', '')[:60]}... ({t.get('thread_id', '')[:12]})": t for t in threads}
    choice = st.selectbox("Select a thread", list(options.keys()), key="artifact_thread_choice")
    if choice:
        thread = options[choice]
        manifest = load_manifest()
        rows = generate_evidence_table(
            thread.get("query", ""),
            thread.get("answer", ""),
            thread.get("chunks", []),
            thread.get("citations", []),
            manifest,
        )
        source_label = thread.get("query", "Selected thread")[:50]
        st.session_state["current_artifact_rows"] = rows

# If we still have no rows, show empty state
if not rows:
    st.info("Select a thread above to generate an evidence table, or use Search → Generate Evidence Table.")
    st.stop()

# Task 5.2: Display table and export buttons
st.subheader("Evidence table" + (f": {source_label}..." if source_label else ""))
st.dataframe(rows, use_container_width=True, hide_index=True)

csv_data, csv_name = export_evidence_table(rows, "csv")
md_data, md_name = export_evidence_table(rows, "markdown")
pdf_data, pdf_name = export_evidence_table(rows, "pdf")

def save_to_artifacts_dir(data: str | bytes, base_name: str, ext: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = ARTIFACTS_DIR / f"{base_name}_{ts}{ext}"
    mode = "wb" if isinstance(data, bytes) else "w"
    encoding = None if isinstance(data, bytes) else "utf-8"
    with open(path, mode, encoding=encoding) as f:
        f.write(data)

col1, col2, col3 = st.columns(3)
with col1:
    if st.download_button("Download CSV", data=csv_data, file_name=csv_name, mime="text/csv", key="dl_csv"):
        save_to_artifacts_dir(csv_data, "evidence_table", ".csv")
        st.toast("Saved to outputs/artifacts/")
with col2:
    if st.download_button("Download Markdown", data=md_data, file_name=md_name, mime="text/markdown", key="dl_md"):
        save_to_artifacts_dir(md_data, "evidence_table", ".md")
        st.toast("Saved to outputs/artifacts/")
with col3:
    if st.download_button("Download PDF", data=pdf_data, file_name=pdf_name, mime="application/pdf", key="dl_pdf"):
        save_to_artifacts_dir(pdf_data, "evidence_table", ".pdf")
        st.toast("Saved to outputs/artifacts/")
