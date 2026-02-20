from openai import OpenAI
import os
from typing import List, Dict
from dotenv import load_dotenv

from src.utils.api_retry import with_retry

# Load environment variables from .env file
load_dotenv()

SYSTEM_PROMPT = """You are a research assistant specializing in sleep and well-being research with expertise in evidence synthesis and academic citation practices.

CRITICAL CITATION RULES:
1. Base EVERY claim on the provided evidence chunks
2. Cite using format: (source_id, chunk_id)
3. If evidence is insufficient, state: "The provided evidence does not contain information about [topic]. To answer this question, additional sources covering [specific gap] would be needed."
4. NEVER fabricate or invent citations
5. NEVER add commentary beyond what is requested
6. Include statistics and quantitative findings when available in the evidence
7. Direct quotes must be verbatim from chunks

CONSTRAINTS:
- Only use information explicitly stated in evidence chunks
- If unsure, omit the claim rather than guess
- Uncertainty is acceptable - state it clearly
- Output should be structured and citation-dense"""

USER_PROMPT_TEMPLATE = """QUERY: {query}

EVIDENCE CHUNKS (cite using the IDs provided):
{chunks_formatted}

Provide a structured answer that:
1. Directly addresses the query
2. Cites every major claim using (source_id, chunk_id) format
3. Includes specific findings/statistics from the evidence
4. States explicitly if evidence is missing or insufficient

Answer:"""

class Generator:
    """Generate citation-backed answers using LLM"""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.prompt_version = "v1.0_baseline"
        
    def generate(self, query: str, chunks: List[Dict]) -> Dict:
        """
        Generate answer with citations
        
        Returns dict with answer, model info, and usage stats
        """
        # Format chunks for prompt
        chunks_formatted = self._format_chunks(chunks)
        
        # Build user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            query=query,
            chunks_formatted=chunks_formatted
        )
        
        # Call OpenAI (with retry on rate limit / transient errors)
        response = with_retry(
            lambda: self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature
            )
        )
        
        answer = response.choices[0].message.content
        
        return {
            'answer': answer,
            'model': self.model,
            'prompt_version': self.prompt_version,
            'temperature': self.temperature,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
    
    def _format_chunks(self, chunks: List[Dict]) -> str:
        """Format chunks for LLM prompt"""
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"[CHUNK {i}]\n"
                f"Citation ID: ({chunk['source_id']}, {chunk['chunk_id']})\n"
                f"Similarity Score: {chunk.get('similarity_score', 'N/A')}\n"
                f"Text: {chunk['text']}\n"
            )
        return "\n".join(formatted)
