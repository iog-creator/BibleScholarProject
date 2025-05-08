# DSPy 2.6 Usage in BibleScholarProject

This documentation covers the DSPy 2.6 features implemented in the BibleScholarProject, including multi-turn conversation support, enhanced optimizers, MLflow integration, and theological assertions.

## Overview

DSPy 2.6 introduces several important features that improve the Bible QA system:

1. **Multi-turn conversation support**: The system now maintains conversation history and considers previous interactions when answering questions.
2. **Enhanced optimizers**: The GRPO and SIMBA optimizers provide better training results than previous methods.
3. **MLflow integration**: Training runs are tracked with MLflow for better experiment tracking and model comparison.
4. **Assertion-based backtracking**: Theological assertions ensure that answers maintain doctrinal accuracy.

## Components

The DSPy 2.6 implementation includes the following components:

- `src/dspy_programs/bible_qa_dspy26.py`: Main DSPy training module with multi-turn support
- `test_bible_qa_dspy26.py`: Test script for the enhanced model
- `train_and_test_dspy26.bat`: Batch script for training and testing
- `src/api/dspy_api.py`: API endpoints with conversation history support

## Training Process

The training process leverages the existing DSPy training data with added conversation history support:

1. Data is loaded from the `data/processed/dspy_training_data/bible_corpus/dspy` directory
2. The BibleQAModule includes conversation history in its signature
3. The GRPO optimizer is used by default for better prompt optimization
4. MLflow tracks the training process and stores metrics
5. Models are saved in the `models/dspy` directory

### Multi-turn Conversation

The key enhancement is support for multi-turn conversations. This is implemented through:

- A history parameter in the BibleQASignature
- Formatting of history in the BibleQAModule.forward method
- Conversation history tracking in the API

Here's a simplified example of the signature:

```python
class BibleQASignature(dspy.Signature):
    """Signature for Bible Question Answering that supports conversation history."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns as a list of questions and answers", default=[])
    answer = dspy.OutputField(desc="Answer to the question based on the biblical context")
```

## Theological Assertions

To ensure theological accuracy, the model uses DSPy's assertion mechanism to enforce certain constraints:

```python
# Add theological assertions
if "god" in question.lower() and "god" not in prediction.answer.lower():
    # Check if an assertion about God should be made
    dspy.Assert(
        "god" in prediction.answer.lower(),
        "Answer must reference God when questions are about God."
    )
```

These assertions help ensure that answers maintain doctrinal accuracy, especially for important theological concepts.

## API Usage

The enhanced API includes support for conversation history:

### Ask a Question with History

```http
POST /api/dspy/ask
Content-Type: application/json

{
    "question": "Who was Moses?",
    "session_id": "user-123"
}
```

The API will maintain conversation history for the specified session and use it for context in follow-up questions.

### Ask with Bible Context

```http
POST /api/dspy/ask_with_context
Content-Type: application/json

{
    "question": "What did Moses do?",
    "context": "Moses led the Israelites out of Egypt across the Red Sea.",
    "session_id": "user-123"
}
```

### Get Conversation History

```http
GET /api/dspy/conversation?session_id=user-123
```

Returns the full conversation history for the specified session.

### Clear Conversation History

```http
DELETE /api/dspy/conversation?session_id=user-123
```

Clears the conversation history for the specified session.

## MLflow Integration

Training and API usage are tracked with MLflow, which can be accessed at http://localhost:5000 after starting:

```bash
mlflow ui --port 5000
```

The MLflow dashboard shows:
- Training parameters
- Model performance metrics
- API usage statistics
- Conversation history metrics

## Testing the Model

The test script `test_bible_qa_dspy26.py` provides two modes:

1. **Standard testing**: Tests the model with predefined examples
2. **Interactive mode**: Allows interactive conversations with the model

To test the model:

```bash
# Standard testing
python test_bible_qa_dspy26.py --model-path models/dspy/bible_qa_t5_latest

# Interactive conversation
python test_bible_qa_dspy26.py --conversation
```

## Training a New Model

To train a new model with DSPy 2.6 features:

```bash
# Train with default settings
train_and_test_dspy26.bat

# Specify teacher model category
train_and_test_dspy26.bat --teacher highest

# Specify student model
train_and_test_dspy26.bat --student google/flan-t5-base

# Specify optimizer 
train_and_test_dspy26.bat --optimizer simba
```

## Troubleshooting

Common issues and their solutions:

1. **Model loading errors**: Check that the model directory exists and contains `.dspy` files
2. **API initialization errors**: Ensure that the required DSPy modules are available
3. **MLflow connection issues**: Verify that MLflow is installed and running
4. **Conversation history not working**: Check that session IDs are being passed correctly

## Resources

- [DSPy Documentation](https://dspy.ai/)
- [DSPy Tutorials](https://dspy.ai/tutorials/rag/)
- [DSPy GitHub Repository](https://github.com/stanfordnlp/dspy)

## Hugging Face Integration

BibleScholarProject uses Hugging Face models for DSPy training and inference. We've implemented a complete integration that handles model selection, API access, and DSPy configuration.

### Setup

The integration requires a Hugging Face API token. Add it to your `.env` file:

```
HF_API_TOKEN=your_token_here
```

Run the setup script to configure the integration:

```bash
python scripts/setup_huggingface_dspy.py
```

This will:
1. Test connectivity to recommended models
2. Select the best models for your account
3. Create configuration files for DSPy

### Testing

Verify the integration with the test script:

```bash
python scripts/test_dspy_huggingface.py
```

This runs several tests:
- Basic verse completion
- Bible question answering
- Embedding generation and similarity

### Model Categories

We use three types of models:

1. **Embedding Models** - Generate vector embeddings for text
   - Default: `sentence-transformers/all-MiniLM-L6-v2`
   - Used for semantic search and retrieval

2. **Completion Models** - Text generation and instruction following
   - Default: `mistralai/Mistral-7B-Instruct-v0.2`
   - Used for DSPy module execution 

3. **Optimizer Models** - Optimize DSPy programs
   - Default: `meta-llama/Llama-2-7b-chat-hf`
   - Used for trace optimization

### Usage in Code

Import the initialization module in your scripts:

```python
from src.utils.dspy_hf_init import initialize_dspy

# Initialize with Hugging Face models
initialize_dspy()

# Now use DSPy as normal
import dspy
module = dspy.Predict(MySignature)
```

For more details, see the [Hugging Face DSPy Integration](../.cursor/rules/features/huggingface_dspy_integration.mdc) rule.

## Structured Output Schema for Retriever API

The retriever API now returns results from all major data sources in the `bible_db` in a unified, structured format. This enables downstream models and agents to consume results programmatically and reliably.

### Response Schema

```json
{
  "status": "success" | "error",
  "results": [
    {
      "type": "verse" | "lexicon" | "word_analysis" | "versification" | "embedding" | ...,
      "reference": "Genesis 1:1" | "H430" | ...,
      "text": "In the beginning God created the heavens and the earth." | "Elohim" | ...,
      "source": "bible.verses" | "bible.hebrew_entries" | ...,
      "metadata": { ... }
    },
    ...
  ],
  "error_type": null,
  "message": null
}
```

On error:

```json
{
  "status": "error",
  "results": [],
  "error_type": "DataNotFound" | "MalformedQuery" | ...,
  "message": "No results found for query: ..."
}
```

### Supported Data Sources
- `bible.verses` (Bible text)
- `bible.translations` (translation metadata)
- `bible.hebrew_entries` (Hebrew lexicon)
- `bible.greek_entries` (Greek lexicon)
- `bible.hebrew_ot_words` (Hebrew OT word analysis)
- `bible.greek_nt_words` (Greek NT word analysis)
- `bible.versification_systems` (versification metadata)
- `bible.verse_mappings` (verse mapping)
- `bible.verse_embeddings` (semantic search)

### Example Usage

```json
{
  "status": "success",
  "results": [
    {
      "type": "verse",
      "reference": "Genesis 1:1",
      "text": "In the beginning God created the heavens and the earth.",
      "source": "bible.verses",
      "metadata": { "translation": "KJV" }
    },
    {
      "type": "lexicon",
      "reference": "H430",
      "text": "Elohim",
      "source": "bible.hebrew_entries",
      "metadata": { "definition": "God, gods, rulers, judges", "usage": "plural of majesty" }
    }
  ],
  "error_type": null,
  "message": null
}
```

See also: [Retriever Output and Error Handling Standards](../../.cursor/rules/standards/retriever_output_and_error_handling.mdc) 