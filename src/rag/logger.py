import json
from datetime import datetime
from pathlib import Path
from typing import Dict
import re

class QueryLogger:
    """Log RAG queries and results"""
    
    def __init__(self, log_path: str = "logs/query_logs.jsonl"):
        self.log_path = log_path
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
    def log(self, result: Dict):
        """Log a query result"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'query': result['query'],
            'answer': result['answer'],
            'model': result['model'],
            'prompt_version': result['prompt_version'],
            'retrieved_chunks': [
                {
                    'chunk_id': c['chunk_id'],
                    'source_id': c['source_id'],
                    'similarity_score': c.get('similarity_score'),
                    'text': c['text'] 
                }
                for c in result['retrieved_chunks']
            ],
            'citations_found': self._extract_citations(result['answer']),
            'metadata': result['metadata']
        }
        
        # Append to log file
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _extract_citations(self, text: str) -> list:
        """Extract all (source_id, chunk_id) citations from text"""
        pattern = r'\(([a-z0-9_]+),\s*([a-z0-9_]+)\)'
        matches = re.findall(pattern, text)
        return [f"({m[0]}, {m[1]})" for m in matches]
