import json
import re
import sys
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports if needed
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class EvaluationMetrics:
    """Calculate evaluation metrics"""
    
    def __init__(self, chunks_path: str = "data/processed/chunks.jsonl", use_llm: bool = True):
        self.chunks = self._load_chunks(chunks_path)
        self.chunk_ids = {c['chunk_id'] for c in self.chunks}
        self.use_llm = use_llm
        
        if use_llm:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = OpenAI(api_key=api_key)
        
    def _load_chunks(self, path: str) -> List[Dict]:
        """Load all chunks"""
        chunks = []
        with open(path) as f:
            for line in f:
                chunks.append(json.loads(line))
        return chunks
    
    def citation_precision(self, result: Dict) -> Dict:
        """
        Calculate citation precision
        
        Returns dict with precision score and details
        """
        answer = result['answer']
        retrieved_chunk_ids = {c['chunk_id'] for c in result['retrieved_chunks']}
        
        # Extract citations from answer
        citations = self._extract_citations(answer)
        
        if not citations:
            return {
                'total_citations': 0,
                'valid_citations': 0,
                'precision': 0.0,
                'invalid': []
            }
        
        # Check which citations are valid
        valid = []
        invalid = []
        
        for cit in citations:
            # Parse citation (source_id, chunk_id)
            match = re.search(r'\(([^,]+),\s*([^)]+)\)', cit)
            if match:
                chunk_id = match.group(2).strip()
                if chunk_id in retrieved_chunk_ids:
                    valid.append(cit)
                else:
                    invalid.append(cit)
        
        precision = len(valid) / len(citations) if citations else 0
        
        return {
            'total_citations': len(citations),
            'valid_citations': len(valid),
            'invalid_citations': len(invalid),
            'precision': precision,
            'invalid': invalid
        }
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract (source_id, chunk_id) citations"""
        pattern = r'\(([a-z0-9_]+),\s*([a-z0-9_]+)\)'
        matches = re.findall(pattern, text)
        return [f"({m[0]}, {m[1]})" for m in matches]
    
    def _get_evaluation_prompt(self, result: Dict) -> str:
        """Generate evaluation prompt based on query type"""
        query = result['query']
        answer = result['answer']
        phase1_task = result.get('phase1_task', 'general')
        category = result.get('category', 'direct')
        retrieved_chunks = result['retrieved_chunks']
        
        # Format retrieved chunks for context
        chunks_text = "\n".join([
            f"Chunk {i+1} ({c['chunk_id']}): {c['text'][:300]}..."
            for i, c in enumerate(retrieved_chunks[:3])  # Use top 3 for context
        ])
        
        # Base prompt
        base_prompt = f"""You are an expert evaluator assessing RAG system outputs for sleep research queries.

QUERY: {query}
QUERY TYPE: {category} | Phase1 Task: {phase1_task}

RETRIEVED EVIDENCE CHUNKS:
{chunks_text}

GENERATED ANSWER:
{answer}

"""
        
        # Add task-specific evaluation criteria
        if phase1_task == "CEE":
            # Claim-Evidence-Extraction task
            base_prompt += """EVALUATION CRITERIA FOR CEE (Claim-Evidence-Extraction):

GROUNDEDNESS (1-4 scale):
- 4: All claims are explicitly stated in retrieved chunks with matching evidence; citations are correct and verifiable
- 3: Most claims grounded; minor paraphrasing acceptable; citations mostly correct
- 2: Some claims not clearly supported by chunks; vague or incorrect citations
- 1: Hallucinations present; fabricated claims or citations; evidence doesn't match chunks

ANSWER RELEVANCE (1-4 scale):
- 4: Answer extracts specific claims with direct evidence/quotes and proper citations in Claim-Evidence-Citation format
- 3: Answer extracts claims but may lack some direct quotes or have minor citation issues
- 2: Answer provides general information but doesn't follow CEE format; missing specific claims with evidence
- 1: Answer doesn't extract claims or provide evidence; doesn't address CEE requirements

Check if answer:
- Extracts specific claims (not just general statements)
- Provides direct evidence/quotes for each claim
- Includes proper citations in (source_id, chunk_id) format
- Follows Claim-Evidence-Citation structure
"""
        
        elif phase1_task == "CSS":
            # Cross-Source Synthesis task
            base_prompt += """EVALUATION CRITERIA FOR CSS (Cross-Source Synthesis):

GROUNDEDNESS (1-4 scale):
- 4: All comparisons/agreements/disagreements are explicitly stated in retrieved chunks; citations correct
- 3: Most comparisons grounded; minor interpretation acceptable; citations mostly correct
- 2: Some comparisons not clearly supported; vague citations or missing evidence
- 1: Fabricated comparisons; citations don't support claims; evidence doesn't match chunks

ANSWER RELEVANCE (1-4 scale):
- 4: Answer identifies clear agreements and disagreements across sources with specific evidence and citations from each
- 3: Answer compares sources but may miss some agreements/disagreements or have incomplete citations
- 2: Answer mentions multiple sources but doesn't clearly synthesize agreements/disagreements
- 1: Answer doesn't compare sources or identify agreements/disagreements; doesn't address CSS requirements

Check if answer:
- Identifies areas of agreement between sources
- Identifies areas of disagreement or different emphasis
- Provides specific evidence from each source with citations
- Synthesizes findings across sources (not just lists them)
"""
        
        elif category == "edge_case":
            # Edge case queries - should state if evidence exists
            base_prompt += """EVALUATION CRITERIA FOR EDGE CASE QUERIES:

GROUNDEDNESS (1-4 scale):
- 4: Answer correctly identifies presence/absence of evidence; all claims about evidence are accurate
- 3: Answer mostly accurate about evidence availability; minor issues
- 2: Answer unclear about evidence availability; makes claims without proper checking
- 1: Answer fabricates evidence or incorrectly states evidence exists/doesn't exist

ANSWER RELEVANCE (1-4 scale):
- 4: Answer explicitly states whether evidence exists or not; if exists, provides it with citations; if not, clearly states absence
- 3: Answer addresses evidence availability but may be less explicit
- 2: Answer partially addresses query but doesn't clearly state evidence availability
- 1: Answer doesn't address whether evidence exists; provides unrelated information

Check if answer:
- Explicitly states "The provided evidence does not contain information about [topic]" if evidence is missing
- OR provides evidence with citations if evidence exists
- Doesn't fabricate evidence when none exists
- Clearly addresses the "does corpus contain evidence" aspect
"""
        
        else:
            # General direct/synthesis queries
            base_prompt += """EVALUATION CRITERIA FOR GENERAL QUERIES:

GROUNDEDNESS (1-4 scale):
- 4: All claims grounded in retrieved chunks; citations correct and verifiable
- 3: Most claims grounded; minor issues acceptable; citations mostly correct
- 2: Some claims unsupported; vague or incorrect citations
- 1: Hallucinations; fabricated citations; claims don't match chunks

ANSWER RELEVANCE (1-4 scale):
- 4: Directly and completely answers the query with specific findings and proper citations
- 3: Answers query well but may miss minor details; citations present
- 2: Partially answers query; key information missing; citations incomplete
- 1: Doesn't answer query; irrelevant or missing information

Check if answer:
- Directly addresses the query
- Includes specific findings/statistics when available
- Provides proper citations in (source_id, chunk_id) format
- Is comprehensive and relevant
"""
        
        base_prompt += """
TASK: Evaluate the answer and provide scores for GROUNDEDNESS and ANSWER_RELEVANCE.

Respond in JSON format:
{
  "groundedness_score": <1-4 integer>,
  "answer_relevance": <1-4 integer>,
  "groundedness_reasoning": "<brief explanation>",
  "relevance_reasoning": "<brief explanation>"
}
"""
        
        return base_prompt
    
    def evaluate_with_llm(self, result: Dict) -> Dict:
        """Use LLM to evaluate groundedness and answer relevance"""
        if not self.use_llm:
            return {
                'groundedness_score': None,
                'answer_relevance': None,
                'groundedness_reasoning': '',
                'relevance_reasoning': ''
            }
        
        prompt = self._get_evaluation_prompt(result)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            eval_result = json.loads(response_text)
            
            return {
                'groundedness_score': int(eval_result.get('groundedness_score', 0)),
                'answer_relevance': int(eval_result.get('answer_relevance', 0)),
                'groundedness_reasoning': eval_result.get('groundedness_reasoning', ''),
                'relevance_reasoning': eval_result.get('relevance_reasoning', '')
            }
        except Exception as e:
            print(f"Warning: LLM evaluation failed for {result.get('query_id')}: {e}")
            return {
                'groundedness_score': None,
                'answer_relevance': None,
                'groundedness_reasoning': f'Error: {str(e)}',
                'relevance_reasoning': ''
            }
    
    def score_all_results(self, results_path: str) -> pd.DataFrame:
        """
        Score all evaluation results
        
        Returns DataFrame with metrics
        """
        results = []
        with open(results_path) as f:
            for line in f:
                results.append(json.loads(line))
        
        scored = []
        for i, r in enumerate(results, 1):
            print(f"Evaluating [{i}/{len(results)}]: {r.get('query_id', 'unknown')}")
            
            cit_metrics = self.citation_precision(r)
            
            # LLM-based evaluation
            llm_eval = self.evaluate_with_llm(r) if self.use_llm else {
                'groundedness_score': None,
                'answer_relevance': None,
                'groundedness_reasoning': '',
                'relevance_reasoning': ''
            }
            
            scored.append({
                'query_id': r.get('query_id'),
                'category': r.get('category'),
                'phase1_task': r.get('phase1_task', 'general'),
                'query': r['query'],
                'citation_precision': cit_metrics['precision'],
                'total_citations': cit_metrics['total_citations'],
                'valid_citations': cit_metrics['valid_citations'],
                'invalid_citations': ','.join(cit_metrics['invalid']) if cit_metrics['invalid'] else '',
                'groundedness_score': llm_eval['groundedness_score'],
                'answer_relevance': llm_eval['answer_relevance'],
                'groundedness_reasoning': llm_eval['groundedness_reasoning'],
                'relevance_reasoning': llm_eval['relevance_reasoning']
            })
        
        return pd.DataFrame(scored)

if __name__ == "__main__":
    import sys
    
    # Determine which results file to use
    if len(sys.argv) > 1:
        results_path = sys.argv[1]
        if "enhanced" in results_path:
            scores_path = "outputs/enhanced_eval_scores.csv"
        elif "baseline" in results_path:
            scores_path = "outputs/baseline_eval_scores.csv"
        else:
            scores_path = "outputs/eval_scores.csv"
    else:
        results_path = "outputs/eval_results.jsonl"
        scores_path = "outputs/eval_scores.csv"
    
    metrics = EvaluationMetrics()
    results_df = metrics.score_all_results(results_path)
    results_df.to_csv(scores_path, index=False)
    
    # Check metrics
    print(f"Average citation precision: {results_df['citation_precision'].mean():.2f}")
    print(f"Total queries scored: {len(results_df)}")
    print(f"Results saved to: {scores_path}")