---
title: Non-Synthetic Bible QA Training Workflow
category: Guides
tags: ["Bible QA", "DSPy", "Training", "Non-Synthetic Data", "Evaluation"]
---
# Non-Synthetic Bible QA Training

This document outlines the approach for improving Bible QA using non-synthetic training data, which has shown significant improvements over synthetically generated data.

## Overview

Our Bible QA system has shown significant improvement when using non-synthetic data (specifically the Bible trivia dataset) compared to synthetic data:

- **Accuracy improvement**: Exact match accuracy improved from ~5% to ~30% (6x improvement)
- **Answer quality**: More precise answers with correct scripture references
- **Few-shot learning**: Better results with 3-5 examples rather than more examples

This document outlines the tools and processes for further improving these results.

## Scripts

### 1. Consolidate and Expand Q&A Datasets (`scripts/data/expand_bible_trivia_dataset.py`)

This script processes and consolidates Q&A datasets from various formats, adds metadata, deduplicates, and prepares them for training. It can currently handle Alpaca-style JSONL (instruction/response) and MushroomGecko-style JSONL (multiple-choice) formats.

**Example Usage:**

```bash
# Process specific Alpaca and MushroomGecko files, save to a custom output
python scripts/data/expand_bible_trivia_dataset.py \
    --alpaca_input data/processed/dspy_training_data/qa_bible_trivia_alpaca.jsonl \
    --mushroomgecko_input data/processed/dspy_training_data/qa_mushroomgecko_bible.jsonl \
    --output data/processed/dspy_training_data/qa_bible_consolidated_custom.jsonl

# Process default files (qa_bible_trivia_alpaca.jsonl and qa_mushroomgecko_bible.jsonl from data/processed/dspy_training_data/)
# and save to default output (qa_bible_consolidated.jsonl in data/processed/dspy_training_data/)
python scripts/data/expand_bible_trivia_dataset.py
```

**Key Features:**
- Loads Alpaca-style Q&A data (`{"instruction": ..., "response": ...}`).
- Loads and transforms MushroomGecko multiple-choice Q&A data to instruction/response format.
- Combines data from specified sources.
- Adds metadata: 
    - Heuristic question type classification (factual, theological, general).
    - Extracts Bible references from answers.
    - Preserves original source and category for transformed data.
- Deduplicates questions (case-insensitive) from the combined dataset.
- Saves the consolidated and enriched dataset in Alpaca-style JSONL format.

### 2. Optimize Few-Shot Example Count (`scripts/tuning/optimize_bible_qa_examples.py`)

This script systematically evaluates different few-shot example counts to find the optimal configuration:

```bash
python scripts/tuning/optimize_bible_qa_examples.py [--input PATH_TO_DATASET] [--example-range 1-10] [--max-eval 20]
```

Features:
- Tests various few-shot example counts (default: 1-10)
- Evaluates performance on a test set
- Generates performance charts for exact and partial match accuracy
- Identifies the optimal number of examples for few-shot learning

### 3. Enhanced Theological Evaluation (`scripts/evaluation/evaluate_bible_qa_theology.py`)

This script provides enhanced evaluation metrics specifically for theological accuracy:

```bash
python scripts/evaluation/evaluate_bible_qa_theology.py [--input PATH_TO_RESULTS] [--output OUTPUT_REPORT]
```

Features:
- Evaluates accuracy of scripture references
- Assesses theological concept accuracy
- Categorizes questions by type (factual, theological, interpretive)
- Generates detailed reports with specialized metrics

## Workflow

1. **Expand Dataset**: First, run the dataset expansion script to enrich the existing dataset with metadata.

2. **Optimize Examples**: Run the optimization script to find the ideal number of few-shot examples.

3. **Evaluate Results**: Use the theological evaluation script to assess performance with domain-specific metrics.

4. **Update Model**: Incorporate the findings into the production Bible QA model.

## Performance Metrics

Our evaluation now includes the following metrics:

- **Exact Match Accuracy**: Direct string match between predicted and expected answer
- **Partial Match Accuracy**: Significant word overlap between prediction and expected answer
- **Theological Accuracy**: Accuracy in answering theological questions
- **Reference Accuracy**: Correctness of scripture references in answers
- **Overall Accuracy**: Combined metric weighted by question type

## Future Work

1. **Larger Dataset**: Continue expanding non-synthetic Bible trivia with high-quality human annotations
2. **Reference Validation**: Implement verification of scripture references against Bible text
3. **Specialized Models**: Train separate models for different question types (factual vs. theological)
4. **Context Integration**: Improve how scripture context is incorporated into answers

## Results Comparison

| Model Configuration | Exact Match | Theological Accuracy | Reference Accuracy |
|---------------------|-------------|----------------------|-------------------|
| Synthetic Data Only | ~5%         | Not measured         | Not measured      |
| Non-Synthetic (3-shot) | ~30%     | ~40%                | ~45%              |
| Target (Future)     | >50%        | >70%                 | >80%              |

## Requirements

- Python 3.8+
- DSPy framework
- matplotlib (for visualization)
- tqdm (for progress bars)
- Access to LLM API (locally or remote) 