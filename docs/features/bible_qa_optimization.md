# Bible QA Optimization System

The Bible QA Optimization system is designed to iteratively improve DSPy-based question answering for Bible text, achieving high accuracy through optimization.

## System Overview

![Bible QA Optimization Architecture](../assets/bible_qa_optimization.png)

The Bible QA Optimization system consists of:

1. **Base Models**:
   - Chain of Thought (CoT) for direct factual questions
   - Program of Thought (PoT) for multi-step reasoning
   - TheologicalQA for specialized theological questions

2. **Optimization Techniques**:
   - BetterTogether: Ensembles multiple approaches
   - InferRules: Learns theological reasoning rules
   - Ensemble: Combines both methods

3. **Tracking & Evaluation**:
   - MLflow integration for experiment tracking
   - Custom theological accuracy metrics
   - Strong's ID handling for Hebrew/Greek terms

## Key Features

### 1. Theological Accuracy Metrics

Our custom BibleQAMetric evaluates:
- Word overlap with reference answers
- Bonus points for handling theological concepts
- Special scoring for Strong's ID questions

### 2. Multi-step Reasoning

The Program of Thought approach includes:
- Theological analysis
- Biblical exegesis
- Answer formulation

### 3. MLflow Integration

Each optimization run tracks:
- Accuracy per iteration
- Best model checkpoints
- Learning curves

## Custom Dataset Creation

The system can generate customized validation datasets:

```bash
python -m scripts.expand_validation_dataset --num-single 50 --num-multi 15
```

## Troubleshooting

If encountering issues:

1. **Memory issues**: Reduce batch size and number of examples
2. **Accuracy plateau**: Try a different optimization method
3. **Theological term issues**: Ensure Strong's IDs are properly processed

## References

- **DSPy Documentation**: [https://dspy.ai/learn/optimization/overview/](https://dspy.ai/learn/optimization/overview/)
- **MLflow Integration**: [https://mlflow.org/docs/latest/python_api/mlflow.dspy.html](https://mlflow.org/docs/latest/python_api/mlflow.dspy.html)
- **Complete README**: See [README_DSPY_OPTIMIZATION.md](../../README_DSPY_OPTIMIZATION.md) 