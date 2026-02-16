from .retriever import Retriever
from .generator import Generator
from .logger import QueryLogger
from typing import Dict

class RAGPipeline:
    """Complete RAG pipeline"""
    
    def __init__(
        self,
        index_path: str = "data/processed/vector_index",
        model: str = "gpt-4o-mini",
        manifest_path: str = "data/data_manifest.json"
    ):
        self.retriever = Retriever(index_path)
        self.generator = Generator(model=model)
        self.logger = QueryLogger()
        try:
            from .structured_citations import StructuredCitationGenerator
            self.citation_enhancer = StructuredCitationGenerator(manifest_path)
        except:
            self.citation_enhancer = None
        
    def query(self, query: str, k: int = 5, log: bool = True, enhance: bool = False) -> Dict:
        """
        Process query through RAG pipeline
        
        Args:
            query: User query
            k: Number of chunks to retrieve
            log: Whether to log the query
            enhance: Whether to apply structured citations enhancement
        
        Returns complete result dict
        """
        # Retrieve chunks
        chunks = self.retriever.retrieve(query, k=k)
        
        # Generate answer
        generation = self.generator.generate(query, chunks)
        
        result = {
            'query': query,
            'retrieved_chunks': chunks,
            'answer': generation['answer'],
            'model': generation['model'],
            'prompt_version': generation['prompt_version'],
            'metadata': {
                'num_chunks_retrieved': k,
                'retrieval_method': 'dense',
                **generation['usage']
            }
        }
        
        # Apply enhancement if requested
        if enhance and self.citation_enhancer:
            result = self.citation_enhancer.enhance_answer(result)
        
        if log:
            self.logger.log(result)
        
        return result

if __name__ == "__main__":
    # Test pipeline
    pipeline = RAGPipeline()
    result = pipeline.query(
        "What is the relationship between sleep duration and anxiety?",
        k=5
    )
    
    print("QUERY:", result['query'])
    print("\nANSWER:", result['answer'])
    print("\nCHUNKS USED:", len(result['retrieved_chunks']))
