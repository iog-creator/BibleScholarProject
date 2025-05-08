# DSPy 2.6 with LM Studio Integration

This guide provides comprehensive rules and patterns for working with DSPy 2.6 with LM Studio integration in the BibleScholarProject.

## Core Components

1. **Environment Configuration**
   - Always use environment variables loaded with `load_dotenv('.env.dspy')` before any DSPy imports
   - Required environment variables:
     ```
     LM_STUDIO_API_URL=http://127.0.0.1:1234/v1
     LM_STUDIO_CHAT_MODEL=mistral-nemo-instruct-2407
     LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
     ```
   - Always enable experimental features after import: `dspy.settings.experimental = True`

2. **LM Studio Configuration**
   - Configure DSPy to use LM Studio with this pattern:
     ```python
     def configure_lm_studio():
         """Configure DSPy to use LM Studio."""
         try:
             lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
             model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
             lm = dspy.LM(
                 model_type="openai",
                 model=model_name,
                 api_base=lm_studio_api,
                 api_key="dummy",
                 config={"temperature": 0.1, "max_tokens": 1024}
             )
             dspy.configure(lm=lm)
             return True
         except Exception as e:
             logger.error(f"LM Studio configuration failed: {e}")
             return False
     ```
   - NEVER use the `response_format` parameter with LM Studio
   - Always use the `dspy_json_patch` module to handle string responses

3. **DSPy Components**
   - Use descriptive `Signature` classes with meaningful field descriptions
   - Add assertion statements in module forward methods for theological verification when relevant
   - Include multi-turn conversation support with a `history` field

4. **Module Structure**
   - Top-level module should inherit from `dspy.Module`
   - Use `ChainOfThought` for complex reasoning tasks
   - Always handle the `history` parameter with a default value: `history=None` and use `history or []`

## Optimizer Selection

1. **LM Studio Compatible Optimizers**
   - **BootstrapFewShot**: Primary optimizer for LM Studio (recommended)
   - **BetterTogether**: Can be used but has more compatibility issues
   - AVOID: Optimizers that require fine-tuning or model weight changes

2. **Optimization Pattern**
   - Use MLflow for experiment tracking:
     ```python
     mlflow.set_experiment("bible_qa_optimization")
     with mlflow.start_run(run_name=f"{optimizer_name}_{int(time.time())}"):
         # Log parameters
         mlflow.log_param("optimizer", optimizer_name)
         mlflow.log_param("train_examples", len(train_data))
         
         # Optimize
         optimized_model = optimizer.compile(student=model, trainset=train_data)
         
         # Log metrics
         mlflow.log_metric("optimized_accuracy", accuracy)
     ```
   - Always calculate base accuracy before optimization for comparison
   - Use clear, descriptive metrics

## Dataset Handling

1. **Dataset Format**
   - Use JSONL format with fields: `context`, `question`, `answer`, `history`
   - Convert to DSPy Examples with `.with_inputs("context", "question", "history")`
   - Store datasets in `data/processed/bible_training_data/`

2. **Dataset Preparation**
   - Use `prepare_training_data.py` to ensure datasets exist in the right location
   - Generate fallback data if needed with theological accuracy
   - Include Strong's IDs (e.g., "H430") for Hebrew terms

## Testing and Workflow

1. **Testing Pattern**
   - Test in both single-turn and multi-turn conversation modes
   - Use the interactive mode for manual testing: `test_optimized_bible_qa.py --conversation`
   - Save sample predictions for analysis

2. **Complete Workflow**
   - Use `train_and_test_dspy.bat` to orchestrate the full workflow:
     1. Prepare training data
     2. Train and optimize model
     3. Test the optimized model
   - Log all steps and results comprehensively

## MLflow Integration

1. **Experiment Tracking**
   - Use MLflow for tracking all optimization runs
   - Log parameters, metrics, and artifacts consistently
   - Save models with `model.save()` for local access
   - Name runs with a combination of optimizer and timestamp

2. **Result Analysis**
   - Use `analyze_mlflow_results.py` to analyze optimization results
   - Compare different optimization approaches
   - Use the `--visualize` flag for visual analysis

## Error Handling

1. **Robust Error Handling**
   - Use try/except blocks around all API calls
   - Log detailed error messages
   - Provide fallbacks for failed operations
   - Handle DSPy JSON parsing errors with the custom patch

2. **Common Issues**
   - LM Studio API unavailable: Check if server is running on the correct port
   - JSON parsing errors: Ensure dspy_json_patch is imported before any DSPy operations
   - Model not found: Verify the model is loaded in LM Studio
   - Theological terms missing: Update assertion statements and metric

## Theological Considerations

1. **Term Verification**
   - Verify theological terms are correctly used (e.g., "Elohim" for "God")
   - Include Strong's IDs when relevant (e.g., "H430" for "Elohim")
   - Use assertions to ensure theological accuracy in answers

2. **Biblical References**
   - Use standard biblical reference format (e.g., "John 3:16")
   - Ensure verse text is accurately quoted
   - Check theological consistency between questions and answers

By following these guidelines, you'll ensure consistent DSPy 2.6 integration with LM Studio in the BibleScholarProject. 