# BetterTogether Optimizer for Bible QA with DSPy 2.6

This document explains how to use the BetterTogether optimizer with DSPy 2.6 for Bible question answering, including our custom JSON patch for LM Studio compatibility.

## Overview

The BetterTogether optimizer in DSPy 2.6 offers a way to optimize language model prompts. Our implementation addresses specific compatibility issues between DSPy 2.6 and LM Studio by:

1. Patching JSON parsing to handle string responses from LM Studio
2. Removing unsupported parameters that cause errors
3. Providing automatic fallbacks for failed optimizations
4. Enhancing pattern recognition for reasoning/answer format

## Key Components

* `test_optimized_bible_qa.py`: Minimal working example of BetterTogether optimizer
* `dspy_json_patch.py`: Patch for DSPy's JSON parsing with LM Studio
* `test_optimized_bible_qa.bat`: Windows script for running the optimization
* `train_and_optimize_bible_qa.py`: Full implementation with MLflow integration

## Prerequisites

1. **LM Studio** (version 0.3.4+):
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Load a suitable model (we tested with mistral-nemo-instruct-2407)
   - Enable the API server (default port: 1234)

2. **Python Environment**:
   ```bash
   pip install "dspy-ai>=2.6.0" mlflow python-dotenv
   ```

3. **Environment Configuration**:
   - Create or modify `.env.dspy` with:
   ```
   LM_STUDIO_API_URL=http://localhost:1234/v1
   LM_STUDIO_CHAT_MODEL=mistral-nemo-instruct-2407
   ```

## Running the Example

1. Start LM Studio and enable the API server
2. Run the minimal test script:
   ```
   .\test_optimized_bible_qa.bat
   ```
   
3. For the complete workflow with MLflow tracking:
   ```
   .\run_complete_optimization.bat better_together 10 0.95
   ```

The scripts will:
- Verify LM Studio is running
- Start MLflow server if not already running
- Run BetterTogether optimization
- Log results to MLflow
- Test the optimized model

## JSON Patch Improvements

The `dspy_json_patch.py` file addresses several issues:

1. **Enhanced String Response Handling**:
   - LM Studio often returns string responses instead of JSON objects
   - Our patch extracts JSON-like structures from text using multiple pattern matching approaches
   - Handles various ChainOfThought formats:
     - Standard reasoning/answer format
     - Numbered steps followed by a conclusion
     - Markdown-style headers
     - "I'll think through this" natural language patterns

2. **Parameter Filtering**:
   - Automatically removes unsupported parameters from BetterTogether.compile():
     - `max_bootstrapped_demos` (not supported in DSPy 2.6)
     - `max_labeled_demos` (not supported in DSPy 2.6)
     - `num_iterations` (not supported in DSPy 2.6)
     - `valset` (not supported in DSPy 2.6)
     - `valset_ratio` (not supported in DSPy 2.6)
     - `strategy` (not supported in DSPy 2.6)
   - Detects unsupported parameter errors and provides detailed error messages

3. **Robust Error Handling**:
   - Provides automatic fallbacks when optimization fails
   - Handles "has no attribute 'run'" errors in DSPy 2.6
   - Logs detailed information for troubleshooting
   - Returns unoptimized model as fallback when optimization fails

4. **LM Configuration Fixes**:
   - Removes problematic `response_format` parameter
   - Correctly configures LM Studio for compatibility
   - Handles both module-level and instance-level configuration

## Implementation Notes

### BetterTogether Configuration

In DSPy 2.6, the BetterTogether optimizer only supports a minimal set of parameters:

```python
# SUPPORTED configuration
optimizer = dspy.BetterTogether(metric=metric)
optimized_model = optimizer.compile(
    student=module,
    trainset=train_data
)

# UNSUPPORTED configuration (will cause errors)
optimizer = dspy.BetterTogether(metric=metric)
optimized_model = optimizer.compile(
    student=module,
    trainset=train_data,
    max_bootstrapped_demos=2,  # Unsupported
    max_labeled_demos=2,       # Unsupported
    num_iterations=5,          # Unsupported
    valset_ratio=0.2           # Unsupported
)
```

### Signature Requirements

For ChainOfThought modules, your signature must include the `reasoning` field:

```python
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    reasoning = dspy.OutputField(desc="Step-by-step reasoning")  # Required for ChainOfThought
    answer = dspy.OutputField(desc="Answer to the question")
```

### Custom Metric Implementation

DSPy 2.6 doesn't support inheriting from `dspy.Metric`. Instead, define a class with `__call__`:

```python
class BibleQAMetric:
    """Metric for evaluating Bible QA responses."""
    
    def __call__(self, example, pred, trace=None):
        # Handle missing answer field
        if not hasattr(pred, 'answer'):
            return 0.0
            
        # Extract answers
        reference = example.answer.strip().lower()
        prediction = pred.answer.strip().lower()
        
        # Calculate score (exact match = 1.0)
        if prediction == reference:
            return 1.0
        
        # Add partial scoring if needed
        return 0.0
```

## PowerShell Compatibility

Our batch files use improved PowerShell commands for running MLflow:

```batch
powershell -Command "$portInUse = $false; try { $connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue; if ($connections) { $portInUse = $true; Write-Host 'Found existing MLflow server on port 5000' } } catch { $portInUse = $false }; if (-not $portInUse) { Write-Host 'Starting new MLflow server...'; Start-Process -FilePath 'mlflow' -ArgumentList 'ui', '--host', '127.0.0.1', '--port', '5000' -WindowStyle Minimized }"
```

This approach:
1. Properly checks if MLflow is already running
2. Only starts a new server if needed
3. Runs MLflow in a minimized window
4. Works reliably on Windows systems

## Troubleshooting

1. **JSON Parsing Errors**:
   - Error: `Expected a JSON object but parsed a <class 'str'>`
   - Solution: Make sure `import dspy_json_patch` comes right after `import dspy`

2. **BetterTogether Parameter Errors**:
   - Error: Messages about unsupported parameters
   - Solution: Remove all parameters except `student` and `trainset`

3. **MLflow Connection Errors**:
   - Error: Unable to connect to MLflow
   - Solution: Run MLflow manually: `mlflow ui --host 127.0.0.1 --port 5000`

4. **LM Studio API Issues**:
   - Error: Connection errors to LM Studio
   - Solution: Verify LM Studio is running with API server enabled
   - Solution: Check your `.env.dspy` file for correct model name

## References

- [DSPy Documentation](https://dspy.ai/)
- [DSPy BetterTogether API](https://dspy.ai/api/optimizers/BetterTogether/)
- [LM Studio Documentation](https://lmstudio.ai/)

## Appendix: Minimal Implementation Example

```python
import dspy
import dspy_json_patch  # Apply the patch

# Enable experimental features
dspy.settings.experimental = True

# Define signature with reasoning field
class BibleQA(dspy.Signature):
    context = dspy.InputField()
    question = dspy.InputField()
    reasoning = dspy.OutputField()  # Required for ChainOfThought
    answer = dspy.OutputField()

# Create simple module
class SimpleBibleQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa = dspy.ChainOfThought(BibleQA)
    
    def forward(self, context, question):
        return self.qa(context=context, question=question)

# Define metric
class BibleQAMetric:
    def __call__(self, example, pred, trace=None):
        if not hasattr(pred, 'answer'):
            return 0.0
        return 1.0 if pred.answer.strip() == example.answer.strip() else 0.0

# Create dataset
examples = [...]  # Your examples here

# Configure DSPy with LM Studio
def configure_dspy():
    lm = dspy.LM(
        model_type="openai",
        model="mistral-nemo-instruct-2407",
        api_base="http://localhost:1234/v1",
        api_key="dummy",
        config={"temperature": 0.1, "max_tokens": 512}  # No response_format
    )
    dspy.configure(lm=lm)

# Optimize
def optimize(model, train_data):
    metric = BibleQAMetric()
    optimizer = dspy.BetterTogether(metric=metric)
    
    try:
        optimized = optimizer.compile(
            student=model,
            trainset=train_data
            # No additional parameters
        )
        return optimized
    except Exception as e:
        print(f"Optimization error: {e}")
        return model  # Fallback to unoptimized model
``` 