from .embedder import Embedder
from .vector_store import VectorStore
from typing import List, Dict

class Retriever:
    """Retrieve relevant chunks for queries"""
    
    def __init__(self, index_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.embedder = Embedder(model_name=model_name)
        self.store = VectorStore()
        print("Loading vector index...", flush=True)
        self.store.load(index_path)
        
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve top-k chunks for query
        
        Returns chunks sorted by similarity
        """
        # Embed query
        query_embedding = self.embedder.model.encode(
            [query],
            normalize_embeddings=True
        )
        
        # Search
        results = self.store.search(query_embedding, k=k)
        
        return results
