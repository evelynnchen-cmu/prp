# Sleep & Well-being Research Portal - Phase 2

## Quick Start (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

<!-- 2. **Set API key:**
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```
   Or export it:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ``` -->

2. **Run ingestion pipeline:**
   ```bash
   python -m src.ingest.pipeline
   ```

3. **Build vector index:**
   ```bash
   python -m src.rag.build_index
   ```

4. **Query the system:**
   ```bash
   # Baseline mode (default)
   ./run_query.sh "How does sleep duration affect mental health?"
   
   # Enhanced mode (with structured citations)
   ./run_query.sh "How does sleep duration affect mental health?" enhanced
   
   # Compare both modes
   ./run_query.sh "How does sleep duration affect mental health?" both
   
   # Or using Python directly
   python -c "from src.rag.pipeline import RAGPipeline; p = RAGPipeline(); print(p.query('How does sleep duration affect mental health?')['answer'])"
   ```

## Project Structure

```
├── data/
│   ├── raw/                    # Source PDFs (16 papers)
│   ├── processed/              # Parsed text, chunks, vector index
│   │   ├── *.txt               # Processed text files
│   │   ├── chunks.jsonl        # All chunks (525 total)
│   │   └── vector_index/        # FAISS index + metadata
│   ├── data_manifest.json      # Source metadata (JSON format)
│   └── data_manifest.csv       # Source metadata (CSV format)
├── src/
│   ├── ingest/                 # PDF parsing & chunking
│   │   ├── pdf_parser.py       # PDF text extraction
│   │   ├── chunker.py          # Token-based chunking (512 tokens, 128 overlap)
│   │   └── pipeline.py         # Complete ingestion pipeline
│   ├── rag/                     # Retrieval & generation
│   │   ├── embedder.py         # Sentence transformer embeddings
│   │   ├── vector_store.py     # FAISS vector store
│   │   ├── build_index.py      # Index building pipeline
│   │   ├── retriever.py        # Dense (vector) retriever
│   │   ├── generator.py         # LLM answer generation with citations
│   │   ├── structured_citations.py  # Structured citations enhancement
│   │   ├── pipeline.py         # Complete RAG pipeline
│   │   └── logger.py           # Query logging system
│   └── eval/                    # Evaluation queries & metrics
│       ├── queries.json        # 20 evaluation queries (CEE, CSS, general)
│       ├── run_eval.py         # Run evaluation on all queries
│       ├── metrics.py          # LLM-based evaluation metrics
│       └── compare_baseline_enhanced.py  # Comparison script
├── logs/
│   └── query_logs.jsonl        # All queries logged (JSONL format)
├── outputs/                     # Evaluation results
│   ├── baseline_eval_results.jsonl
│   ├── baseline_eval_scores.csv
│   ├── baseline_eval_summary.json
│   ├── enhanced_eval_results.jsonl
│   ├── enhanced_eval_scores.csv
│   ├── enhanced_eval_summary.json
│   ├── baseline_enhanced_comparison.csv
│   ├── eval_report_data.json
│   └── representative_failure_cases.json
├── view_query_result.py        # Helper script to view query results
└── requirements.txt
```

## System Overview

**Domain:** Sleep patterns, quality, and impact on well-being

**Main Question:** How do different sleep factors (duration, quality, timing, consistency) affect physical health, mental well-being, and cognitive performance, and what interventions most effectively improve sleep outcomes?

**Corpus:** 16 peer-reviewed papers on sleep research (525 chunks total)

## Technical Architecture

### Ingestion Pipeline

**PDF Parsing:**
- Library: PyMuPDF (fitz)
- Text extraction with artifact cleaning
- Metadata extraction (title, author, page count)

**Text Chunking:**
- Strategy: Token-based sliding window
- Chunk size: 512 tokens (~384 words)
- Overlap: 128 tokens (~96 words, 25% overlap)
- Tokenizer: tiktoken (cl100k_base encoding)
- Output: JSONL format with chunk metadata

**Storage:**
- Processed text: `data/processed/{source_id}.txt`
- All chunks: `data/processed/chunks.jsonl`
- Ingestion report: `data/processed/ingestion_report.txt`

### Retrieval System

**Dense Retrieval (Baseline):**
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- Index: FAISS IndexFlatIP (Inner Product = cosine similarity)
- Normalization: All embeddings normalized for cosine similarity
- Top-k: 5 chunks per query

### Generation System

**Model:** GPT-4o-mini (OpenAI)

**Configuration:**
- Temperature: 0.1 (low for consistency)
- Prompt: Structured with role, constraints, citation requirements
- Citation format: `(source_id, chunk_id)`

**System Prompt Features:**
- Role-based: Research assistant specializing in sleep research
- Citation rules: Base every claim on evidence chunks
- Constraints: Only use explicit information, no fabrication
- Format requirements: Include statistics, direct quotes verbatim

**Output:**
- Answer with citations in `(source_id, chunk_id)` format
- Usage statistics (tokens, costs)
- Model and prompt version metadata

### Logging System

**Format:** JSONL (one entry per query)

**Logged Information:**
- Timestamp
- Query and answer
- Retrieved chunks (with similarity scores)
- Citations found in answer
- Model and prompt version
- Usage metadata (tokens)

**Location:** `logs/query_logs.jsonl`

## Citation System

Citations use format: `(source_id, chunk_id)`

Example: `(wang2025association, wang2025association_chunk_001)`

All citations resolve to:
1. `chunk_id` in `data/processed/chunks.jsonl` → exact text
2. `source_id` in `data/data_manifest.json` → paper metadata + DOI

**Verification:**
Use `view_query_result.py` to view complete query results with full chunk text:
```bash
python view_query_result.py [query_id]
```

## Evaluation

**Purpose:** The `outputs/` directory contains systematic evaluation results comparing baseline vs enhanced RAG systems across 20 test queries. This is used for:
- Measuring system performance (citation accuracy, groundedness, relevance)
- Comparing baseline vs enhanced modes
- Generating evaluation reports
- Identifying failure cases

**Quick Start - Full Evaluation Pipeline:**
```bash
# Step 1: Run baseline evaluation (runs all 20 queries)
python -m src.eval.run_eval

# Step 2: Score baseline results (calculates metrics)
python -m src.eval.metrics outputs/baseline_eval_results.jsonl

# Step 3: Run enhanced evaluation (runs all 20 queries with structured citations)
python -m src.eval.run_eval --enhanced

# Step 4: Score enhanced results
python -m src.eval.metrics outputs/enhanced_eval_results.jsonl

# Step 5: Compare both and generate report data
python -m src.eval.compare_baseline_enhanced
```

**What gets generated:**
- `baseline_eval_results.jsonl` - Raw results for all 20 queries (baseline mode)
- `baseline_eval_scores.csv` - Metrics for each query (citation precision, groundedness, relevance)
- `baseline_eval_summary.json` - Aggregate statistics
- `enhanced_eval_results.jsonl` - Raw results for all 20 queries (enhanced mode)
- `enhanced_eval_scores.csv` - Metrics for each query (enhanced mode)
- `enhanced_eval_summary.json` - Aggregate statistics
- `baseline_enhanced_comparison.csv` - Side-by-side comparison
- `eval_report_data.json` - Summary metrics for writing reports
- `representative_failure_cases.json` - 3 detailed failure cases for analysis

**Note:** `run_query.sh` is for **single queries** (testing/exploration). The evaluation scripts in `src/eval/` are for **systematic evaluation** across all test queries.

### Query Set

**Total:** 20 queries

**By Category:**
- 10 direct queries (factual questions)
- 5 synthesis queries (multi-source comparisons)
- 5 edge case queries (test missing evidence handling)

**By Phase 1 Task:**
- 6 CEE-pattern queries (Claim-Evidence-Extraction)
- 4 CSS-pattern queries (Cross-Source Synthesis)
- 10 general queries

**File:** `src/eval/queries.json`

### Metrics

**1. Citation Precision (Automated):**
- Checks if citations in answer exist in retrieved chunks
- Formula: valid_citations / total_citations
- Range: 0.0 to 1.0

**2. Groundedness (LLM-scored, 1-4 scale):**
- 4: All claims grounded in chunks; citations correct
- 3: Mostly grounded; minor issues
- 2: Some claims unsupported; vague citations
- 1: Hallucinations; fabricated citations
- Uses task-specific evaluation criteria (CEE, CSS, edge_case)

**3. Answer Relevance (LLM-scored, 1-4 scale):**
- 4: Directly answers query completely
- 3: Answers query; missing minor details
- 2: Partially answers; key gaps
- 1: Doesn't answer query
- Evaluates based on query type and expected format

**LLM Evaluation:**
- Uses GPT-4o-mini to automatically score groundedness and relevance
- Provides reasoning for each score
- Task-specific criteria for CEE, CSS, and edge case queries

### Running Evaluation

**Baseline Evaluation:**
```bash
# Run baseline evaluation
python -m src.eval.run_eval

# Score baseline results
python -m src.eval.metrics outputs/baseline_eval_results.jsonl
```

**Enhanced Evaluation (Structured Citations):**
```bash
# Run enhanced evaluation
python -m src.eval.run_eval --enhanced

# Score enhanced results
python -m src.eval.metrics outputs/enhanced_eval_results.jsonl
```

**Compare Baseline vs Enhanced:**
```bash
python -m src.eval.compare_baseline_enhanced
```

This generates:
- `outputs/baseline_enhanced_comparison.csv` - Detailed comparison
- `outputs/eval_report_data.json` - Summary metrics for report
- `outputs/representative_failure_cases.json` - 3 detailed failure cases

### Results Files

**Baseline:**
- `outputs/baseline_eval_results.jsonl` - All query results
- `outputs/baseline_eval_scores.csv` - Scored metrics
- `outputs/baseline_eval_summary.json` - Summary statistics

**Enhanced:**
- `outputs/enhanced_eval_results.jsonl` - All query results
- `outputs/enhanced_eval_scores.csv` - Scored metrics
- `outputs/enhanced_eval_summary.json` - Summary statistics

## Enhancement: Structured Citations

**Problem it solves:** Phase 1 showed citation inconsistency/hallucination was a major failure. The baseline system generates citations but doesn't validate them or provide reference lists.

**What it does:**
1. **Citation Validation:** Validates all citations in answer exist in retrieved chunks
2. **Reference List Generation:** Auto-generates formatted reference list from manifest
3. **Invalid Citation Detection:** Flags citations that don't match retrieved chunks

**Benefits:**
- Improved citation accuracy: catches invalid citations
- Better user experience: provides formatted reference list
- Enhanced transparency: shows which citations are valid

**Usage:**

Via command line:
```bash
# Enhanced mode
./run_query.sh "your query" enhanced
```

Via Python:
```python
# Use structured citations enhancement
pipeline = RAGPipeline()
result = pipeline.query("your query", k=5, enhance=True)

# Enhanced result includes:
# - citation_validation_passed: bool
# - invalid_citations: list
# - reference_list: str (formatted references)
# - num_unique_sources: int
```

**When to use each mode:**
- **Baseline**: Quick queries, testing, when you just need an answer
- **Enhanced**: When you need validated citations and a reference list, or want to catch citation errors
- **Both**: When comparing results or understanding the difference between modes

## Single Query vs Full Evaluation

**Single Query Testing** (`run_query.sh`):
- Purpose: Test individual queries, explore the system, quick checks
- Usage: `./run_query.sh "your query" [baseline|enhanced|both]`
- Output: Console output + logs to `logs/query_logs.jsonl`
- When to use: Development, debugging, exploring specific questions

**Full Evaluation** (`src/eval/` scripts):
- Purpose: Systematic evaluation across all 20 test queries
- Usage: See "Running Evaluation" section above
- Output: All files in `outputs/` directory
- When to use: Measuring overall system performance, generating reports, comparing modes

## Helper Scripts

**Single Command Query (Retrieval + Answer + Log):**
```bash
# Baseline mode (default) - Standard RAG pipeline
./run_query.sh "your query here"
./run_query.sh "your query here" baseline

# Enhanced mode - With structured citations (validation + reference list)
./run_query.sh "your query here" enhanced

# Compare both modes side-by-side
./run_query.sh "your query here" both

# Examples
./run_query.sh "How does sleep duration affect depression?"
./run_query.sh "How does sleep duration affect depression?" enhanced
./run_query.sh "How does sleep duration affect depression?" both
```

**What each mode does:**

1. **Baseline mode** (default):
   - Retrieves top-k relevant chunks
   - Generates answer with citations
   - Saves query to `logs/query_logs.jsonl`
   - Displays results with metadata

2. **Enhanced mode**:
   - Same as baseline, plus:
   - Validates all citations (checks if they exist in retrieved chunks)
   - Generates formatted reference list from manifest
   - Shows invalid citations if any are found
   - Displays number of unique sources cited

3. **Both mode**:
   - Runs both baseline and enhanced
   - Shows side-by-side comparison
   - Compares citation counts, validation status, and answer length
   - Useful for understanding the difference between modes

**View Query Result:**
```bash
# View any query result with full chunk text for verification
python view_query_result.py [query_id]

# View first result (default)
python view_query_result.py
```

**Compare Evaluations:**
```bash
# Compare baseline vs enhanced (structured citations)
python -m src.eval.compare_baseline_enhanced
```

## Dependencies

See `requirements.txt`:
- pymupdf - PDF parsing
- sentence-transformers - Embeddings
- faiss-cpu - Vector search
- pandas - Data manipulation
- numpy - Numerical operations
- python-dotenv - Environment variables
- openai - LLM API
- tiktoken - Tokenization

All tools are free/open-source except OpenAI API (requires API key).

## Citation Resolution

To verify a citation:
1. Extract `(source_id, chunk_id)` from answer
2. Find chunk in `data/processed/chunks.jsonl`:
   ```bash
   grep "\"chunk_id\": \"{chunk_id}\"" data/processed/chunks.jsonl
   ```
3. Find source metadata in `data/data_manifest.json`:
   ```bash
   grep "\"id\": \"{source_id}\"" data/data_manifest.json
   ```

## Evaluation Report Data

All data needed for the evaluation report is available in:
- `outputs/eval_report_data.json` - Summary metrics
- `outputs/baseline_enhanced_comparison.csv` - Detailed comparison
- `outputs/representative_failure_cases.json` - 3 failure cases with full details

Use these files to write the evaluation report with:
- Aggregate metrics comparison
- Category and Phase1 task breakdowns
- Failure case analysis with evidence
