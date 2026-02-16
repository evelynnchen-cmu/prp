import json
import sys
from pathlib import Path

# Add parent directory to path for imports when run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.rag.embedder import Embedder
    from src.rag.vector_store import VectorStore
else:
    from .embedder import Embedder
    from .vector_store import VectorStore

def load_chunks(chunks_path: str) -> list:
    """Load chunks from JSONL file"""
    chunks = []
    with open(chunks_path, 'r') as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks

def build_index(
    chunks_path: str = "data/processed/chunks.jsonl",
    index_path: str = "data/processed/vector_index",
    model_name: str = "all-MiniLM-L6-v2"
):
    """Build complete vector index"""
    print("Loading chunks...")
    chunks = load_chunks(chunks_path)
    print(f"  Loaded {len(chunks)} chunks")
    
    print("\nGenerating embeddings...")
    embedder = Embedder(model_name=model_name)
    embeddings = embedder.embed_chunks(chunks)
    print(f"  Generated embeddings: {embeddings.shape}")
    
    print("\nBuilding index...")
    store = VectorStore(dimension=embedder.dimension)
    store.add_chunks(chunks, embeddings)
    
    print("\nSaving index...")
    store.save(index_path)
    
    print("\n✓ Index build complete")
    print(f"  Chunks indexed: {len(chunks)}")
    print(f"  Embedding dimension: {embedder.dimension}")
    print(f"  Saved to: {index_path}")

if __name__ == "__main__":
    build_index()
