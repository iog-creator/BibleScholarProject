# LM Studio + DSPy Integration
> **Note:** For the Contextual Insights feature, minimal LM Studio integration bypasses the DSPy JSON patches described below. This document applies to DSPy-based modules and future enhancements.

## Recent Integration Work

The team recently solved a critical integration issue between DSPy and LM Studio that was preventing reliable structured JSON output from DSPy modules. The key discoveries and solutions were:

1. **JSON Schema Format Requirements**: LM Studio requires a specific double-nested format for JSON schemas that differs from standard OpenAI format:
   ```
   response_format = {
     "type": "json_schema", 
     "json_schema": {
       "schema": { ... actual schema ... }
     }
   }
   ```

2. **Dynamic Schema Generation**: DSPy's dynamic signatures require runtime schema extraction. We developed a patch that:
   - Uses Python's `inspect` module to extract the current signature from the call stack
   - Builds a schema with output fields from the signature as required string properties
   - Injects this schema into LM Studio calls with the correct nesting structure

3. **Patch Components**: The `dspy_json_patch.py` file intercepts DSPy's calls to LM Studio and:
   - Detects if LM Studio is being used as the backend
   - Extracts signature information (output fields and descriptions)
   - Constructs a properly nested schema matching the signature
   - Replaces any generic 'output' field with specific fields from the signature

This integration enables all DSPy modules to work reliably with LM Studio's local models, supporting the full range of DSPy functionality including optimization, training, and multi-module pipelines.

## Overview

This documentation covers the integration of LM Studio (a local inference server) with DSPy (a framework for LLM pipelines) in the BibleScholarProject, including structured JSON output handling, schema generation, and optimization.

LM Studio provides an OpenAI-compatible API for running local LLMs, but there are specific challenges when integrating with DSPy for structured JSON output:

1. **Schema format differences**: LM Studio requires a specific nested format for JSON schemas
2. **Dynamic signature handling**: DSPy modules have dynamically generated output signatures
3. **Optimization requirements**: Training and optimizing modules requires consistent JSON formatting

This integration solves these challenges through a custom patch that:
- Dynamically generates JSON schemas from DSPy signatures
- Applies the correct schema nesting format for LM Studio
- Facilitates optimization and reliable structured output from local models

## Components

The LM Studio + DSPy integration includes:

- `dspy_json_patch.py`: Core patch to handle JSON schema generation and integration
- `scripts/data/direct_lmstudio_json_test.py`: Test script for direct LM Studio API calls
- `scripts/data/run_direct_test_with_optimized_module.py`: Comparison between DSPy and direct API
- `scripts/data/optimize_verse_summary_module.py`: Example of DSPy optimization with LM Studio

## Key Integration Points

### JSON Schema Format

LM Studio requires a specific double-nested schema structure when using the `response_format` parameter:

```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "Description of the field"
                }
            },
            "required": ["field_name"]
        }
    }
}
```

This differs from other implementations which may use different nesting levels.

### Dynamic Schema Generation

The patch extracts the output field specifications from DSPy signatures using Python's `inspect` module:

```python
# Simplified example
signature = get_signature_from_call_stack()
if signature and hasattr(signature, 'output_fields'):
    for field in signature.output_fields:
        schema_properties[field] = {"type": "string"}
        schema_required.append(field)
```

### Prompt Engineering for Reliable Output

For best results with structured JSON output:

1. **Include explicit examples** in prompts and training data:
   ```
   Respond ONLY with a JSON object in this format: {"summary_text": "..."}
   ```

2. **Include multiple examples** for different input types:
   ```
   Verse: For God so loved the world...
   Output: {"summary_text": "God's love and the promise of eternal life..."}
   
   Topic: The Beatitudes
   Output: {"summary_text": "Jesus' teachings on blessings..."}
   ```

3. **Use appropriate temperature** (0.2-0.3) to ensure consistent outputs

## Example Implementation

### Patching DSPy for LM Studio

```python
# Setup DSPy with LM Studio
lm_studio_lm = dspy.LM(
    "openai/mistral-nemo-instruct-2407@q4_k_m",
    api_base="http://localhost:1234/v1",
    api_key="sk-dummykeyforlocal",
    temperature=0.3
)
dspy.settings.configure(lm=lm_studio_lm)

# Apply the JSON schema patch to ensure correct schema format
from dspy_json_patch import apply_all_patches
apply_all_patches()
```

### Creating a DSPy Module with Compatible Output

```python
import dspy

class GenerateSummarySignature(dspy.Signature):
    """Generate a concise summary of a Bible verse or topic."""
    context_text = dspy.InputField(desc="Text of the Bible verse or topic description")
    focus_reference_or_topic = dspy.InputField(desc="Bible reference or topic name")
    summary_text = dspy.OutputField(desc="A concise summary of the verse or topic")

summarizer = dspy.Predict(GenerateSummarySignature)
```

## Training and Optimization

The integration supports DSPy's optimization methods, which improve the model's ability to generate correctly structured JSON:

```python
# Example of optimization
from dspy.teleprompt import BootstrapFewShot

# Load training examples
trainset = [dspy.Example(...) for example in examples]

# Create optimizer
bootstrapper = BootstrapFewShot(metric="exact_match")

# Optimize the module
compiled_summarizer = bootstrapper.compile(summarizer, trainset=trainset)
```

## Handling Different Input Types

When working with different input types (e.g., verses, topics, snippets), structure your DSPy module to handle each type:

```python
def forward(self, context_text, focus_reference_or_topic):
    # Format the input based on type
    if is_verse(focus_reference_or_topic):
        input_block = f"Verse: {context_text}\nReference: {focus_reference_or_topic}"
    elif is_topic(focus_reference_or_topic):
        input_block = f"Topic: {focus_reference_or_topic}"
    else:
        input_block = f"Snippet: {context_text}"
        
    # Generate prediction with formatted input
    prediction = self.generate(input_block=input_block)
    return prediction
```

## Troubleshooting

Common issues and their solutions:

1. **Empty JSON response (`{}`)**: 
   - Ensure you're using explicit JSON format instructions in your prompt
   - Add multiple few-shot examples for the model to follow
   - Use a lower temperature (0.2-0.3) for more consistent outputs

2. **Missing required fields**:
   - Check that field names in DSPy signature match what you're expecting
   - Use the `direct_lmstudio_json_test.py` script to test direct API calls
   - Compare DSPy vs. direct API responses with the comparison script

3. **Schema format errors**:
   - Verify the dspy_json_patch is applied correctly
   - Check for error messages about JSON schema formatting
   - Ensure schema properties match signature output fields

## Related Documentation

- [DSPy Usage in BibleScholarProject](./dspy_usage.md)
- [MLflow DSPy Integration](./MLFLOW_DSPY_INTEGRATION.md)
- [Hugging Face DSPy Integration](./HUGGINGFACE_DSPY_INTEGRATION.md)
- [LM Studio API Documentation](https://lmstudio.ai/docs/app/api)

## Version Compatibility

This integration has been tested with:
- LM Studio 0.2.9+
- DSPy 2.6+
- Python 3.10+
- Mistral, Llama, and other model families

## Future Work

Future enhancements to the integration include:
- Support for more complex nested schemas
- Integration with DSPy's RM (Retrieval Module) for combined RAG workflows
- Automated testing and validation of schema compliance
- Pre-built optimized modules for common biblical analysis tasks

> **Note:** The Contextual Insights feature now uses direct LM Studio minimal integration (`contextual_insights_minimal.py`) and bypasses the DSPy JSON patches described here. This document applies to other DSPy-based modules and future enhancements. 