# Bible T5 Model Training with DSPy

This document provides instructions for training and using a T5 model with DSPy to interact with the Bible database.

## Overview

The system consists of two main components:

1. **Training Pipeline**: Trains a T5 model on Bible question-answering data, using the DSPy framework
2. **Testing & Inference**: Allows interacting with the trained model for Bible questions

## Prerequisites

- Python 3.8+
- PostgreSQL database with Bible data (bible_db)
- Required Python packages:
  - dspy-ai
  - psycopg2
  - pandas
  - sklearn
  - mlflow
  - transformers
  - torch
  - tqdm
  - python-dotenv

## Setup

1. **Install Required Packages**

   ```bash
   pip install dspy-ai psycopg2-binary pandas scikit-learn mlflow transformers torch tqdm python-dotenv
   ```

2. **Configure Environment Variables**

   Edit the `.env.dspy` file with your database credentials:

   ```ini
   # Database connection details
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=bible_db
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   
   # API keys and paths
   OPENAI_API_KEY=your_openai_api_key  # For teacher model
   ```

3. **Prepare Directory Structure**

   Ensure the following directories exist:
   - `logs/`
   - `models/dspy/bible_qa_t5/`

## Training the Model

### Automatic Training

Run the included batch file on Windows:

```bash
train_and_test_bible_t5.bat
```

### Manual Training

To train the model manually, use the `train_t5_bible_qa.py` script:

```bash
python train_t5_bible_qa.py \
  --lm "google/flan-t5-small" \
  --teacher "gpt-3.5-turbo" \
  --optimizer "dsp" \
  --track-with-mlflow
```

#### Available Options

- `--lm`: Base language model (default: "google/flan-t5-small")
- `--teacher`: Teacher model for optimization (default: "gpt-3.5-turbo")
- `--optimizer`: DSPy optimizer to use: "dsp", "rm", or "none" (default: "dsp")
- `--use-custom-data`: Generate training data from database instead of using existing dataset
- `--dataset-path`: Path to existing dataset file
- `--num-examples`: Number of examples to generate if using custom data (default: 100)
- `--batch-size`: Batch size for training (default: 8)
- `--max-tokens`: Maximum tokens for generation (default: 512)
- `--track-with-mlflow`: Track experiment with MLflow

## Testing the Model

### Interactive Mode

To test the model interactively:

```bash
python test_bible_t5_model.py \
  --model-path "models/dspy/bible_qa_t5/your_model_name" \
  --interactive
```

### Direct Question

To ask a specific question:

```bash
python test_bible_t5_model.py \
  --model-path "models/dspy/bible_qa_t5/your_model_name" \
  --question "Who is Jesus in the Bible?" \
  --verse-ref "John 1:1"
```

#### Available Options

- `--model-path`: Path to the trained DSPy model (required)
- `--question`: Question to ask the model
- `--verse-ref`: Verse reference for context (e.g., 'John 3:16')
- `--interactive`: Run in interactive mode
- `--max-tokens`: Maximum tokens for generation (default: 512)
- `--temperature`: Temperature for generation (default: 0.3)

## Advanced: Training with Custom Data

To train the model with data generated from the database:

```bash
python train_t5_bible_qa.py \
  --lm "google/flan-t5-small" \
  --teacher "gpt-3.5-turbo" \
  --use-custom-data \
  --num-examples 500 \
  --optimizer "dsp"
```

## Experiment Tracking

The training process is tracked using MLflow. You can view the experiments by:

1. Starting the MLflow UI:
   ```bash
   mlflow ui
   ```

2. Opening [http://localhost:5000](http://localhost:5000) in your browser

## Troubleshooting

- **Database Connection Issues**: Verify your database credentials in `.env.dspy`
- **Missing Training Data**: Ensure the training data exists at the specified path
- **Model Loading Errors**: Check that Hugging Face has the model you're trying to use
- **CUDA Out of Memory**: Reduce batch size or try a smaller model

## Example Usage

```python
import dspy

# Load model
model = dspy.load("models/dspy/bible_qa_t5/your_model_name")

# Configure language model
lm = dspy.HFModel(model="google/flan-t5-small", max_tokens=512, temperature=0.3)
dspy.settings.configure(lm=lm)

# Ask question
answer = model(context="John 3:16: For God so loved the world...", 
               question="What does John 3:16 tell us about God's love?")
print(answer.answer)
``` 