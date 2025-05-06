# DSPy Usage Guide

This guide provides instructions for working with DSPy in the BibleScholarProject.

## Overview

DSPy (Declarative Self-improving Language Programs) is a framework for building robust AI systems with language models (LMs). It separates program flow from prompt design, allowing for systematic optimization of LM performance through:

1. **Signatures**: Declarations of tasks with input and output fields
2. **Modules**: Encapsulated LM workflows like chain-of-thought, ReAct, etc.
3. **Optimizers**: Algorithms that improve prompts and LM parameters automatically

## DSPy Datasets

The project includes several training datasets for DSPy in `data/processed/dspy_training_data/`:

| Dataset | Description | Examples |
|---------|-------------|----------|
| `qa_dataset.jsonl` | Question-answering pairs | 104 |
| `summarization_dataset.jsonl` | Bible passage summarization | 3 |
| `theological_terms_dataset.jsonl` | Theological term analysis | 100 |
| `documentation_organization_dataset.jsonl` | Documentation improvement patterns | 5 |

## Working with DSPy

### 1. Basic Example

Here's a simple example of using DSPy for question answering:

```python
import dspy
import json

# Load examples
with open('data/processed/dspy_training_data/qa_dataset.jsonl') as f:
    examples = [dspy.Example(**json.loads(line)) for line in f if not line.startswith('//') and line.strip()]

# Configure a language model
lm = dspy.OpenAI(model="gpt-3.5-turbo")
dspy.settings.configure(lm=lm)

# Define a signature
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="The Bible verse or passage")
    question = dspy.InputField(desc="Question about the verse")
    answer = dspy.OutputField(desc="Answer to the question")

# Create a module
class QAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQA)
    
    def forward(self, context, question):
        return self.qa_model(context=context, question=question)

# Use the module
qa = QAModule()
result = qa(
    context="In the beginning God created the heavens and the earth.",
    question="Who created the heavens and the earth?"
)
print(result.answer)  # Should output: "God"
```

### 2. Optimizing Models

DSPy's power comes from its ability to automatically optimize prompts using examples:

```python
from dspy.teleprompt import BootstrapFewShot

# Define a metric to evaluate performance
def answer_accuracy(example, prediction, trace=None):
    return example.answer.lower() in prediction.answer.lower()

# Create the optimizer
optimizer = BootstrapFewShot(metric=answer_accuracy)

# Split examples into train/test
trainset = examples[:80]
testset = examples[80:]

# Compile (optimize) the model
optimized_qa = optimizer.compile(QAModule(), trainset=trainset, valset=testset)

# Save the optimized model
optimized_qa.save("models/optimized_bible_qa.dspy")
```

### 3. Documentation Organization Example

The project includes a specialized module for documentation organization in `src/utils/documentation_organizer.py`:

```python
from src.utils.documentation_organizer import (
    DocumentationOrganizer,
    load_training_examples,
    train_documentation_organizer,
    generate_solution
)

# Load examples
examples = load_training_examples()

# Create and optimize a model
model = train_documentation_organizer(
    trainset=examples[:4],
    valset=examples[4:],
    optimizer_name="bootstrap",
    save_path="models/doc_organizer.dspy"
)

# Generate a solution
solution = generate_solution(
    model,
    "API documentation needs better organization and cross-referencing"
)

print(solution['solution'])
print(solution['steps'])
print(solution['patterns'])
```

### 4. Command-line Interface

You can optimize documentation organization models using the CLI:

```bash
# Basic usage
python scripts/optimize_documentation_organizer.py

# Custom optimizer
python scripts/optimize_documentation_organizer.py --optimizer simba

# Custom test problem
python scripts/optimize_documentation_organizer.py --test-problem "Documentation lacks clear examples"

# Log trace for debugging
python scripts/optimize_documentation_organizer.py --log-trace
```

## Best Practices

1. **Always define proper signatures** with clear descriptions for input and output fields
2. **Use type hints** in your DSPy modules and utility functions
3. **Create proper metrics** that measure what you care about (not just string matching)
4. **Split datasets** into proper training and validation sets
5. **Save and load models** to avoid reoptimizing every time
6. **Use ChainOfThought** for complex reasoning tasks
7. **Create reusable modules** that can be composed into larger systems

## Advanced Techniques

### 1. Custom Metrics

DSPy allows for custom metrics to evaluate model performance:

```python
def theological_accuracy(pred, gold, trace=None):
    """Custom metric for theological term analysis."""
    # Check term matching
    term_match = pred.term.strongs_id == gold.term.strongs_id
    
    # Check theological meaning
    meaning_match = (
        gold.analysis.theological_meaning.lower() in 
        pred.analysis.theological_meaning.lower()
    )
    
    # Return True only if both match
    return term_match and meaning_match
```

### 2. Multi-stage Pipelines

For complex tasks like semantic search, create multi-stage pipelines:

```python
class SemanticSearchPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.query_generator = dspy.ChainOfThought(QueryGeneration)
        self.retriever = dspy.Retrieve(k=5)
        self.analyzer = dspy.ChainOfThought(PassageAnalysis)
    
    def forward(self, question):
        # Generate an optimized query
        query = self.query_generator(question=question).query
        
        # Retrieve relevant passages
        passages = self.retriever(query).passages
        
        # Analyze the passages
        analysis = self.analyzer(passages=passages, question=question)
        
        return dspy.Prediction(
            query=query,
            passages=passages,
            answer=analysis.answer,
            explanation=analysis.explanation
        )
```

## Model Tracking

The BibleScholarProject implements a comprehensive model tracking system to monitor the performance of DSPy models over time:

### Model Versioning

All trained DSPy models are automatically versioned and stored in the `models/dspy/` directory with the naming convention:
```
{model_name}_v{version_number}.dspy
```

For example: `documentation_organizer_v3.dspy`

### Metrics Tracking

Performance metrics for each model version are stored in JSONL format in `data/processed/dspy_training_data/metrics/`:

```
{model_name}_metrics.jsonl
```

Each entry includes:
- Training/validation/test metrics
- Dataset versions used (with hashes)
- Timestamp and version information
- Optional description of changes

### Using the Tracking System

```bash
# Record metrics for a model
python scripts/track_dspy_model_metrics.py record --model-name doc_organizer --metrics metrics.json

# Generate a performance report
python scripts/track_dspy_model_metrics.py report --model-name doc_organizer
```

The metrics.json file should include structured metrics like:

```json
{
  "metrics": {
    "train_accuracy": 0.95,
    "val_accuracy": 0.92,
    "test_accuracy": 0.89,
    "theological_precision": 0.87
  },
  "parameters": {
    "optimizer": "bootstrap",
    "max_bootstrapped_demos": 3,
    "model": "gpt-3.5-turbo"
  },
  "description": "Improved theological term recognition"
}
```

## Troubleshooting

1. **Module not learning**: Check that your examples are correctly formatted with proper field names
2. **Inconsistent results**: Use a higher temperature for exploration, then lower for final use
3. **Poor performance**: Try different optimizers (BootstrapFewShot, SIMBA, KNNFewShot)
4. **Metrics not working**: Ensure metric function signature has `(pred, gold, trace=None)` parameters

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