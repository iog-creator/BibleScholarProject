# External Bible Datasets Integration

This document describes the process of integrating external Bible datasets with the BibleScholarProject for enhanced theological question answering.

## Overview

The external dataset integration pipeline enhances our Bible QA system by incorporating diverse sources of theological and linguistic data from external repositories, alongside our own database content.

### Key Components

1. **External Dataset Fetcher** (`scripts/fetch_external_bible_datasets.py`)
   - Downloads and processes multiple Bible datasets from online sources
   - Converts raw data into standardized QA pairs for DSPy training
   - Focuses on theological terms, multilingual resources, and cross-references

2. **Dataset Integrator** (`scripts/integrate_external_datasets.py`)
   - Combines external datasets with our internal theological database
   - Adds theological term definitions, cross-language examples, and more
   - Creates a comprehensive, integrated training dataset

3. **Full Integration Pipeline** (`scripts/run_full_dataset_integration.py`)
   - Orchestrates the complete workflow from fetching to integration to training
   - Provides command-line options for customizing the process
   - Logs detailed information throughout the process

## Supported External Datasets

| Dataset | Description | Source |
|---------|-------------|--------|
| Strong's Dictionary | Hebrew and Greek lexical definitions | [openscriptures/strongs (GitHub)](https://github.com/openscriptures/strongs) |
| World English Bible | Public domain Bible translation | [thiagobodruk/bible (GitHub)](https://github.com/thiagobodruk/bible) |
| STEP Bible Data | STEP Bible lexicons and morphology | [STEPBible-Data (GitHub)](https://github.com/STEPBible/STEPBible-Data) |
| Bible NLP Corpus | Parallel Bible text in 833+ languages | [biblenlp-corpus (HuggingFace)](https://huggingface.co/datasets/bible-nlp/biblenlp-corpus) |
| Open Hebrew Bible | BHS with Strong's numbers and lexicons | [OpenHebrewBible (GitHub)](https://github.com/eliranwong/OpenHebrewBible) |

## Types of Data Generated

1. **Theological Term QA Pairs**
   - Hebrew and Greek word definitions with Strong's numbers
   - Theological significance of important biblical terms
   - Etymology and usage statistics

2. **Cross-Language Connections**
   - Translation pairs between English, Hebrew, Greek, and Arabic
   - Comparisons between different Bible translations
   - Cultural and linguistic insights

3. **Interlinear and Morphological Data**
   - Word-by-word translations with original languages
   - Grammatical analysis and parsing information
   - Word origins and semantic meanings

## Usage

### Full Pipeline Execution

Run the complete pipeline with a single command:

```bash
python scripts/run_full_dataset_integration.py
```

Options:
- `--skip-fetch`: Skip downloading external datasets (use existing data)
- `--skip-integrate`: Skip integration step (only download data)
- `--train`: Run DSPy training after integration

### Individual Component Execution

1. **Fetch External Datasets Only**:
   ```bash
   python scripts/fetch_external_bible_datasets.py
   ```

2. **Integrate Datasets Only**:
   ```bash
   python scripts/integrate_external_datasets.py
   ```

3. **Train with Integrated Data**:
   ```bash
   python train_dspy_bible_qa.py --use-integrated-data
   ```

## Directory Structure

```
data/
  ├── processed/
  │   └── dspy_training_data/
  │       ├── bible_corpus/           # Original training data
  │       ├── external/               # Downloaded external datasets
  │       └── integrated/             # Combined dataset for training
  │           ├── combined_training_data.jsonl
  │           └── dataset_summary.json
  └── raw/
      └── external_datasets/          # Raw downloaded files
```

## Data Formats

All data is stored in JSONL format with the following structure:

```json
{
  "question": "What is the meaning of the Hebrew word 'shalom'?",
  "answer": "The Hebrew word 'shalom' means peace, completeness, and wellness.",
  "context": "Strong's: H7965, Hebrew: שָׁלוֹם, Transliteration: shalom, Definition: peace, completeness, welfare",
  "metadata": {
    "source": "open_hebrew_bible",
    "type": "lexical",
    "strongs_id": "H7965"
  }
}
```

## Integration with DSPy Training

The integrated dataset is used by the DSPy training pipeline to enhance model capabilities:

1. Increased diversity of theological questions and answers
2. Better understanding of Hebrew and Greek terms
3. Improved multilingual capabilities
4. Enhanced morphological and lexical knowledge

### Using the Integrated Data for Training

To train a DSPy Bible QA model with the integrated dataset:

```bash
python train_dspy_bible_qa.py --use-integrated-data --optimizer bootstrap --model "google/flan-t5-small"
```

The `--use-integrated-data` flag instructs the training script to use the integrated dataset instead of the default one.

### Available DSPy Models

The `src/dspy_programs/bible_qa.py` module provides multiple DSPy models for Bible QA:

1. **Basic Bible QA** (`BibleQA`): Simple question-answering
2. **Bible QA with History** (`BibleQAWithHistory`): Supports conversation history
3. **Theological Term Analyzer** (`TheologicalTermAnalyzer`): Specializes in theological term analysis
4. **Theological Bible QA** (`TheologicalBibleQA`): Multi-hop reasoning for complex questions
5. **Integrated Bible QA** (`IntegratedBibleQA`): Combined system with all features

To create and use a model:

```python
from src.dspy_programs.bible_qa import create_bible_qa_model

# Create an integrated model
model = create_bible_qa_model("integrated")

# Ask a question
result = model(
    question="What is the theological significance of the Hebrew term 'shalom'?",
    context=""
)

print(result.answer)
```

## Examples of Enhanced Capabilities

The integrated dataset enables the following enhanced capabilities:

### 1. Theological Term Analysis

```
Q: What is the meaning of the Hebrew word 'shalom' (Strong's H7965)?
A: The Hebrew word 'shalom' (Strong's H7965) means peace, completeness, welfare, and wholeness. 
   It encompasses a sense of totality and well-being that extends beyond merely the absence of conflict.
```

### 2. Cross-Translation Comparison

```
Q: How do different translations render John 3:16?
A: Different Bible translations vary in how they render John 3:16. The KJV uses "For God so loved the world, 
   that he gave his only begotten Son..." while the NIV uses "For God so loved the world that he gave his 
   one and only Son..." The WEB translation says "For God so loved the world, that he gave his one and only Son..."
```

### 3. Complex Theological Reasoning

```
Q: How does the concept of grace in the New Testament relate to covenant theology in the Old Testament?
A: [Multi-step reasoning followed by comprehensive answer linking Old Testament covenant concepts with 
   New Testament grace through progressive revelation]
```

## Troubleshooting

If you encounter issues with the dataset integration:

1. Check `logs/dataset_fetcher.log` for details on dataset download issues
2. Check `logs/dataset_integration.log` for integration errors
3. Ensure all required Python packages are installed
4. Verify that the PostgreSQL database is running and accessible

### Common Issues and Solutions

1. **404 Errors When Downloading Datasets**:
   - Check if the source URLs in the fetcher script are still valid
   - Try running with just one dataset by modifying the `datasets` dictionary

2. **JSON Parsing Errors**:
   - Some external datasets may have formatting issues
   - Check the raw data and modify the parsing logic if needed

3. **Database Connection Issues**:
   - Verify that the database credentials in `.env` are correct
   - Ensure the PostgreSQL server is running

## Extending the System

To add new external datasets:

1. Add a new entry to the `datasets` dictionary in `fetch_external_bible_datasets.py`
2. Implement a custom processing function for the new dataset
3. Run the fetcher to download and process the new dataset
4. The integration pipeline will automatically include the new data

## References

For more information on the Bible QA system architecture, please see:
- `README_DSPY.md`: Information about the DSPy framework and training
- `README_VECTOR_SEARCH.md`: Details on the semantic search capabilities
- `README_BIBLE_CORPUS.md`: Documentation on the internal Bible corpus 