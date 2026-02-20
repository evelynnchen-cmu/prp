"""
Shared app utilities: manifest, run_query, save/load threads.
All paths are relative to repo root (where Streamlit is run).
"""
import json
import re
import uuid
from pathlib import Path
from typing import Any

# Repo root: parent of src/ (sibling of src/, data/, logs/, etc.)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MANIFEST_PATH = _REPO_ROOT / "data" / "data_manifest.json"
DEFAULT_INDEX_PATH = str(_REPO_ROOT / "data" / "processed" / "vector_index")
DEFAULT_THREADS_PATH = _REPO_ROOT / "threads" / "threads.jsonl"
# Single outputs dir at repo root (sibling of src/)
OUTPUTS_DIR = _REPO_ROOT / "outputs"
ARTIFACTS_DIR = _REPO_ROOT / "outputs" / "artifacts"


def load_manifest(manifest_path: Path | str | None = None) -> dict[str, Any]:
    """
    Load data manifest as a dict keyed by source id for fast lookups.
    Returns {} if file is missing; raises with clear message on read error.
    """
    path = Path(manifest_path) if manifest_path else DEFAULT_MANIFEST_PATH
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to load manifest from {path}: {e}") from e
    if not isinstance(data, list):
        return {}
    return {item["id"]: item for item in data if isinstance(item, dict) and "id" in item}


def _extract_citations(text: str) -> list[str]:
    """Extract (source_id, chunk_id) citations from answer text."""
    pattern = r"\(([a-z0-9_]+),\s*([a-z0-9_]+)\)"
    matches = re.findall(pattern, text)
    return [f"({m[0]}, {m[1]})" for m in matches]


def run_query(query: str, enhanced: bool = True) -> dict[str, Any]:
    """
    Run RAG query with Phase 2 pipeline (enhanced=True by default).
    Returns a single dict for the UI: answer, chunks, citations, reference_list,
    citation_validation_passed, query, num_unique_sources, etc.
    """
    from src.rag.pipeline import RAGPipeline

    pipeline = RAGPipeline(
        index_path=DEFAULT_INDEX_PATH,
        manifest_path=str(DEFAULT_MANIFEST_PATH),
    )
    result = pipeline.query(query, k=5, log=True, enhance=enhanced)

    chunks = result.get("retrieved_chunks", [])
    answer = result.get("answer", "")
    citations = _extract_citations(answer)

    out = {
        "query": result.get("query", query),
        "answer": answer,
        "chunks": chunks,
        "citations": citations,
        "reference_list": result.get("reference_list", ""),
        "citation_validation_passed": result.get("citation_validation_passed", True),
        "num_unique_sources": result.get("num_unique_sources", 0),
        "invalid_citations": result.get("invalid_citations", []),
    }
    return out


def save_thread(
    query: str,
    chunks: list[dict],
    answer: str,
    citations: list[str] | None = None,
    reference_list: str | None = None,
    threads_path: Path | str | None = None,
) -> str:
    """
    Append one thread record to threads/threads.jsonl (creates file/dir if needed).
    Returns the generated thread_id.
    """
    path = Path(threads_path) if threads_path else DEFAULT_THREADS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    # Keep chunk payload reasonable: required fields only
    chunk_records = [
        {
            "chunk_id": c.get("chunk_id"),
            "source_id": c.get("source_id"),
            "text": (c.get("text") or "")[:2000],
            "similarity_score": c.get("similarity_score"),
        }
        for c in chunks
    ]

    import time
    ts = time.time()
    thread_id = f"{int(ts * 1000)}_{uuid.uuid4().hex[:8]}"

    record = {
        "thread_id": thread_id,
        "timestamp": ts,
        "query": query,
        "answer": answer,
        "chunks": chunk_records,
        "citations": citations or [],
        "reference_list": reference_list or "",
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return thread_id


def load_threads(threads_path: Path | str | None = None) -> list[dict[str, Any]]:
    """
    Read all threads from threads/threads.jsonl, newest first.
    Returns [] if file is missing or empty.
    """
    path = Path(threads_path) if threads_path else DEFAULT_THREADS_PATH
    if not path.exists():
        return []
    threads = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                threads.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    threads.sort(key=lambda t: t.get("timestamp", 0), reverse=True)
    return threads
