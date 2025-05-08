type: feature
title: DSPy Dataset Expansion
description: Guidelines for expanding DSPy training datasets in the BibleScholarProject
globs:
  - "scripts/expand_dspy_training_data.py"
  - "scripts/split_dspy_dataset.py"
  - "train_dspy_bible_qa.py"
alwaysApply: false
---

# DSPy Dataset Expansion Guidelines

## Overview

This rule provides guidelines for expanding DSPy training datasets in the BibleScholarProject, focusing on:
1. Creating diverse examples for Bible QA models
2. Incorporating theological concepts 
3. Generating multi-turn conversations
4. Creating proper train/validation splits

## Dataset Types

The BibleScholarProject uses several dataset types for DSPy training:

1. **Single-Turn QA Examples**
   - Direct questions about Bible verses
   - Theological interpretation questions
   - Factual questions about Bible content

2. **Multi-Turn Conversation Examples**
   - Theological term definition followed by application
   - Verse meaning followed by implications
   - Comparative analysis of theological concepts

3. **Cross-Reference Examples**
   - Questions connecting multiple Bible passages
   - Thematic comparisons across verses
   - Theological connections between passages

4. **Theological Concept Examples**
   - Explanations of Hebrew/Greek terms
   - Questions about theological principles
   - Analysis of God's attributes in Scripture

## Data Sources

Primary data sources include:

1. **Bible Database**
   - Verses table (`bible.verses`)
   - Strong's dictionary (`bible.strongs_dictionary`)
   - Books reference (`bible.books`)

2. **Existing Datasets**
   - `theological_terms_dataset.jsonl`: 100+ Hebrew/Greek terms
   - `combined_bible_corpus_dataset.json`: 2000+ QA examples

3. **Fallback Mechanisms**
   - Hardcoded examples for database failure scenarios
   - Standard theological terms when database is unavailable
   - Common Bible verses (Genesis 1:1, John 3:16, etc.)

## Implementation Guidelines

### 1. Dataset Expansion

The DSPy dataset expansion script (`scripts/expand_dspy_training_data.py`) should follow these principles:

- **Theological Balance**: Ensure 60-70% of examples focus on theological concepts
- **Translation Diversity**: Include examples from multiple Bible translations
- **Question Variety**: Generate diverse question formulations using templates
- **Error Handling**: Include robust fallback mechanisms for database failures
- **Examples Per Type**:
  - Single-turn QA: 100+ examples
  - Multi-turn conversations: 50+ examples 
  - Cross-references: 50+ examples
  - Theological concepts: 50+ examples

Example of a well-formed theological question:
```json
{
  "question": "What is the meaning of Elohim (H430) in Genesis 1:1?",
  "context": "Genesis 1:1: In the beginning God created the heaven and the earth.",
  "answer": "In Genesis 1:1, Elohim (H430) refers to God, gods. The verse states: \"In the beginning God created the heaven and the earth.\""
}
```

### 2. Dataset Splitting

Datasets should be split using `scripts/split_dspy_dataset.py` with the following guidelines:

- **Train/Validation Ratio**: 80% training, 20% validation by default
- **Random Seed**: Use a fixed random seed (42) for reproducibility
- **Stratification**: Ensure theological concepts are represented in both splits
- **Format**: Save splits in JSON format for compatibility with train_dspy_bible_qa.py
- **Naming Conventions**: Use `_train.json` and `_val.json` suffixes

### 3. Training Parameters

When training with the expanded dataset:

- **Optimizer**: Use `bootstrap` for most cases, `simba` for complex examples
- **Max Demos**: 5-8 demonstrations for theological questions
- **Model Selection**: Mistral-based models preferred for theological understanding
- **MLflow Tracking**: Always use MLflow experiment tracking to compare versions
- **Evaluation Metrics**: Track accuracy, but also theological correctness

## Implementation Example

1. **Expand Dataset**:
```bash
python scripts/expand_dspy_training_data.py --output-file data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset.json
```

2. **Split Dataset**:
```bash
python scripts/split_dspy_dataset.py --input-file data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset.json
```

3. **Train Model**:
```bash
python train_dspy_bible_qa.py --lm-studio --optimizer bootstrap --data-dir data/processed/dspy_training_data/bible_corpus/dspy/
```

## Best Practices

1. **Always check MLflow UI** (http://localhost:5000) to compare runs with different dataset expansions
2. **Version your datasets** with date or version number
3. **Document enhancements** made to each dataset expansion iteration
4. **Review example quality** periodically for theological accuracy
5. **Test with multiple model types** to gauge dataset versatility

## Common Issues

1. **Database Connection Failures**: Use hardcoded examples as fallback
2. **Example Duplication**: Use unique question checking to avoid duplicates
3. **Output Format Inconsistency**: Standardize answer formatting in templates
4. **Theological Accuracy**: Verify theological statements against reference works
5. **Context Length**: Keep contexts concise for model token limits 