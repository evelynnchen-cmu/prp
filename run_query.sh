#!/bin/bash
# Single command to query the RAG system
# Usage: 
#   ./run_query.sh "your query here"              # Baseline mode (default)
#   ./run_query.sh "your query here" baseline     # Baseline mode
#   ./run_query.sh "your query here" enhanced      # Enhanced mode (structured citations)
#   ./run_query.sh "your query here" both          # Compare baseline vs enhanced

QUERY="$1"
MODE="${2:-baseline}"

if [ -z "$QUERY" ]; then
    echo "Usage: ./run_query.sh \"your query here\" [baseline|enhanced|both]"
    echo ""
    echo "Modes:"
    echo "  baseline  - Standard RAG pipeline (default)"
    echo "  enhanced  - With structured citations (validation + reference list)"
    echo "  both      - Run both and compare results"
    exit 1
fi

if [ "$MODE" != "baseline" ] && [ "$MODE" != "enhanced" ] && [ "$MODE" != "both" ]; then
    echo "Error: Invalid mode '$MODE'. Use 'baseline', 'enhanced', or 'both'"
    exit 1
fi

python -c "
from src.rag.pipeline import RAGPipeline
import json
import re

def print_result(result, title, is_enhanced=False):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)
    print('QUERY:', result['query'])
    print('\nRETRIEVED CHUNKS:', len(result['retrieved_chunks']))
    for i, chunk in enumerate(result['retrieved_chunks'], 1):
        score = chunk.get('similarity_score', chunk.get('hybrid_score', 'N/A'))
        print(f'  {i}. {chunk[\"chunk_id\"]} (score: {score})')
    
    print('\n' + '-' * 80)
    print('ANSWER:')
    print('-' * 80)
    print(result['answer'])
    
    print('\n' + '-' * 80)
    print('METADATA:')
    print('-' * 80)
    print(f'  Model: {result[\"model\"]}')
    print(f'  Retrieval method: {result[\"metadata\"].get(\"retrieval_method\", \"dense\")}')
    print(f'  Tokens used: {result[\"metadata\"].get(\"total_tokens\", \"N/A\")}')
    
    # Extract citations
    citations = re.findall(r'\\(([a-z0-9_]+),\\s*([a-z0-9_]+)\\)', result['answer'])
    print(f'\n  Citations found: {len(citations)}')
    if citations:
        print('  Sample citations:')
        for cit in citations[:3]:
            print(f'    ({cit[0]}, {cit[1]})')
    
    # Enhanced features
    if is_enhanced:
        print('\n' + '-' * 80)
        print('ENHANCED FEATURES:')
        print('-' * 80)
        validation_passed = result.get('citation_validation_passed', False)
        invalid = result.get('invalid_citations', [])
        print(f'  Citation validation: {\"✓ PASSED\" if validation_passed else \"✗ FAILED\"}')
        if invalid:
            print(f'  Invalid citations: {len(invalid)}')
            for inv in invalid[:3]:
                print(f'    - {inv}')
        else:
            print('  Invalid citations: None')
        
        ref_list = result.get('reference_list', '')
        if ref_list:
            print(f'\n  Unique sources: {result.get(\"num_unique_sources\", 0)}')
            print('\n  Reference List:')
            for line in ref_list.split('\n')[:5]:
                print(f'    {line}')
            if ref_list.count('\n') >= 5:
                print(f'    ... ({ref_list.count(chr(10)) - 4} more)')

# Initialize pipeline
pipeline = RAGPipeline()

if '$MODE' == 'both':
    # Run both modes and compare
    print('Running BASELINE mode...')
    baseline = pipeline.query('$QUERY', k=5, log=True, enhance=False)
    print_result(baseline, 'BASELINE RESULT', is_enhanced=False)
    
    print('\n\n' + '#' * 80)
    print('#' * 80)
    print('\nRunning ENHANCED mode...')
    enhanced = pipeline.query('$QUERY', k=5, log=True, enhance=True)
    print_result(enhanced, 'ENHANCED RESULT', is_enhanced=True)
    
    # Comparison
    print('\n\n' + '=' * 80)
    print('COMPARISON')
    print('=' * 80)
    baseline_citations = re.findall(r'\\(([a-z0-9_]+),\\s*([a-z0-9_]+)\\)', baseline['answer'])
    enhanced_citations = re.findall(r'\\(([a-z0-9_]+),\\s*([a-z0-9_]+)\\)', enhanced['answer'])
    
    print(f'\nCitations:')
    print(f'  Baseline: {len(baseline_citations)} citations')
    print(f'  Enhanced: {len(enhanced_citations)} citations')
    
    if enhanced.get('citation_validation_passed'):
        print(f'  Enhanced validation: ✓ All citations valid')
    else:
        invalid_count = len(enhanced.get('invalid_citations', []))
        print(f'  Enhanced validation: ✗ {invalid_count} invalid citations found')
    
    if enhanced.get('reference_list'):
        print(f'\nEnhanced features:')
        print(f'  Reference list: ✓ Generated ({enhanced.get(\"num_unique_sources\", 0)} sources)')
    
    print(f'\nAnswer length:')
    print(f'  Baseline: {len(baseline[\"answer\"])} characters')
    print(f'  Enhanced: {len(enhanced[\"answer\"])} characters')
    
elif '$MODE' == 'enhanced':
    result = pipeline.query('$QUERY', k=5, log=True, enhance=True)
    print_result(result, 'ENHANCED RESULT', is_enhanced=True)
else:
    result = pipeline.query('$QUERY', k=5, log=True, enhance=False)
    print_result(result, 'BASELINE RESULT', is_enhanced=False)

print('\n✓ Query logged to logs/query_logs.jsonl')
"
