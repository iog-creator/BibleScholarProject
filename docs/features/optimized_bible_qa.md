# Optimized Bible QA with Non-Synthetic Training Data

## Overview

The Optimized Bible QA system is an enhanced question-answering system that leverages non-synthetic Bible trivia data to provide accurate, concise answers to Bible-related questions. This approach significantly improves the quality of answers compared to systems trained on synthetic data.

## Key Components

1. **`train_bible_qa_optimized.py`**: Main training pipeline that implements the `OptimizedBibleQAModule` for Bible QA using non-synthetic data
2. **`test_optimized_bible_qa.py`**: Command-line interface for testing the optimized model
3. **`test_optimized_bible_qa.bat`**: Windows batch file for easy model testing and usage
4. **`bible_qa_api.py`**: Flask Blueprint for integrating the Bible QA system with web applications

## Implementation Details

### Training Approach

The system uses DSPy's few-shot learning capabilities with the Mistral model via LM Studio:

1. Loads non-synthetic Bible trivia examples from `data/processed/dspy_training_data/qa_bible_trivia_alpaca.jsonl`
2. Uses these examples for few-shot learning (optimal performance with 3-5 examples)
3. Creates a custom system prompt that combines the question with example QA pairs
4. Formats responses to ensure proper Bible verse citations
5. Evaluates performance against a baseline model

### Performance Results

Performance metrics compared to the baseline system:

| Metric             | Baseline | Optimized with Non-Synthetic Data | Improvement |
|--------------------|----------|-----------------------------------|-------------|
| Exact Match        | 5.0%     | 30.0%                             | +25.0%      |
| Scripture Citations| Limited  | Consistent                        | +           |
| Answer Conciseness | Verbose  | Concise                           | +           |

### API Integration

The system exposes a REST API through a Flask Blueprint:

- **Endpoint**: `/bible_qa/question` (POST)
- **Request Format**:
  ```json
  {
    "question": "Your Bible question here",
    "context": "Optional context"
  }
  ```
- **Response Format**:
  ```json
  {
    "status": "success",
    "answer": "The answer to the question",
    "model_info": {
      "model_type": "Bible QA (Optimized)",
      "response_time": "1.23s"
    }
  }
  ```

## Usage

### Interactive Mode

```bash
.\test_optimized_bible_qa.bat
```

This launches an interactive session where you can ask Bible-related questions.

### Single Question Mode

```bash
.\test_optimized_bible_qa.bat What books of the Bible did Paul write?
```

This answers a specific question directly.

### API Usage

```python
import requests
import json

response = requests.post(
    "http://localhost:5000/bible_qa/question",
    json={"question": "What is the significance of the number 40 in the Bible?"}
)

result = response.json()
print(result["answer"])
```

## Examples

1. **Question**: "Who was the first person to see Jesus after his resurrection?"
   **Answer**: "Mary Magdalene (John 20:1-18)"

2. **Question**: "What is the significance of the number 40 in the Bible?"
   **Answer**: "The number 40 represents testing, trial, or probation. Examples include: 40 days of flood (Genesis 7:17), 40 years in wilderness (Numbers 14:33-34), Moses on Mount Sinai for 40 days (Exodus 24:18), Jesus fasted for 40 days (Matthew 4:2)."

## Requirements

- Python 3.9+
- DSPy 2.6+
- LM Studio with Mistral model
- Flask for API integration

## Future Improvements

1. **Expanded Dataset**: Incorporate more non-synthetic Q&A pairs from biblical scholars
2. **Fine-Tuning**: Full parameter fine-tuning of smaller models on the non-synthetic dataset
3. **Multi-Language Support**: Extend to non-English Bible questions and answers 