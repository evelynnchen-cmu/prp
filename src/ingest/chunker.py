import tiktoken
from typing import List, Dict

class TextChunker:
    """Chunk text with sliding window approach"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 128):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def chunk_text(self, text: str, source_id: str) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Returns list of dicts:
        {
            'chunk_id': str,
            'source_id': str,
            'text': str,
            'token_count': int,
            'start_char': int,
            'end_char': int
        }
        """
        tokens = self.tokenizer.encode(text)
        chunks = []
        start = 0
        chunk_num = 1
        
        while start < len(tokens):
            # Get chunk tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Calculate character positions for reference
            start_char = len(self.tokenizer.decode(tokens[:start]))
            end_char = len(self.tokenizer.decode(tokens[:end]))
            
            chunks.append({
                'chunk_id': f"{source_id}_chunk_{chunk_num:03d}",
                'source_id': source_id,
                'text': chunk_text,
                'token_count': len(chunk_tokens),
                'start_char': start_char,
                'end_char': end_char
            })
            
            # Move window forward
            start += self.chunk_size - self.overlap
            chunk_num += 1
        
        return chunks
