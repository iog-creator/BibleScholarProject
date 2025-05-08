# Bible Corpus Dataset for DSPy Training

## Overview

We have successfully created a Bible corpus dataset as a non-synthetic training data source for the Bible Scholar Project. This dataset contains 31 examples with well-structured question-answer pairs based on Bible verses, lexicon entries, and theological terms.

## Dataset Structure

The dataset has the following characteristics:

- **Example Count**: 31 examples
- **Fields**: context, question, answer, metadata (and occasionally history)
- **Question Types**:
  - Verse content questions (10 examples)
  - Definition questions (6 examples)
  - Other types (15 examples)
- **Content Types**:
  - Bible verses (15 examples)
  - Lexicon entries (5 examples)
  - Theological terms (5 examples)

## Sample Example

```json
{
  "question": "What does Genesis 1:1 say?",
  "answer": "In the beginning God created the heaven and the earth.",
  "context": "Genesis 1:1: In the beginning God created the heaven and the earth.",
  "metadata": {
    "source": "verse_content",
    "reference": "Genesis 1:1",
    "book": "Genesis",
    "chapter": 1,
    "verse": 1,
    "translation": "KJV"
  }
}
```

## Current Implementation

The dataset is generated using the `scripts/create_sample_bible_dataset.py` script, which creates a variety of question-answer pairs based on Bible content. The dataset is saved at:

```
data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json
```

## Recommendations for DSPy Integration

1. **Increase Dataset Size**: The current dataset is small (31 examples). For more robust training, consider expanding it to at least 100-200 examples.

2. **Diversify Content Types**: Add more examples from different Bible books, more lexicon entries with theological significance, and a wider variety of question types.

3. **DSPy Training Pipeline Modifications**:
   - When using the dataset, ensure proper input/output field mapping (context, question → answer)
   - Use simpler DSPy training approaches while resolving API integration issues:
     - For API-based models: Use `dspy.BootstrapFewShot` with a small number of examples
     - For local testing: Create a simplified training pipeline with a mock LM for development

4. **Handling API Authentication**: To use OpenAI models, ensure the `.env.dspy` file contains the necessary API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ```

5. **Training Approach**:
   - Start with a simpler model like `dspy.ChainOfThought(BibleQA)` 
   - Use a consistent metric for evaluation (e.g., substring matching)
   - Start with fewer examples and simpler optimization before scaling up

## Next Steps

1. **Fix API Authentication**: Set up proper API keys for LLM access
2. **Expand the Dataset**: Generate more and diverse examples
3. **Test with Local LLMs**: Consider integrating with locally hosted models (e.g., Ollama)
4. **Create Evaluation Dataset**: Develop a separate evaluation set with challenging theological questions
5. **Document Integration Points**: Update the project documentation with details on how to use this non-synthetic dataset

## Usage Example

To use the Bible corpus dataset for training:

```python
import dspy

# Load the dataset
with open("data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json", "r") as f:
    data = json.load(f)

# Convert to DSPy examples
examples = [
    dspy.Example(
        context=item["context"],
        question=item["question"],
        answer=item["answer"]
    ).with_inputs("context", "question")
    for item in data
]

# Define a simple model and optimizer
model = dspy.ChainOfThought("context, question -> answer")
optimizer = dspy.BootstrapFewShot(metric=simple_accuracy_metric)

# Train and evaluate
compiled_model = optimizer.compile(model, trainset=examples)
```

By following these recommendations, we can effectively integrate this non-synthetic Bible corpus dataset into the DSPy training pipeline, improving the quality and theological accuracy of the Bible Scholar Project's question-answering capabilities. 