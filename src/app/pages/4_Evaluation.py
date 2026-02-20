import streamlit as st
import json
import subprocess
import sys
from pathlib import Path

# Pages live in src/app/pages/ → need 4 parents to get repo root (prp)
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.app.utils import OUTPUTS_DIR

EVAL_REPORT_PATH = OUTPUTS_DIR / "eval_report_data.json"
COMPARISON_CSV_PATH = OUTPUTS_DIR / "baseline_enhanced_comparison.csv"
FAILURE_CASES_PATH = OUTPUTS_DIR / "representative_failure_cases.json"

st.title("Evaluation")
st.caption("Phase 2 metrics, baseline vs enhanced comparison, and re-run evaluation.")

# Task 7.1: Summary metrics
if not EVAL_REPORT_PATH.exists():
    st.warning("Run evaluation first: see README. Use **Re-run Evaluation** below to generate metrics.")
    report = None
else:
    with open(EVAL_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

if report:
    overall = report.get("overall_metrics", {})
    baseline = overall.get("baseline", {})
    enhanced = overall.get("enhanced", {})

    st.subheader("Overall metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        cp_b = baseline.get("citation_precision", 0)
        cp_e = enhanced.get("citation_precision", 0)
        st.metric("Citation Precision (baseline)", f"{cp_b * 100:.1f}%", f"→ {cp_e * 100:.1f}% (enhanced)")
    with col2:
        g_b = baseline.get("groundedness", 0)
        g_e = enhanced.get("groundedness", 0)
        st.metric("Groundedness (baseline)", f"{g_b:.2f}/4", f"→ {g_e:.2f}/4 (enhanced)")
    with col3:
        ar_b = baseline.get("answer_relevance", 0)
        ar_e = enhanced.get("answer_relevance", 0)
        st.metric("Answer Relevance (baseline)", f"{ar_b:.2f}/4", f"→ {ar_e:.2f}/4 (enhanced)")

    improvements = report.get("improvements", {})
    if improvements:
        st.caption(
            f"Improvements: Citation Precision {improvements.get('citation_precision', {}).get('percent', 0):.1f}%, "
            f"Groundedness {improvements.get('groundedness_score', {}).get('percent', 0):.1f}%, "
            f"Answer Relevance {improvements.get('answer_relevance', {}).get('percent', 0):.1f}%"
        )

    # Task 7.2: Baseline vs enhanced comparison table
    st.subheader("Baseline vs enhanced comparison")
    if COMPARISON_CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(COMPARISON_CSV_PATH)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Comparison file not found. Run **Re-run Evaluation** to generate it.")

    # Task 7.3: Category breakdown
    st.subheader("Metrics by category")
    by_cat = report.get("metrics_by_category", {})
    if by_cat:
        base_cat = by_cat.get("baseline", {})
        enh_cat = by_cat.get("enhanced", {})
        categories = list(base_cat.keys()) if base_cat else list(enh_cat.keys())
        if categories:
            import pandas as pd
            cat_rows = []
            for cat in categories:
                b = base_cat.get(cat, {})
                e = enh_cat.get(cat, {})
                cat_rows.append({
                    "Category": cat,
                    "Citation Precision (B)": f"{b.get('citation_precision', 0):.2f}",
                    "Citation Precision (E)": f"{e.get('citation_precision', 0):.2f}",
                    "Groundedness (B)": f"{b.get('groundedness_score', 0):.2f}",
                    "Groundedness (E)": f"{e.get('groundedness_score', 0):.2f}",
                    "Answer Relevance (B)": f"{b.get('answer_relevance', 0):.2f}",
                    "Answer Relevance (E)": f"{e.get('answer_relevance', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

    # Task 7.4: Representative failure cases
    st.subheader("Representative failure cases")
    if FAILURE_CASES_PATH.exists():
        with open(FAILURE_CASES_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)
        if isinstance(cases, list):
            for i, case in enumerate(cases[:10]):  # up to 10
                title = case.get("type", f"Case {i+1}")
                if case.get("query"):
                    title = f"{title}: {str(case.get('query', ''))[:50]}..."
                with st.expander(title):
                    st.markdown("**Query:** " + str(case.get("query", "")))
                    ans = case.get("answer", "")
                    st.markdown("**Answer (excerpt):** " + (ans[:500] + "..." if len(ans) > 500 else ans))
                    st.markdown("**What failed:** " + str(case.get("issue", "—")))
                    if case.get("root_cause"):
                        st.markdown("**Root cause:** " + str(case["root_cause"]))
    else:
        st.info("Failure cases file not found. Run **Re-run Evaluation** to generate it.")

# Task 7.5: Re-run Evaluation button (required)
st.divider()
st.subheader("Re-run evaluation")
if st.button("Re-run Evaluation"):
    progress = st.progress(0, text="Running evaluation…")
    cwd = str(repo_root)
    steps = [
        (["python", "-m", "src.eval.run_eval"], "Baseline eval"),
        (["python", "-m", "src.eval.metrics", "outputs/baseline_eval_results.jsonl"], "Baseline metrics"),
        (["python", "-m", "src.eval.run_eval", "--enhanced"], "Enhanced eval"),
        (["python", "-m", "src.eval.metrics", "outputs/enhanced_eval_results.jsonl"], "Enhanced metrics"),
        (["python", "-m", "src.eval.compare_baseline_enhanced"], "Compare & report"),
    ]
    try:
        for i, (cmd, label) in enumerate(steps):
            progress.progress((i + 1) / len(steps), text=label + "…")
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
            if r.returncode != 0:
                st.error(f"Step failed: {label}\n{r.stderr or r.stdout}")
                progress.empty()
                st.stop()
        progress.progress(1.0, text="Done.")
        st.success("Evaluation complete. Refreshing…")
        st.rerun()
    except subprocess.TimeoutExpired:
        st.error("Evaluation timed out.")
    except Exception as e:
        st.error(str(e))
    finally:
        progress.empty()
