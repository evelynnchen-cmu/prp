import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.rag.pipeline import RAGPipeline

def load_queries(path: str) -> list:
    """Load all queries from JSON"""
    with open(path) as f:
        data = json.load(f)
    
    queries = []
    for category in ['direct_queries', 'synthesis_queries', 'edge_case_queries']:
        queries.extend(data.get(category, []))
    return queries

def run_evaluation(
    queries_path: str = "src/eval/queries.json",
    output_path: str = None,
    enhance: bool = False
):
    """Run all evaluation queries"""
    # Load queries
    queries = load_queries(queries_path)
    print(f"Loaded {len(queries)} queries")
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    eval_type = "enhanced" if enhance else "baseline"
    print(f"Running {eval_type} evaluation")
    
    # Set output paths
    if output_path is None:
        if enhance:
            output_path = "outputs/enhanced_eval_results.jsonl"
        else:
            output_path = "outputs/baseline_eval_results.jsonl"
    
    # Import enhancement if needed
    if enhance:
        from src.rag.structured_citations import StructuredCitationGenerator
        citation_enhancer = StructuredCitationGenerator()
    
    # Process each query
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    results = []
    
    for i, q in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Processing: {q['id']}")
        
        result = pipeline.query(q['query'], k=5, log=False, enhance=enhance)
        result['query_id'] = q['id']
        result['category'] = q['category']
        result['phase1_task'] = q.get('phase1_task', 'general')
        
        # Save to file
        with open(output_path, 'a') as f:
            f.write(json.dumps(result) + '\n')
        
        results.append(result)
    
    # Generate summary
    summary = {
        'total_queries': len(queries),
        'by_category': {
            'direct': len([q for q in queries if q['category'] == 'direct']),
            'synthesis': len([q for q in queries if q['category'] == 'synthesis']),
            'edge_case': len([q for q in queries if q['category'] == 'edge_case'])
        },
        'enhanced': enhance
    }
    
    # Set summary path
    if enhance:
        summary_path = "outputs/enhanced_eval_summary.json"
    else:
        summary_path = "outputs/baseline_eval_summary.json"
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Evaluation complete")
    print(f"  Results: {output_path}")
    print(f"  Summary: {summary_path}")

if __name__ == "__main__":
    import sys
    enhance = '--enhanced' in sys.argv
    run_evaluation(enhance=enhance)
