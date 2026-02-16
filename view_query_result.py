#!/usr/bin/env python3
"""
Helper script to view a complete query result with full chunk text for manual verification.
Usage: python view_query_result.py [query_id]
"""

import json
import re
import sys

def view_query_result(query_id=None):
    """View a complete query result with full chunk text"""
    
    # Load results
    with open('outputs/eval_results.jsonl', 'r') as f:
        results = [json.loads(line) for line in f]
    
    # Find the result
    if query_id:
        result = next((r for r in results if r.get('query_id') == query_id), None)
        if not result:
            print(f"Query ID '{query_id}' not found.")
            print(f"\nAvailable query IDs:")
            for r in results:
                print(f"  - {r.get('query_id')}")
            return
    else:
        # Show first result
        result = results[0]
    
    print('=' * 100)
    print('COMPLETE QUERY RESPONSE WITH FULL CHUNK TEXT FOR VERIFICATION')
    print('=' * 100)
    
    print(f'\n📋 QUERY ID: {result.get("query_id")}')
    print(f'📋 CATEGORY: {result.get("category")} | Phase1 Task: {result.get("phase1_task", "general")}')
    print(f'\n❓ QUERY:')
    print(f'   {result["query"]}')
    
    print(f'\n📝 GENERATED ANSWER:')
    print('-' * 100)
    answer = result['answer']
    print(answer)
    print('-' * 100)
    
    # Extract citations from answer
    citations = re.findall(r'\(([a-z0-9_]+),\s*([a-z0-9_]+)\)', answer)
    print(f'\n📚 CITATIONS FOUND IN ANSWER: {len(citations)}')
    for i, (source_id, chunk_id) in enumerate(citations, 1):
        print(f'   {i}. ({source_id}, {chunk_id})')
    
    print(f'\n🔍 FULL TEXT OF CITED CHUNKS:')
    print('=' * 100)
    
    # Create a dict for quick lookup
    chunk_dict = {chunk['chunk_id']: chunk for chunk in result['retrieved_chunks']}
    
    for i, (source_id, chunk_id) in enumerate(citations, 1):
        if chunk_id in chunk_dict:
            chunk = chunk_dict[chunk_id]
            print(f'\n✅ CITATION {i}: ({source_id}, {chunk_id})')
            print(f'   Similarity Score: {chunk.get("similarity_score", "N/A")}')
            print(f'   Full Chunk Text:')
            print('   ' + '=' * 96)
            print(f'   {chunk["text"]}')
            print('   ' + '=' * 96)
        else:
            print(f'\n❌ CITATION {i}: ({source_id}, {chunk_id}) - NOT FOUND IN RETRIEVED CHUNKS!')
    
    print(f'\n📊 ALL RETRIEVED CHUNKS ({len(result["retrieved_chunks"])} total):')
    for i, chunk in enumerate(result['retrieved_chunks'], 1):
        cited = chunk['chunk_id'] in [cid for _, cid in citations]
        marker = '✅ CITED' if cited else '   '
        similarity = chunk.get('similarity_score', 'N/A')
        if isinstance(similarity, float):
            similarity = f'{similarity:.4f}'
        print(f'   {marker} {i}. {chunk["chunk_id"]} (similarity: {similarity})')
    
    print(f'\n✅ VERIFICATION CHECKLIST:')
    print(f'   1. ✓ Check if each citation in the answer matches a retrieved chunk')
    print(f'   2. ✓ Verify that the claims in the answer are actually stated in the cited chunks')
    print(f'   3. ✓ Check if direct quotes in the answer match the chunk text verbatim')
    print(f'   4. ✓ Verify statistics/numbers match what\'s in the chunks')

if __name__ == "__main__":
    query_id = sys.argv[1] if len(sys.argv) > 1 else None
    view_query_result(query_id)
