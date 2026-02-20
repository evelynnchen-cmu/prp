import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict

class VectorStore:
    """FAISS-based vector store for chunk retrieval"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product
        self.chunk_metadata = []  # Store full chunk dicts
        
    def add_chunks(self, chunks: List[Dict], embeddings: np.ndarray):
        """Add chunks and their embeddings to index"""
        assert embeddings.shape[0] == len(chunks)
        assert embeddings.shape[1] == self.dimension
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store metadata
        self.chunk_metadata.extend(chunks)
        
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search for top-k similar chunks
        
        Returns chunks with similarity scores
        """
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        scores, indices = self.index.search(
            query_embedding.astype('float32'), k
        )
        
        # Return chunks with scores
        results = []
        for i, idx in enumerate(indices[0]):
            chunk = self.chunk_metadata[idx].copy()
            chunk['similarity_score'] = float(scores[0][i])
            results.append(chunk)
        
        return results
    
    def save(self, path: str):
        """Save index and metadata to disk"""
        Path(path).mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}/faiss.index")
        
        # Save metadata
        with open(f"{path}/metadata.json", 'w') as f:
            json.dump(self.chunk_metadata, f)
        
        print(f"Saved index with {self.index.ntotal} vectors to {path}")
    
    def load(self, path: str):
        """Load index and metadata from disk"""
        print("Loading vector index from disk (this may take a moment)...", flush=True)
        # Load FAISS index
        self.index = faiss.read_index(f"{path}/faiss.index")
        self.dimension = self.index.d
        
        # Load metadata
        with open(f"{path}/metadata.json", 'r') as f:
            self.chunk_metadata = json.load(f)
        
        print(f"Loaded index with {self.index.ntotal} vectors from {path}")
