from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict

class Embedder:
    """Generate embeddings for text chunks"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(f"sentence-transformers/{model_name}")
        self.dimension = self.model.get_sentence_embedding_dimension()
        
    def embed_chunks(self, chunks: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for all chunks
        
        Returns: (N, dimension) numpy array
        """
        texts = [chunk['text'] for chunk in chunks]
        
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True  # For cosine similarity
        )
        
        return embeddings
