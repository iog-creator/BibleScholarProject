# Archived: Content Relocated
#
# This file has been archived. Its content is now maintained in:
#
# - docs/guides/dspy_training_data.md
# - .cursor/rules/dspy_generation.mdc
#
# Please refer to those files for the latest and consolidated DSPy training instructions and guidelines.

"""
Instructions for Training Models with DSPy using HuggingFace Teacher Models
"""

# 1. Configure Your Environment
# ----------------------------

# Required Environment Variables
# Add to your .env file:
# HUGGINGFACE_API_KEY=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  # Your HuggingFace API key for teacher models
# STUDENT_MODEL=google/flan-t5-small  # Local model to be trained/optimized

# 2. Install Required Packages
# ---------------------------

# Make sure all dependencies are installed:
# pip install dspy-ai>=2.0.0 huggingface_hub>=0.23.0 transformers>=4.38.0 torch>=2.2.0

# 3. Prepare Training Data
# -----------------------

# Ensure Bible QA dataset exists
# Create folder structure if needed:
# mkdir -p data/processed/dspy_training_data

# The training dataset should be in JSONL format
# Each line should contain a JSON object with:
# {"context": "Bible verse", "question": "Question about verse", "answer": "Correct answer"}

# Example script to create dataset:
"""
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
"""

# 4. Training Process Options
# -------------------------

# Option 1: Use the API for training (background process)
# Starts a training job that runs in the background
"""
curl -X POST http://localhost:5001/api/dspy/train \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_model": "microsoft/Phi-4-mini-reasoning",
    "student_model": "google/flan-t5-small",
    "data_path": "data/processed/dspy_training_data/qa_dataset.jsonl",
    "save_path": "models/dspy"
  }'
"""

# Check training status
# curl http://localhost:5001/api/dspy/status

# Option 2: Run training script directly
# python -m src.dspy_programs.huggingface_integration

# 5. Using Trained Models
# ---------------------

# Load trained models from disk
"""
curl -X POST http://localhost:5001/api/dspy/load \
  -H "Content-Type: application/json" \
  -d '{
    "dspy_path": "models/dspy/bible_qa_compiled.dspy",
    "student_path": "models/dspy/student_model"
  }'
"""

# Test the trained model with an example
"""
curl -X POST http://localhost:5001/api/dspy/example \
  -H "Content-Type: application/json" \
  -d '{
    "context": "In the beginning God created the heavens and the earth.",
    "question": "Who created the heavens and the earth?"
  }'
"""

# 6. Available Models
# -----------------

# List available teacher models from HuggingFace
# curl http://localhost:5001/api/dspy/models

# High-Quality Teacher Models:
# - meta-llama/Llama-3.1-70B-Instruct (Best quality but slower)
# - Qwen/Qwen3-32B (Strong multilingual support)
# - anthropic/claude-3-opus-20240229 (Excellent understanding)

# Balanced Teacher Models:
# - meta-llama/Llama-3.1-8B-Instruct (Good balance of speed/quality)
# - microsoft/Phi-4-reasoning-plus (Good reasoning capabilities)

# Fast Teacher Models:
# - microsoft/Phi-4-mini-reasoning (Fast with decent quality)
# - HuggingFaceH4/zephyr-7b-beta (Fast open model)

# Student Models (to be trained):
# - google/flan-t5-small (Small but trainable)
# - google/flan-t5-base (Medium size)
# - google/flan-t5-large (Larger capacity)

# 7. Advanced Usage
# ---------------

# Create your own training dataset
# Add more complex theological questions to test student model capabilities

# Experiment with different teacher/student combinations
# Compare results with different optimization approaches

# Customize the theological accuracy metric
# Modify src/dspy_programs/huggingface_integration.py theological_accuracy_metric()

# Implement model ensembling for improved results
# Combine multiple student models for better performance

