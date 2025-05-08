# Bible QA System with DSPy and LM Studio

This document provides information about the Bible Question Answering (QA) system implemented using DSPy framework and LM Studio integration.

## Overview

The Bible QA system is designed to answer questions about the Bible using large language models. The system supports:

1. Direct inference using pre-trained models
2. DSPy-optimized models for specific Bible-related tasks
3. Integration with local LLMs via LM Studio
4. Iterative optimization to achieve high accuracy (95%+)

## System Components

### 1. Training Data

The system uses extensive training data available in:

- `data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json` (2000+ examples)
- `data/processed/dspy_training_data/theological_terms_dataset.jsonl` (100+ theological terms)
- Various specialized datasets for translations, named entities, and user interactions

For training, you can split the dataset using:
```bash
python scripts/split_dspy_dataset.py --input data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json --train-ratio 0.8
```

### 2. Model Training

The system supports training with multiple DSPy optimizers:

```bash
# Train with GRPO optimizer
python train_dspy_bible_qa.py --optimizer grpo --train-pct 0.8 --model "google/flan-t5-small"

# Train with LM Studio and Bootstrap optimizer
python train_dspy_bible_qa.py --lm-studio --lm-studio-model "mistral-nemo-instruct-2407" --model-format "chat" --optimizer bootstrap
```

Training progress is tracked using MLflow at `mlruns/672288977809348462/`.

### 3. Model Optimization

The system supports advanced optimization with multiple DSPy optimization methods:

```bash
# Optimize with BetterTogether (ensemble approach)
python train_and_optimize_bible_qa.py --optimization-method better_together --max-iterations 10 --target-accuracy 0.95

# Optimize with InferRules (rule-based approach)
python train_and_optimize_bible_qa.py --optimization-method infer_rules --max-iterations 10 --target-accuracy 0.95

# Optimize with both methods and select best
python train_and_optimize_bible_qa.py --optimization-method ensemble --max-iterations 15 --target-accuracy 0.95
```

For Windows users, a batch file simplifies the process:
```bash
# Run with default settings (BetterTogether)
optimize_bible_qa.bat

# Specify optimization method
optimize_bible_qa.bat infer_rules
```

#### Optimization Methods

1. **BetterTogether**:
   - Combines multiple model architectures (CoT, PoT, Theological QA)
   - Learns which approach works best for different question types
   - Good for diverse question sets

2. **InferRules**:
   - Focuses on improving a single model
   - Derives explicit reasoning rules to enhance performance
   - Especially effective for theological questions with Strong's IDs

3. **Ensemble**:
   - Runs both methods with half the iterations each
   - Selects the best-performing approach
   - Good when uncertain which method will work better

### 4. Inference

The system supports multiple inference methods:

```bash
# Use trained DSPy model
python test_bible_qa_dspy26.py --model-path models/dspy/bible_qa_t5_latest --test-file data/bible_qa_test.jsonl

# Use LM Studio with Mistral NeMo
python test_bible_qa_dspy26.py --use-lm-studio --lm-studio-model "mistral-nemo-instruct-2407" --test-file data/bible_qa_test.jsonl --pretty
```

### 5. Web Interface

A web interface is available for interactive QA:

```bash
# Start the web interface
python start_bible_qa_web.bat
```

## Testing with Mistral NeMo

The system has been successfully tested with Mistral NeMo 12B through LM Studio, achieving:

- **100% accuracy** on the validation test set
- Support for both context-based and general Bible knowledge questions
- Handling of theological concepts and terms

### Key Features

- **Robust LM Studio Integration**: Direct API access with retry logic
- **Flexible Answer Evaluation**: Multiple matching strategies for theological concepts
- **Prompt Optimization**: Concise, direct answers with theological precision
- **Output Formatting**: Handling for model-specific output formats like Mistral's `<think>` tags
- **Specialized Theological Reasoning**: Strong's ID recognition and theological validation

For detailed test results, see `logs/dspy_mistral_test_results.md`.

## Available Models

The system supports multiple model types:

### 1. DSPy Trained Models

Located in `models/dspy/bible_qa_t5/`:
- `bible_qa_t5_latest/` - Latest T5 model 
- `bible_qa_flan-t5-small_TIMESTAMP/` - Timestamped models for tracking

### 2. DSPy Optimized Models

Located in `models/dspy/bible_qa_optimized/`:
- `iteration_X/` - Models saved from optimization iterations
- `final_TIMESTAMP/` - Final optimized models with configuration

### 3. External Models via API

- HuggingFace models via API (configure in `.env.dspy`)
- Claude models via API (configure in `.env.dspy`)

### 4. Local Models via LM Studio

Support for any model loaded in LM Studio including:
- Mistral NeMo 12B
- Llama 3.1 models
- Mixtral models
- DeepSeek models

## DSPy Integration

The system leverages DSPy for:

1. **Signature Definition**: Bible QA tasks with theological awareness
2. **Module Implementation**: Chain-of-thought reasoning for theological questions
3. **Prompt Optimization**: GRPO and Bootstrap optimizers for improved performance
4. **Evaluation**: Specialized metrics for theological term coverage
5. **Advanced Optimization**: BetterTogether and InferRules for reaching 95%+ accuracy

## Development Guidelines

When extending the system:

1. **Training Data**: Add diverse examples covering theological concepts
2. **Prompt Engineering**: Focus on conciseness and theological precision
3. **Model Selection**: Balance performance with deployment constraints
4. **Evaluation**: Use both technical metrics and theological understanding
5. **Optimization Strategy**: Select appropriate optimization method based on question types

## Monitoring and Evaluation

The optimization process can be monitored in real-time:

1. **MLflow Dashboard**:
   ```bash
   mlflow ui
   # Access at http://localhost:5000
   ```

2. **Direct Testing**:
   ```bash
   python test_enhanced_bible_qa.py --batch-test --output-file results.json
   ```

3. **Logs and Reports**:
   - `logs/train_and_optimize_bible_qa.log` - Optimization progress
   - `logs/test_bible_qa.log` - Test output
   - `logs/dspy_mistral_test_results.md` - Detailed analysis
   - `logs/test_results.json` - Per-question outcomes

## Future Improvements

1. **Training Data Expansion**:
   - More multi-turn conversation examples
   - Complex theological reasoning questions
   - Cross-reference and narrative analysis questions

2. **Model Optimization**:
   - Distill knowledge from larger models to smaller ones
   - Optimize for specific theological domains
   - Enhance multilingual support

3. **Integration**:
   - API integration with web applications
   - Vector search enhancement
   - Cross-translation comparison

## Troubleshooting

For common issues:

1. **Model Loading**:
   - Check model path exists
   - Verify environment variables are set
   - Ensure LM Studio is running for local models

2. **API Connection**:
   - Test API endpoints directly
   - Verify API keys are valid
   - Check for rate limiting

3. **Training Issues**:
   - Validate dataset format
   - Monitor GPU memory usage
   - Check MLflow logs for errors

4. **Optimization Issues**:
   - **JSON Parsing Errors**: Ensure LM Studio is configured with proper JSON response formatting
   - **MLflow Connection Issues**: Check that MLflow server is running on port 5000
   - **Low Scores**: Try increasing training data size or number of optimization iterations
   - **Memory Issues**: Reduce batch sizes in the optimization process
   
For additional help, see `docs/rules/dspy_training_analysis.md`. 