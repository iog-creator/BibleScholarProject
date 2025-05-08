# HuggingFace Integration with DSPy for Model Training

## Overview

This document describes the teacher-student approach for model training using DSPy and HuggingFace's Inference API in the BibleScholarProject. This integration enables training smaller local models guided by high-quality, hosted models from HuggingFace.

## Features

1. **Teacher-Student Training** - Use large HuggingFace models as teachers to optimize smaller local models
2. **DSPy-Powered Optimization** - Leverage DSPy's optimization techniques for Bible research tasks
3. **Web Interface for Training** - Simple UI for configuring and monitoring training
4. **Training API** - RESTful API for programmatic training and optimization
5. **Flexible Model Configuration** - Easily switch between different teacher and student models

## Setup

### Prerequisites

1. HuggingFace API Key (sign up at [HuggingFace](https://huggingface.co) and create an API key)
2. DSPy installed (`pip install dspy-ai>=2.0.0`)
3. Python 3.8+ environment with PyTorch and transformers

### Configuration

1. Add your HuggingFace API key to your `.env` file:

```
HUGGINGFACE_API_KEY=your_api_key_here
STUDENT_MODEL=google/flan-t5-small  # Default student model
```

2. Install required packages:

```bash
pip install dspy-ai>=2.0.0 huggingface_hub>=0.23.0 transformers>=4.38.0 torch>=2.2.0
```

## Usage

### Web Interface

Access the web interface at `/dspy-ask` to interact with the system. The interface provides:

- **Training Tab**: Configure and start model training
  - Select teacher model from HuggingFace
  - Select student model to be trained
  - Specify training data path
  
- **Testing Tab**: Test trained models with Biblical passages
  - Enter Bible passage as context
  - Ask questions about the passage
  
- **Status Tab**: Monitor training progress
  - View training progress and status
  - See training results and model paths

### Training Process

The DSPy training process involves:

1. **Teacher Selection**: Choose a high-quality model from HuggingFace to guide the training
2. **Student Configuration**: Set up a smaller, local model that will be optimized
3. **Data Loading**: Load Bible question-answering examples from JSONL format
4. **Optimization**: Use DSPy's optimization algorithms (e.g., BootstrapFewShot) to optimize the student
5. **Evaluation**: Assess theological accuracy using the teacher model
6. **Model Saving**: Save both the compiled DSPy model and the student model

### API Endpoints

The following API endpoints are available:

#### `/api/dspy/train` (POST)

Start a training job with teacher-student approach.

**Request:**
```json
{
  "teacher_model": "microsoft/Phi-4-mini-reasoning",
  "student_model": "google/flan-t5-small",
  "data_path": "data/processed/dspy_training_data/qa_dataset.jsonl",
  "save_path": "models/dspy"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Training job started",
  "training_status": {
    "is_training": true,
    "current_task": "initializing",
    "progress": 0,
    "start_time": "2023-08-14T15:22:30.123456"
  }
}
```

#### `/api/dspy/status` (GET)

Check the status of a running training job.

**Response:**
```json
{
  "status": "success",
  "training_status": {
    "is_training": true,
    "current_task": "loading_data",
    "progress": 10,
    "start_time": "2023-08-14T15:22:30.123456",
    "completion_time": null,
    "error": null,
    "results": null
  }
}
```

#### `/api/dspy/example` (POST)

Test a trained model with a Bible passage.

**Request:**
```json
{
  "context": "In the beginning God created the heavens and the earth.",
  "question": "Who created the heavens and the earth?"
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "answer": "God created the heavens and the earth.",
    "student_model": "google/flan-t5-small"
  }
}
```

#### `/api/dspy/models` (GET)

List available teacher and student models.

**Response:**
```json
{
  "teacher_models": {
    "high_quality": ["meta-llama/Llama-3.1-70B-Instruct", "Qwen/Qwen3-32B", "anthropic/claude-3-opus-20240229"],
    "balanced": ["meta-llama/Llama-3.1-8B-Instruct", "microsoft/Phi-4-reasoning-plus", "Qwen/Qwen3-8B"],
    "fast": ["microsoft/Phi-4-mini-reasoning", "HuggingFaceH4/zephyr-7b-beta"]
  },
  "student_models": {
    "local_models": ["google/flan-t5-small", "google/flan-t5-base", "google/flan-t5-large"],
    "embedding_models": ["text-embedding-nomic-embed-text-v1.5", "BAAI/bge-large-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"]
  }
}
```

### Training Data Format

Training data should be in JSONL format with each line containing a JSON object:

```json
{"context": "Bible verse text", "question": "Question about the verse", "answer": "Correct answer"}
```

Example:

```json
{"context": "In the beginning God created the heavens and the earth.", "question": "Who created the heavens and the earth?", "answer": "God created the heavens and the earth."}
{"context": "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.", "question": "What is required to have eternal life?", "answer": "Believing in God\'s Son is required to have eternal life."}
```

## Architecture

The HuggingFace DSPy training integration consists of:

1. **Teacher-Student Configuration** - `src/dspy_programs/huggingface_integration.py`
2. **DSPy Training API** - `src/api/dspy_api.py`
3. **Web Interface** - `src/web_app.py` route and `templates/dspy_ask.html`
4. **Environment Configuration** - `.env` file settings

The integration uses HuggingFace's Inference API for teacher models, which eliminates the need for powerful local GPU resources while training smaller models that can run locally.

## Testing

To create a simple test dataset:

```python
import json

examples = [
    {
        'context': 'In the beginning God created the heavens and the earth.',
        'question': 'Who created the heavens and the earth?',
        'answer': 'God created the heavens and the earth.'
    },
    {
        'context': 'For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.',
        'question': 'What is required to have eternal life?',
        'answer': 'Believing in God\'s Son is required to have eternal life.'
    }
]

with open('data/processed/dspy_training_data/qa_dataset.jsonl', 'w') as f:
    for example in examples:
        f.write(json.dumps(example) + '\n')
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your HuggingFace API key is correctly set in the .env file
   - Verify the key has appropriate permissions for Inference API

2. **Model Availability**
   - Some teacher models may be temporarily unavailable or require specific providers
   - Try switching to a different teacher model if you encounter errors

3. **Student Model Installation**
   - Ensure transformers and torch are properly installed
   - Some student models may require additional dependencies

4. **Training Data Format**
   - Verify your JSONL file has the correct format
   - Each line must be a valid JSON object with context, question, and answer fields

## Future Enhancements

1. **Advanced Optimization Techniques** - Implement more sophisticated DSPy optimization algorithms
2. **Multi-Stage Training** - Add support for multi-stage training pipelines
3. **Ensemble Models** - Create ensembles of multiple student models for improved results
4. **Extended Metrics** - Add more theological evaluation metrics
5. **Cross-Language Training** - Support training for multilingual Bible research

## References

- [DSPy Documentation](https://dspy.ai/)
- [HuggingFace Models](https://huggingface.co/models) 
- [Transformers Documentation](https://huggingface.co/docs/transformers/) 