---
title: DSPy Training Guide
description: Comprehensive guide for training, optimizing, and evaluating DSPy models in the BibleScholarProject.
last_updated: 2024-06-10
related_docs:
  - ../../src/dspy_programs/README.md
  - ../../scripts/README.md
  - ../../tests/README.md
  - ../../data/README.md
  - ../../.cursor/rules/dspy_generation.mdc
---
# DSPy Training Data Guide for BibleScholarProject

This document provides comprehensive guidance on generating, using, and extending DSPy training data for the BibleScholarProject's AI assistance capabilities.

*This document is complemented by the [dspy_generation](.cursor/rules/standards/dspy_generation.mdc) cursor rule.*

## Overview

The BibleScholarProject uses DSPy to train AI models that can assist with biblical research, theological queries, and autonomous web interface interactions. Training data is stored in JSONL format in the `data/processed/dspy_training_data` directory.

## Bible T5 Model for Question-Answering

The BibleScholarProject implements a specialized T5-based model for biblical question answering using DSPy. This model leverages transfer learning from pre-trained T5 models (FLAN-T5) and adds domain-specific optimization for biblical knowledge.

### Training the Bible T5 Model

The `train_t5_bible_qa.py` script provides a comprehensive framework for training T5 models:

```bash
# Basic training with default parameters
python train_t5_bible_qa.py

# Specify model size by key name
python train_t5_bible_qa.py --lm small

# With specific model path, optimizer, and MLflow tracking
python train_t5_bible_qa.py --lm "google/flan-t5-base" --optimizer dsp --track-with-mlflow

# Use Hugging Face API for remote model access
python train_t5_bible_qa.py --lm small --use-huggingface 

# Use custom dataset generation
python train_t5_bible_qa.py --use-custom-data --num-examples 200
```

### Class Structure

The implementation requires module and signature classes defined at the module level for proper serialization:

```python
# Define the signature for Bible QA tasks
class BibleQA(dspy.Signature):
    """Answer questions about Bible passages with theological accuracy."""
    context = dspy.InputField(desc="Optional context from Bible passages")
    question = dspy.InputField(desc="A question about Bible content, history, or theology")
    answer = dspy.OutputField(desc="A comprehensive, accurate answer based on the Bible")

# Module implementation must be at top level (not nested in functions)
class BibleQAModule(dspy.Module):
    """Module for Bible QA using a student model."""
    
    def __init__(self):
        super().__init__()
        self.qa_predictor = dspy.Predict(BibleQA)
    
    def forward(self, context, question):
        """Answer a question based on context."""
        return self.qa_predictor(context=context, question=question)
```

> **Important**: Class definitions must be at the module level, not nested within functions, for pickle serialization to work correctly.

### Model Architecture and Options

The T5 implementation provides multiple model sizes through a dictionary:

```python
T5_MODELS = {
    "small": "google/flan-t5-small",     # 80M parameters
    "base": "google/flan-t5-base",       # 250M parameters
    "large": "google/flan-t5-large",     # 800M parameters
    "xl": "google/flan-t5-xl",           # 3B parameters
}
```

This allows easy selection through the command line:

```python
# Support both direct paths and key names
if args.lm in T5_MODELS:
    args.lm = T5_MODELS[args.lm]
```

### LM Backend Configuration

The system supports two primary backends:

1. **LM Studio** (local inference):
   ```python
   # Dynamic configuration from environment
   lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
   lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL")
   
   # Create LM instance
   lm = dspy.LM(
       model_type="chat",
       model="openai/" + lm_studio_model, 
       api_base=lm_studio_api,
       api_key="sk-dummy-key",
       max_tokens=args.max_tokens,
       temperature=args.temperature
   )
   ```

2. **Hugging Face** (cloud API):
   ```python
   # Get API key from environment
   hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
   
   # Create LM instance
   lm = dspy.LM(
       model="huggingface/" + args.lm,
       api_key=hf_api_key,
       max_tokens=args.max_tokens,
       temperature=args.temperature
   )
   ```

### Optimization Methods

The system offers multiple optimization approaches:

1. **BootstrapFewShot** (default):
   ```python
   optimizer = BootstrapFewShot(max_bootstrapped_demos=5)
   optimized_model = optimizer.compile(student=model, trainset=train_examples[:100])
   ```

2. **RewardModelRM**:
   ```python
   bootstrap = BootstrapFewShot(max_bootstrapped_demos=3)
   bootstrapped_model = bootstrap.compile(student=model, trainset=train_examples[:50])
   
   rm_optimizer = RewardModelRM(metric=basic_accuracy)
   optimized_model = rm_optimizer.compile(student=bootstrapped_model, trainset=train_examples[50:100])
   ```

3. **LabeledFewShot**:
   ```python
   teleprompter = LabeledFewShot(k=3)
   optimized_model = teleprompter.compile(student=model, trainset=train_examples[:5])
   ```

### Model Persistence

The models are serialized using Python's pickle for compatibility across environments:

```python
def save_model(model, path: str):
    """Save a trained model to disk."""
    # Ensure output directory exists
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Use pickling to save the optimized module
    try:
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump(model, f)
        
        # Also save metadata as JSON
        config = {
            'model_type': 'bible_qa',
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'version': '1.0.0'
        }
        with open(f"{path}.json", 'w') as f:
            json.dump(config, f, indent=2)
            
        # Create an MLflow-friendly info file
        with open(f"{path}.info", 'w') as f:
            f.write(f"Bible QA Model\n")
            f.write(f"Version: 1.0.0\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
            
        logger.info(f"Successfully saved model to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return False
```

#### Pickle Serialization Requirements

For successful model pickling, observe these requirements:

1. All classes must be defined at module level, not nested in functions
2. Class definitions should be consistent between saving and loading
3. Import dependencies must match when loading the model
4. Consider versioning the pickled files with timestamps for tracking

### Loading and Using Bible T5 Models

To use a trained Bible T5 model in another script:

```python
def load_bible_qa_model(model_path: str):
    """Load a saved Bible QA model."""
    try:
        # Load model with pickle
        with open(os.path.join(model_path, 'model.pkl'), 'rb') as f:
            model = pickle.load(f)
        
        # Load metadata
        with open(os.path.join(model_path, 'config.json'), 'r') as f:
            config = json.load(f)
        
        return model, config
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

# Use latest model or specific version
model_path = "models/dspy/bible_qa_t5/bible_qa_t5_latest"
# Or specific timestamp
# model_path = "models/dspy/bible_qa_t5/bible_qa_t5_20250506_184421"

# Load the model
bible_qa, config = load_bible_qa_model(model_path)

# Configure a DSPy LM for inference
lm = dspy.LM(...)
dspy.settings.configure(lm=lm)

# Use the model
if bible_qa:
    result = bible_qa(
        context="In the beginning God created the heavens and the earth.",
        question="Who created the heavens and the earth?"
    )
    print(f"Answer: {result.answer}")
```

### Experiment Tracking with MLflow

The training script includes comprehensive MLflow integration:

```python
# Configure MLflow
mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', './mlruns'))
mlflow.set_experiment(os.getenv('MLFLOW_EXPERIMENT_NAME', 'bible_qa_t5'))

# Start tracking run
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
with mlflow.start_run(run_name=f"t5_{model_name}_{timestamp}"):
    # Log parameters
    mlflow.log_param("base_model", args.lm)
    mlflow.log_param("optimizer", args.optimizer)
    mlflow.log_param("num_train_examples", len(train_data))
    mlflow.log_param("max_tokens", args.max_tokens)
    mlflow.log_param("temperature", args.temperature)
    
    # Log metrics
    mlflow.log_metric("accuracy", accuracy)
    
    # Log artifacts
    mlflow.log_artifact(info_file)
```

Runs can be viewed through the MLflow UI:

```bash
# Start MLflow UI
mlflow ui --port 5000
```

### Evaluation Metrics

The Bible T5 models use custom evaluation metrics:

```python
def basic_accuracy(example, pred, trace=None):
    """Basic accuracy metric - checks if key parts of answer match."""
    gold_answer = example.answer.lower()
    pred_answer = pred.answer.lower()
    
    # Check for basic matching
    if gold_answer in pred_answer or pred_answer in gold_answer:
        return True
    
    # Calculate word overlap as a fallback
    gold_words = set(gold_answer.split())
    pred_words = set(pred_answer.split())
    if len(gold_words) > 0:
        overlap = len(gold_words.intersection(pred_words)) / len(gold_words)
        return overlap > 0.5
    
    return False
```

More specialized theological metrics can be added for domain-specific evaluation.

## Dataset Categories

### 1. Question-Answering (QA)

Dataset file: `qa_dataset.jsonl`

This dataset contains question-answer pairs about Bible verses, with proper context. It's designed to train models to answer factual and theological questions about biblical content.

Example format:
```json
{
  "context": "In the beginning God created the heavens and the earth.",
  "question": "Who created the heavens and the earth?",
  "answer": "God",
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1, "type": "factual"}
}
```

### 2. Theological Terms Analysis

Dataset file: `theological_terms_dataset.jsonl`

This dataset focuses specifically on critical theological terms such as Elohim, YHWH, Adon, Chesed, and Aman. It provides context, lexical information, and theological analysis.

Example format:
```json
{
  "term": {"word": "אלהים", "strongs_id": "H430", "lemma": "אלהים", "gloss": "God"},
  "context": {"verse_text": "In the beginning God created...", "book": "Genesis", "chapter": 1, "verse": 1},
  "analysis": {"theological_meaning": "Elohim", "importance": "Core theological term with expected 2,600+ occurrences"}
}
```

### 3. Named Entity Recognition (NER)

Dataset file: `ner_dataset.jsonl`

This dataset contains tagged tokens for identifying named entities in biblical texts, with special focus on distinguishing between DEITY and PERSON entities.

Example format:
```json
{
  "tokens": ["In", "the", "beginning", "God", "created"],
  "tags": ["O", "O", "O", "DEITY", "O"],
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1}
}
```

### 4. Web Interaction

Dataset file: `web_interaction_dataset.jsonl`

This dataset trains models to interpret user queries, extract parameters, and formulate appropriate API calls for web interface interaction.

Example format:
```json
{
  "query": "Find verses containing YHWH in Genesis",
  "action": "search_database",
  "parameters": {"book": "Genesis", "term": "YHWH", "strongs_id": "H3068"},
  "expected_response_format": {"results": [{"reference": "Gen 2:4", "text": "..."}]},
  "metadata": {"interaction_type": "database_query"}
}
```

### 5. Evaluation Metrics

Dataset file: `evaluation_metrics.jsonl`

This dataset provides specialized evaluation metrics for assessing the quality of model outputs, particularly for theological accuracy.

Example format:
```json
{
  "task": "bible_qa",
  "metric_name": "theological_accuracy",
  "metric_implementation": "def theological_accuracy(prediction, reference): ...",
  "metadata": {"metric_type": "accuracy", "theological_focus": true}
}
```

## Generating Training Data

### Running the Generator

To generate fresh DSPy training data:

```bash
python scripts/generate_dspy_training_data.py
```

This script connects to the database, extracts relevant information, and formats it into the appropriate JSONL files in the `data/processed/dspy_training_data` directory.

### Critical Requirements

1. **Theological Term Integrity**: All data generation must validate the presence of critical theological terms:
   - Elohim (H430): Minimum 2,600 occurrences
   - YHWH (H3068): Minimum 6,000 occurrences
   - Adon (H113): Minimum 335 occurrences
   - Chesed (H2617): Minimum 248 occurrences
   - Aman (H539): Minimum 100 occurrences

2. **Batch Processing**: Generation must use batch processing for efficiency:
   ```python
   def process_in_batches(items, batch_size=100):
       results = []
       for i in range(0, len(items), batch_size):
           batch = items[i:i+batch_size]
           batch_results = process_batch(batch)
           results.extend(batch_results)
       return results
   ```

3. **Quality Control**: All generated data must adhere to the schema defined in the README.md file in the output directory.

## Using with DSPy

### Basic Loading

Load DSPy examples like this:

```python
import dspy
import json

with open('data/processed/dspy_training_data/qa_dataset.jsonl') as f:
    trainset = [dspy.Example(**json.loads(line)) for line in f if not line.startswith('//') and line.strip()]
```

### Model Optimization

Optimize models using DSPy's optimization capabilities:

```python
from dspy.teleprompt import SIMBA

# Define a custom metric function if needed
def theological_accuracy(prediction, reference):
    # Add implementation that checks theological accuracy
    pass

# Create optimizer with the metric
optimizer = SIMBA(metric=theological_accuracy)

# Optimize the model
optimized_model = optimizer.optimize(base_model, trainset=trainset, devset=devset)
```

### Creating Web Interface Agents

Implement autonomous web interface agents:

```python
class BibleSearchAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.query_parser = dspy.ChainOfThought("context, query -> action, parameters")
        
    def forward(self, query):
        # Parse query to determine action and parameters
        parsed = self.query_parser(context="Biblical research assistant", query=query)
        
        # Execute the appropriate action
        if parsed.action == "search_database":
            results = search_bible_database(**parsed.parameters)
            return {"results": results}
        elif parsed.action == "lookup_strongs":
            definition = lookup_strongs_entry(**parsed.parameters)
            return {"definition": definition}
        # Add other actions as needed
```

## Extending Training Data

### Adding New Categories

1. Create a new generation function in `scripts/generate_dspy_training_data.py`
2. Update the main function to call your new generator
3. Add the new dataset to the README.md template

### Improving Existing Categories

To improve an existing category:

1. Review the current examples for quality and theological accuracy
2. Modify the generator function to include more diverse examples
3. Add new example types that address identified weaknesses
4. Ensure all critical theological terms are properly represented

## Best Practices

1. **Theological Verification**: Always verify that theological terms are correctly represented and that answers align with scholarly biblical interpretation.
2. **Consistent Formatting**: Maintain consistent JSON formatting across all dataset files.
3. **Metadata Inclusion**: Always include metadata fields for traceability and filtering.
4. **Cross-Language Support**: Include examples across different translations when possible.

## Integration with Semantic Search

The DSPy training system integrates closely with the semantic search capabilities:

1. **Vector-Enhanced Examples**: Use embedding vectors to find semantically similar verses for training examples.
2. **Theological Term Boosting**: Prioritize examples containing critical theological terms.
3. **Multilingual Support**: Generate examples across different language translations.

See [Semantic Search](../features/semantic_search.md) for more details on how the vector search capabilities enhance DSPy training data generation.

## Related Documentation

- [Theological Terms](../features/theological_terms.md) - Theological term definitions and processing
- [Database Schema](../reference/DATABASE_SCHEMA.md) - Database structure information
- [API Reference](../reference/API_REFERENCE.md) - API endpoints for data access

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Moved to guides directory and updated cross-references | BibleScholar Team |
| 2025-04-20 | Added integration with semantic search section | BibleScholar Team |
| 2025-03-15 | Added best practices section | BibleScholar Team |
| 2025-02-01 | Initial DSPy training guide | BibleScholar Team | 