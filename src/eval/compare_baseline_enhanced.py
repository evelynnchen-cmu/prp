#!/usr/bin/env python3
"""
Compare baseline vs enhanced (structured citations) results
Generates comprehensive comparison report for evaluation
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
import re

def load_results(results_path: str) -> List[Dict]:
    """Load evaluation results from JSONL"""
    results = []
    with open(results_path, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results

def extract_citations(text: str) -> List[str]:
    """Extract citations from text"""
    pattern = r'\(([a-z0-9_]+),\s*([a-z0-9_]+)\)'
    matches = re.findall(pattern, text)
    return [f"({m[0]}, {m[1]})" for m in matches]

def compare_metrics():
    """Compare baseline vs enhanced metrics"""
    print("=" * 100)
    print("BASELINE vs ENHANCED (STRUCTURED CITATIONS) COMPARISON")
    print("=" * 100)
    
    # Load scores
    baseline_scores = pd.read_csv("outputs/baseline_eval_scores.csv")
    enhanced_scores = pd.read_csv("outputs/enhanced_eval_scores.csv")
    
    print("\n📊 OVERALL METRICS COMPARISON")
    print("-" * 100)
    
    metrics = ['citation_precision', 'groundedness_score', 'answer_relevance', 'total_citations']
    comparison = []
    
    for metric in metrics:
        baseline_mean = baseline_scores[metric].mean()
        enhanced_mean = enhanced_scores[metric].mean()
        diff = enhanced_mean - baseline_mean
        pct_change = (diff / baseline_mean * 100) if baseline_mean > 0 else 0
        
        comparison.append({
            'metric': metric,
            'baseline': baseline_mean,
            'enhanced': enhanced_mean,
            'difference': diff,
            'percent_change': pct_change
        })
        
        print(f"\n{metric.upper().replace('_', ' ')}:")
        print(f"  Baseline: {baseline_mean:.3f}")
        print(f"  Enhanced: {enhanced_mean:.3f}")
        print(f"  Change:   {diff:+.3f} ({pct_change:+.1f}%)")
    
    # By category
    print("\n\n📈 METRICS BY CATEGORY")
    print("-" * 100)
    
    for category in baseline_scores['category'].unique():
        baseline_cat = baseline_scores[baseline_scores['category'] == category]
        enhanced_cat = enhanced_scores[enhanced_scores['category'] == category]
        
        print(f"\n{category.upper()}:")
        print(f"  Citation Precision: {baseline_cat['citation_precision'].mean():.3f} → {enhanced_cat['citation_precision'].mean():.3f}")
        print(f"  Groundedness: {baseline_cat['groundedness_score'].mean():.2f} → {enhanced_cat['groundedness_score'].mean():.2f}")
        print(f"  Answer Relevance: {baseline_cat['answer_relevance'].mean():.2f} → {enhanced_cat['answer_relevance'].mean():.2f}")
    
    # By Phase1 task
    print("\n\n📋 METRICS BY PHASE1 TASK")
    print("-" * 100)
    
    for task in baseline_scores['phase1_task'].unique():
        baseline_task = baseline_scores[baseline_scores['phase1_task'] == task]
        enhanced_task = enhanced_scores[enhanced_scores['phase1_task'] == task]
        
        print(f"\n{task.upper()}:")
        print(f"  Citation Precision: {baseline_task['citation_precision'].mean():.3f} → {enhanced_task['citation_precision'].mean():.3f}")
        print(f"  Groundedness: {baseline_task['groundedness_score'].mean():.2f} → {enhanced_task['groundedness_score'].mean():.2f}")
        print(f"  Answer Relevance: {baseline_task['answer_relevance'].mean():.2f} → {enhanced_task['answer_relevance'].mean():.2f}")
    
    # Enhanced features analysis
    print("\n\n✨ ENHANCED FEATURES ANALYSIS")
    print("-" * 100)
    
    enhanced_results = load_results("outputs/enhanced_eval_results.jsonl")
    
    # Citation validation stats
    validation_passed = sum(1 for r in enhanced_results if r.get('citation_validation_passed', False))
    total_with_citations = sum(1 for r in enhanced_results if r.get('total_citations', 0) > 0)
    
    print(f"\nCitation Validation:")
    print(f"  Queries with valid citations: {validation_passed}/{len(enhanced_results)}")
    print(f"  Validation pass rate: {validation_passed/len(enhanced_results)*100:.1f}%")
    
    # Reference list stats
    avg_sources = sum(r.get('num_unique_sources', 0) for r in enhanced_results) / len(enhanced_results)
    print(f"\nReference Lists:")
    print(f"  Average unique sources per query: {avg_sources:.1f}")
    print(f"  Queries with reference lists: {sum(1 for r in enhanced_results if r.get('reference_list'))}/{len(enhanced_results)}")
    
    # Invalid citations analysis
    invalid_citations = []
    for r in enhanced_results:
        invalid = r.get('invalid_citations', [])
        if invalid:
            invalid_citations.append({
                'query_id': r.get('query_id'),
                'query': r.get('query', '')[:60],
                'invalid_count': len(invalid),
                'invalid_citations': invalid
            })
    
    if invalid_citations:
        print(f"\nInvalid Citations Found:")
        print(f"  Queries with invalid citations: {len(invalid_citations)}/{len(enhanced_results)}")
        print(f"  Sample invalid citations:")
        for inv in invalid_citations[:3]:
            print(f"    {inv['query_id']}: {inv['invalid_count']} invalid - {inv['invalid_citations'][:2]}")
    else:
        print(f"\n✓ All citations validated successfully!")
    
    # Save comparison to CSV
    comparison_df = pd.DataFrame(comparison)
    comparison_df.to_csv("outputs/baseline_enhanced_comparison.csv", index=False)
    print(f"\n✓ Comparison saved to: outputs/baseline_enhanced_comparison.csv")
    
    return comparison_df, invalid_citations

def find_failure_cases():
    """Find representative failure cases for evaluation report"""
    print("\n\n" + "=" * 100)
    print("FAILURE CASE ANALYSIS")
    print("=" * 100)
    
    enhanced_scores = pd.read_csv("outputs/enhanced_eval_scores.csv")
    enhanced_results = load_results("outputs/enhanced_eval_results.jsonl")
    
    # Create lookup
    results_dict = {r['query_id']: r for r in enhanced_results}
    scores_dict = {row['query_id']: row for _, row in enhanced_scores.iterrows()}
    
    failures = []
    
    # Find failures by different criteria
    # 1. Low citation precision (invalid citations)
    low_precision = enhanced_scores[enhanced_scores['citation_precision'] < 0.8]
    for _, row in low_precision.iterrows():
        query_id = row['query_id']
        result = results_dict.get(query_id, {})
        failures.append({
            'type': 'Low Citation Precision',
            'query_id': query_id,
            'category': row['category'],
            'phase1_task': row.get('phase1_task', 'general'),
            'query': row['query'],
            'issue': f"Citation precision: {row['citation_precision']:.2f} - {row['invalid_citations']}",
            'metrics': {
                'citation_precision': row['citation_precision'],
                'total_citations': row['total_citations'],
                'valid_citations': row['valid_citations']
            },
            'answer': result.get('answer', ''),
            'retrieved_chunks': result.get('retrieved_chunks', []),
            'invalid_citations': result.get('invalid_citations', []),
            'reference_list': result.get('reference_list', ''),
            'citation_validation_passed': result.get('citation_validation_passed', False),
            'num_unique_sources': result.get('num_unique_sources', 0),
            'model': result.get('model', ''),
            'prompt_version': result.get('prompt_version', ''),
            'metadata': result.get('metadata', {}),
            'root_cause': 'Citations in answer do not match retrieved chunks'
        })
    
    # 2. Missing citations
    no_citations = enhanced_scores[enhanced_scores['total_citations'] == 0]
    for _, row in no_citations.iterrows():
        query_id = row['query_id']
        result = results_dict.get(query_id, {})
        if len(result.get('retrieved_chunks', [])) > 0:
            failures.append({
                'type': 'Missing Citations',
                'query_id': query_id,
                'category': row['category'],
                'phase1_task': row.get('phase1_task', 'general'),
                'query': row['query'],
                'issue': f"No citations in answer despite {len(result.get('retrieved_chunks', []))} retrieved chunks",
                'metrics': {
                    'citation_precision': 0.0,
                    'total_citations': 0,
                    'groundedness_score': row.get('groundedness_score'),
                    'answer_relevance': row.get('answer_relevance')
                },
                'answer': result.get('answer', ''),
                'retrieved_chunks': result.get('retrieved_chunks', []),
                'reference_list': result.get('reference_list', ''),
                'citation_validation_passed': result.get('citation_validation_passed', False),
                'num_unique_sources': result.get('num_unique_sources', 0),
                'model': result.get('model', ''),
                'prompt_version': result.get('prompt_version', ''),
                'metadata': result.get('metadata', {}),
                'root_cause': 'Answer generated without citations despite having retrieved chunks'
            })
    
    # 3. Low groundedness
    low_groundedness = enhanced_scores[enhanced_scores['groundedness_score'] < 3]
    for _, row in low_groundedness.iterrows():
        query_id = row['query_id']
        if query_id not in [f['query_id'] for f in failures]:
            result = results_dict.get(query_id, {})
            failures.append({
                'type': 'Low Groundedness',
                'query_id': query_id,
                'category': row['category'],
                'phase1_task': row.get('phase1_task', 'general'),
                'query': row['query'],
                'issue': f"Groundedness score: {row['groundedness_score']}/4 (below average)",
                'metrics': {
                    'groundedness_score': row['groundedness_score'],
                    'answer_relevance': row['answer_relevance'],
                    'citation_precision': row['citation_precision']
                },
                'answer': result.get('answer', ''),
                'retrieved_chunks': result.get('retrieved_chunks', []),
                'groundedness_reasoning': row.get('groundedness_reasoning', ''),
                'reference_list': result.get('reference_list', ''),
                'citation_validation_passed': result.get('citation_validation_passed', False),
                'invalid_citations': result.get('invalid_citations', []),
                'num_unique_sources': result.get('num_unique_sources', 0),
                'model': result.get('model', ''),
                'prompt_version': result.get('prompt_version', ''),
                'metadata': result.get('metadata', {}),
                'root_cause': 'Answer claims may not be fully supported by retrieved chunks'
            })
    
    # 4. Low answer relevance
    low_relevance = enhanced_scores[enhanced_scores['answer_relevance'] < 3]
    for _, row in low_relevance.iterrows():
        query_id = row['query_id']
        if query_id not in [f['query_id'] for f in failures]:
            result = results_dict.get(query_id, {})
            failures.append({
                'type': 'Low Answer Relevance',
                'query_id': query_id,
                'category': row['category'],
                'phase1_task': row.get('phase1_task', 'general'),
                'query': row['query'],
                'issue': f"Answer relevance: {row['answer_relevance']}/4 (below average)",
                'metrics': {
                    'answer_relevance': row['answer_relevance'],
                    'groundedness_score': row['groundedness_score'],
                    'citation_precision': row['citation_precision']
                },
                'answer': result.get('answer', ''),
                'retrieved_chunks': result.get('retrieved_chunks', []),
                'relevance_reasoning': row.get('relevance_reasoning', ''),
                'reference_list': result.get('reference_list', ''),
                'citation_validation_passed': result.get('citation_validation_passed', False),
                'invalid_citations': result.get('invalid_citations', []),
                'num_unique_sources': result.get('num_unique_sources', 0),
                'model': result.get('model', ''),
                'prompt_version': result.get('prompt_version', ''),
                'metadata': result.get('metadata', {}),
                'root_cause': 'Answer does not adequately address the query'
            })
    
    # 5. Invalid citations (from enhanced results)
    for result in enhanced_results:
        query_id = result.get('query_id')
        invalid = result.get('invalid_citations', [])
        if invalid and query_id not in [f['query_id'] for f in failures]:
            row = scores_dict.get(query_id, {})
            failures.append({
                'type': 'Invalid Citations',
                'query_id': query_id,
                'category': result.get('category', 'unknown'),
                'phase1_task': result.get('phase1_task', 'general'),
                'query': result.get('query', ''),
                'issue': f"Citation validation failed: {len(invalid)} invalid citations",
                'metrics': {
                    'citation_precision': row.get('citation_precision', 0),
                    'total_citations': row.get('total_citations', 0),
                    'invalid_citations': invalid
                },
                'answer': result.get('answer', ''),
                'retrieved_chunks': result.get('retrieved_chunks', []),
                'invalid_citations': invalid,
                'reference_list': result.get('reference_list', ''),
                'citation_validation_passed': result.get('citation_validation_passed', False),
                'num_unique_sources': result.get('num_unique_sources', 0),
                'model': result.get('model', ''),
                'prompt_version': result.get('prompt_version', ''),
                'metadata': result.get('metadata', {}),
                'root_cause': 'Citations reference chunks not in retrieved set'
            })
    
    # Select 3 most representative failures
    # Prioritize: invalid citations > missing citations > low scores
    selected = []
    seen_types = set()
    
    # First, get one of each major type
    for failure in failures:
        if failure['type'] not in seen_types:
            selected.append(failure)
            seen_types.add(failure['type'])
            if len(selected) >= 3:
                break
    
    # Fill remaining slots with most severe cases
    if len(selected) < 3:
        remaining = [f for f in failures if f['query_id'] not in [s['query_id'] for s in selected]]
        remaining.sort(key=lambda x: (
            x['metrics'].get('citation_precision', 1),
            x['metrics'].get('groundedness_score', 5),
            x['metrics'].get('answer_relevance', 5)
        ))
        selected.extend(remaining[:3-len(selected)])
    
    print(f"\nFound {len(failures)} failure cases. Selected {len(selected)} representative ones:\n")
    
    for i, failure in enumerate(selected, 1):
        print(f"{i}. {failure['type']}")
        print(f"   Query ID: {failure['query_id']}")
        print(f"   Query: {failure['query'][:70]}...")
        print(f"   Issue: {failure['issue']}")
        print(f"   Root Cause: {failure['root_cause']}")
        print(f"   Metrics: {failure['metrics']}\n")
    
    # Save failure cases
    with open("outputs/representative_failure_cases.json", 'w') as f:
        json.dump(selected, f, indent=2)
    
    print(f"✓ Saved to: outputs/representative_failure_cases.json\n")
    
    return selected

def generate_report_data():
    """Generate all data needed for evaluation report"""
    comparison_df, invalid_citations = compare_metrics()
    failure_cases = find_failure_cases()
    
    baseline_scores = pd.read_csv("outputs/baseline_eval_scores.csv")
    enhanced_scores = pd.read_csv("outputs/enhanced_eval_scores.csv")
    
    metrics = ['citation_precision', 'groundedness_score', 'answer_relevance', 'total_citations']
    
    report_data = {
        "overall_metrics": {
            "baseline": {
                "citation_precision": float(baseline_scores['citation_precision'].mean()),
                "groundedness": float(baseline_scores['groundedness_score'].mean()),
                "answer_relevance": float(baseline_scores['answer_relevance'].mean()),
                "avg_citations": float(baseline_scores['total_citations'].mean())
            },
            "enhanced": {
                "citation_precision": float(enhanced_scores['citation_precision'].mean()),
                "groundedness": float(enhanced_scores['groundedness_score'].mean()),
                "answer_relevance": float(enhanced_scores['answer_relevance'].mean()),
                "avg_citations": float(enhanced_scores['total_citations'].mean())
            }
        },
        "improvements": {
            "citation_precision": {
                "absolute": float(enhanced_scores['citation_precision'].mean() - baseline_scores['citation_precision'].mean()),
                "percent": float((enhanced_scores['citation_precision'].mean() - baseline_scores['citation_precision'].mean()) / baseline_scores['citation_precision'].mean() * 100) if baseline_scores['citation_precision'].mean() > 0 else 0
            },
            "groundedness_score": {
                "absolute": float(enhanced_scores['groundedness_score'].mean() - baseline_scores['groundedness_score'].mean()),
                "percent": float((enhanced_scores['groundedness_score'].mean() - baseline_scores['groundedness_score'].mean()) / baseline_scores['groundedness_score'].mean() * 100) if baseline_scores['groundedness_score'].mean() > 0 else 0
            },
            "answer_relevance": {
                "absolute": float(enhanced_scores['answer_relevance'].mean() - baseline_scores['answer_relevance'].mean()),
                "percent": float((enhanced_scores['answer_relevance'].mean() - baseline_scores['answer_relevance'].mean()) / baseline_scores['answer_relevance'].mean() * 100) if baseline_scores['answer_relevance'].mean() > 0 else 0
            }
        },
        "metrics_by_category": {
            "baseline": baseline_scores.groupby('category')[metrics].mean().to_dict(orient='index'),
            "enhanced": enhanced_scores.groupby('category')[metrics].mean().to_dict(orient='index')
        },
        "metrics_by_phase1_task": {
            "baseline": baseline_scores.groupby('phase1_task')[metrics].mean().to_dict(orient='index'),
            "enhanced": enhanced_scores.groupby('phase1_task')[metrics].mean().to_dict(orient='index')
        },
        "enhanced_features": {
            "citation_validation_passed": sum(1 for r in load_results("outputs/enhanced_eval_results.jsonl") if r.get('citation_validation_passed', False)),
            "total_queries": len(load_results("outputs/enhanced_eval_results.jsonl")),
            "avg_unique_sources": sum(r.get('num_unique_sources', 0) for r in load_results("outputs/enhanced_eval_results.jsonl")) / len(load_results("outputs/enhanced_eval_results.jsonl")),
            "invalid_citations_count": len(invalid_citations)
        },
        "representative_failure_cases": failure_cases
    }
    
    with open("outputs/eval_report_data.json", 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print("\n" + "=" * 100)
    print("EVALUATION REPORT DATA SUMMARY")
    print("=" * 100)
    print(f"\n✓ All data saved to: outputs/eval_report_data.json")
    print(f"\n📊 KEY METRICS FOR REPORT:")
    print(f"  Baseline Citation Precision: {report_data['overall_metrics']['baseline']['citation_precision']:.3f}")
    print(f"  Enhanced Citation Precision: {report_data['overall_metrics']['enhanced']['citation_precision']:.3f}")
    print(f"  Improvement: {report_data['improvements']['citation_precision']['absolute']:+.3f} ({report_data['improvements']['citation_precision']['percent']:+.1f}%)\n")
    print(f"  Baseline Groundedness: {report_data['overall_metrics']['baseline']['groundedness']:.2f}/4")
    print(f"  Enhanced Groundedness: {report_data['overall_metrics']['enhanced']['groundedness']:.2f}/4")
    print(f"  Improvement: {report_data['improvements']['groundedness_score']['absolute']:+.2f}/4 ({report_data['improvements']['groundedness_score']['percent']:+.1f}%)\n")
    print(f"  Baseline Answer Relevance: {report_data['overall_metrics']['baseline']['answer_relevance']:.2f}/4")
    print(f"  Enhanced Answer Relevance: {report_data['overall_metrics']['enhanced']['answer_relevance']:.2f}/4")
    print(f"  Improvement: {report_data['improvements']['answer_relevance']['absolute']:+.2f}/4 ({report_data['improvements']['answer_relevance']['percent']:+.1f}%)\n")
    print(f"  Citation Validation Pass Rate: {report_data['enhanced_features']['citation_validation_passed']}/{report_data['enhanced_features']['total_queries']} ({report_data['enhanced_features']['citation_validation_passed']/report_data['enhanced_features']['total_queries']*100:.1f}%)\n")

if __name__ == "__main__":
    generate_report_data()
