# Enterprise RAG Evaluation

This directory contains evaluation scripts and results for the Enterprise RAG system.

## Quick Start

### Run Single Evaluation
```bash
python scripts/evaluate_rag.py --mode single --domain enterprise
```

### Compare Engine Performance
```bash
python scripts/evaluate_rag.py --mode compare --domain enterprise
```

### Continuous Monitoring
```bash
python scripts/evaluate_rag.py --mode continuous --interval 24
```

## Evaluation Metrics

The system uses RAGAS to evaluate the following metrics:

- **Faithfulness**: Factual consistency of the answer with retrieved contexts
- **Answer Relevancy**: Relevance of the generated answer to the question
- **Context Precision**: Precision of retrieved contexts
- **Context Recall**: Recall of relevant contexts
- **Context Entity Recall**: Recall of entities in contexts
- **Answer Correctness**: Overall correctness of the answer

## Quality Thresholds

- Faithfulness: ≥ 0.8
- Answer Relevancy: ≥ 0.7
- Context Precision: ≥ 0.8
- Context Recall: ≥ 0.7

## Custom Test Queries

Create a JSON file with custom test queries:

```json
[
  {
    "question": "What is the company's remote work policy?",
    "ground_truth": "The company allows remote work up to 3 days per week...",
    "contexts": ["Relevant document excerpt 1", "Relevant document excerpt 2"]
  }
]
```

Run with custom queries:
```bash
python scripts/evaluate_rag.py --queries custom_queries.json
```

## Results

Evaluation results are saved in the `evaluations/` directory with timestamp:
- `evaluation_results_YYYYMMDD_HHMMSS.json`

## API Endpoints

- `POST /evaluate` - Run single evaluation
- `GET /evaluate/compare` - Compare engine performance