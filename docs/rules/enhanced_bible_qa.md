type: feature
title: Enhanced Bible QA with Database Verification
description: Guidelines for working with the Enhanced Bible QA system that combines DSPy models with Bible database verification
globs:
  - "src/dspy_programs/enhanced_bible_qa.py"
  - "test_enhanced_bible_qa.py"
alwaysApply: false
---

# Enhanced Bible QA with Database Verification

## Overview

This rule provides guidelines for the Enhanced Bible QA system, which combines DSPy-optimized models with direct Bible database lookups for improved accuracy. The system verifies model-generated answers against the Bible database to ensure theological and factual correctness.

## Core Components

### 1. Multi-Stage Pipeline

The Enhanced Bible QA system uses a multi-stage pipeline:

1. **Reference Extraction**: Identifies Bible references in questions
2. **Theological Term Extraction**: Identifies Hebrew/Greek terms and theological concepts
3. **Database Lookup**: Retrieves relevant verses and term definitions
4. **Semantic Search**: Finds semantically related verses for questions without specific references
5. **DSPy Answer Generation**: Generates answers using optimized DSPy models
6. **Database Verification**: Verifies answers against database content
7. **MLflow Tracking**: Records metrics and artifacts for model improvement

### 2. DSPy Signatures

The system defines several DSPy signatures:

```python
class BibleReferenceExtractor(dspy.Signature):
    """Extract Bible references from a question."""
    question = dspy.InputField(desc="The question about the Bible")
    references = dspy.OutputField(desc="List of Bible references mentioned in the question")
    requires_lookup = dspy.OutputField(desc="Whether the question requires looking up verses")

class TheologicalTermExtractor(dspy.Signature):
    """Extract theological terms from a question."""
    question = dspy.InputField(desc="The question about the Bible")
    theological_terms = dspy.OutputField(desc="List of theological terms in the question")
    hebrew_terms = dspy.OutputField(desc="List of Hebrew terms with Strong's numbers")

class BibleQA(dspy.Signature):
    """Answer questions about the Bible with DB-verified responses."""
    question = dspy.InputField(desc="The question about the Bible")
    context = dspy.InputField(desc="Bible verses and information relevant to the question")
    theological_terms = dspy.InputField(desc="Theological terms relevant to the question")
    answer = dspy.OutputField(desc="Precise, factual answer to the question based on the Bible")

class DatabaseVerifier(dspy.Signature):
    """Verify if an answer is consistent with the Bible database."""
    question = dspy.InputField(desc="The original question")
    proposed_answer = dspy.InputField(desc="The proposed answer to verify")
    database_context = dspy.InputField(desc="Relevant information from the Bible database")
    is_consistent = dspy.OutputField(desc="Whether the answer is consistent with the database")
    corrected_answer = dspy.OutputField(desc="Corrected answer if inconsistent")
    explanation = dspy.OutputField(desc="Explanation of consistency check")
```

### 3. Database Integration

The system integrates with the Bible database through:

1. **Direct Verse Lookup**: Retrieves verses by reference (book, chapter, verse)
2. **Theological Term Lookup**: Looks up Strong's dictionary entries
3. **Semantic Search**: Uses pgvector to find semantically related verses

### 4. Example Utilization

The system leverages examples from multiple datasets:

1. **Combined Bible Corpus Dataset**: 2000+ QA examples
2. **Theological Terms Dataset**: 100+ theological term examples
3. **Few-Shot Learning**: Bootstrap optimization with selected examples

## Usage Guidelines

### Basic Usage

```python
from src.dspy_programs.enhanced_bible_qa import EnhancedBibleQA

# Create an instance with default settings
qa_system = EnhancedBibleQA()

# Answer a question
result = qa_system.answer("What does Genesis 1:1 say?")
print(result["answer"])

# Use a specific Bible translation
result = qa_system.answer("What does John 3:16 say?", translation="ASV")
```

### Command-Line Usage

```bash
# Answer a specific question
python test_enhanced_bible_qa.py --question "What does Genesis 1:1 say?" --translation KJV

# Run a batch test with sample questions
python test_enhanced_bible_qa.py --batch-test --use-lm-studio --output-file results.json

# Apply optimizers for improved performance
python test_enhanced_bible_qa.py --question "What is the meaning of Elohim?" --optimize
```

### Using with LM Studio

```python
# Create an instance using LM Studio
qa_system = EnhancedBibleQA(use_lm_studio=True)

# LM Studio with specific model path
qa_system = EnhancedBibleQA(use_lm_studio=True, model_path="models/dspy/bible_qa_t5_latest")
```

## Database Schema Requirements

The system expects the following database schema:

1. **bible.verses** table:
   - `book_name`: Name of the Bible book
   - `chapter_num`: Chapter number
   - `verse_num`: Verse number
   - `verse_text`: Text of the verse
   - `translation_source`: Bible translation identifier

2. **bible.strongs_dictionary** table:
   - `strongs_id`: Strong's number (e.g., "H430")
   - `term`: Original language term
   - `transliteration`: Transliteration to English
   - `definition`: Definition of the term

3. **bible.verse_embeddings** table:
   - Used for semantic search
   - Requires pgvector extension

## Example Workflow

1. **Question Processing**:
   ```python
   # Extract Bible references
   reference_result = reference_extractor(question="What does Genesis 1:1 say?")
   references = reference_result.references  # ["Genesis 1:1"]
   
   # Extract theological terms
   term_result = term_extractor(question="What is the meaning of Elohim in Genesis 1:1?")
   theological_terms = term_result.theological_terms  # ["Elohim"]
   hebrew_terms = term_result.hebrew_terms  # ["H430 (Elohim)"]
   ```

2. **Database Lookup**:
   ```python
   # Look up specific verses
   verse_context = _look_up_verses(["Genesis 1:1"], translation="KJV")
   # Result: "Genesis 1:1: In the beginning God created the heaven and the earth."
   
   # Look up theological terms
   term_context = _get_theological_terms(["H430 (Elohim)"])
   # Result: "H430 (Elohim): God, gods"
   ```

3. **Answer Generation and Verification**:
   ```python
   # Generate answer
   qa_result = qa_module(question=question, context=context, theological_terms=term_context)
   proposed_answer = qa_result.answer
   
   # Verify against database
   verification = verifier(question=question, proposed_answer=proposed_answer, database_context=context)
   
   # Determine final answer
   final_answer = proposed_answer
   if not verification.is_consistent:
       final_answer = verification.corrected_answer
   ```

## Optimizer Configuration

The system supports DSPy optimizers for improved performance:

```python
from src.dspy_programs.enhanced_bible_qa import EnhancedBibleQA, configure_optimizers

# Create the QA system
qa_system = EnhancedBibleQA()

# Apply optimizers
qa_system = configure_optimizers(qa_system)
```

Available optimizers:

1. **BootstrapFewShot**: Uses existing examples to optimize prompt construction
2. **GRPO**: Gradient-based optimization
3. **SIMBA**: Optimization through parameter search

## MLflow Integration

The system records metrics and artifacts with MLflow:

```python
with mlflow.start_run(run_name="bible_qa_inference"):
    mlflow.log_param("question", question)
    mlflow.log_param("translation", translation)
    mlflow.log_metric("references_found", len(references))
    mlflow.log_metric("theological_terms_found", len(all_terms))
    mlflow.log_metric("answer_verified", 0 if answer_changed else 1)
    
    # Log artifacts
    with open("logs/temp_context.txt", "w", encoding="utf-8") as f:
        f.write(context)
    mlflow.log_artifact("logs/temp_context.txt")
```

Access MLflow UI to view results:

```bash
mlflow ui
# Access at http://localhost:5000
```

## Output Format

The system returns a dictionary with:

```python
{
    "question": "What does Genesis 1:1 say?",
    "answer": "In the beginning God created the heaven and the earth.",
    "references": ["Genesis 1:1"],
    "theological_terms": ["H430 (Elohim)"],
    "context": "Genesis 1:1: In the beginning God created the heaven and the earth.\n\nTheological terms:\nH430 (Elohim): God, gods",
    "proposed_answer": "Genesis 1:1 says, 'In the beginning God created the heaven and the earth.'",
    "verification": {
        "is_consistent": True,
        "explanation": "The answer is consistent with the Bible verse Genesis 1:1."
    }
}
```

## Error Handling

The system implements robust error handling:

1. **Database Connection Errors**:
   - Attempts to reconnect using connection string
   - Logs detailed error information

2. **Reference Parsing Errors**:
   - Falls back to semantic search if reference parsing fails
   - Logs parsing errors for future improvement

3. **Model Generation Errors**:
   - Captures and logs model errors
   - Provides graceful degradation

## Performance Considerations

1. **Caching**:
   - Database connections are cached
   - Loaded examples are cached

2. **Batch Processing**:
   - Process multiple questions efficiently with batching
   - Use `--batch-test` for testing multiple questions

3. **Optimization**:
   - Use the `--optimize` flag to apply DSPy optimizers
   - Bootstrap optimization uses existing examples for few-shot learning

## Best Practices

1. **Question Formulation**:
   - Include specific Bible references when possible
   - Use standard book names and chapter/verse notation
   - Mention theological terms explicitly for better recognition

2. **Translation Selection**:
   - Specify the translation for consistent results
   - KJV is used by default
   - ASV, WEB, and other public domain translations are supported

3. **Theological Term Handling**:
   - Use Strong's numbers when available (e.g., "H430")
   - Use transliterated forms (e.g., "Elohim")
   - Provide context for ambiguous terms

4. **Database Verification**:
   - Always verify factual claims against the database
   - Check theological interpretations for consistency with source texts
   - Log verification results for continual improvement

## Implementation Details

Main implementation files:

- `src/dspy_programs/enhanced_bible_qa.py` - Core implementation
- `test_enhanced_bible_qa.py` - Testing script
- `docs/rules/enhanced_bible_qa.md` - Documentation 