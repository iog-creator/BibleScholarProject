# DSPy Migration Guide: 2.5 to 2.6

This document provides information about the migration from DSPy 2.5.x to DSPy 2.6.x in the BibleScholarProject.

> **Status**: ✅ Migration Completed
> 
> The BibleScholarProject has been successfully migrated to DSPy 2.6.0 using the `scripts/upgrade_to_dspy26.py` script.

## Migration Implementation

The migration to DSPy 2.6 was completed with the following key changes:

1. **Installation Update**: Upgraded to DSPy 2.6.0 via pip
2. **Client API Migration**: Replaced all `GPT3` instances with the unified `dspy.LM` interface
3. **Configuration Updates**: Changed `dspy.settings.configure()` to `dspy.configure()`
4. **Model References**: Added provider prefixes to model names (e.g., `openai/{model_name}`)
5. **Parameter Updates**: Added explicit `model_type` specifications for all LM instances
6. **Langfuse Handling**: Disabled Langfuse integration causing `NoneType has no len()` errors

## Original Overview of Changes

DSPy 2.6 introduced several breaking changes that required updates to our codebase:

1. **Deprecated LM Clients**: All LM clients except `dspy.LM` are now deprecated and will be removed
2. **New Chat Interface**: The API for chat models has been standardized across providers
3. **Adapters**: Added support for adapters that improve consistency of LM outputs
4. **Removal of Legacy Client Interfaces**: GPT3, Anthropic, and other legacy clients will be removed

## Migration Steps

### 1. Replace Legacy LM Clients with `dspy.LM`

#### Before (DSPy 2.5):
```python
import dspy
teacher_lm = dspy.GPT3(model="text-davinci-003")
dspy.settings.configure(lm=teacher_lm)
```

#### After (DSPy 2.6):
```python
import dspy
teacher_lm = dspy.LM(model="openai/text-davinci-003")
dspy.configure(lm=teacher_lm)
```

### 2. Update Configuration Method

#### Before (DSPy 2.5):
```python
dspy.settings.configure(lm=lm, temperature=0.7)
```

#### After (DSPy 2.6):
```python
dspy.configure(lm=lm, temperature=0.7)
```

### 3. Update LM Studio Integration

#### Before (DSPy 2.5):
```python
lm = dspy.GPT3(model=model_name, api_base=api_base)
```

#### After (DSPy 2.6):
```python
lm = dspy.LM(f"openai/{model_name}", api_base=api_base, api_key="lm-studio")
```

### 4. Update Model Types and Parameters

#### Before (DSPy 2.5):
```python
lm = dspy.GPT3(model=model_name, temperature=0.7, max_tokens=100)
```

#### After (DSPy 2.6):
```python
lm = dspy.LM(f"openai/{model_name}", temperature=0.7, max_tokens=100, 
             model_type='text-completion')  # or 'chat' for chat models
```

## LM Studio Integration

When using LM Studio with DSPy 2.6, follow these guidelines:

```python
# For chat models in LM Studio
lm = dspy.LM(
    f"openai/{model_name}",  # e.g., "openai/darkidol-llama-3.1-8b-instruct-1.2-uncensored"
    api_base="http://localhost:1234/v1",
    api_key="lm-studio",
    model_type='chat'
)

# For text completion models in LM Studio
lm = dspy.LM(
    f"openai/{model_name}",  # e.g., "openai/gguf-flan-t5-small"
    api_base="http://localhost:1234/v1",
    api_key="lm-studio",
    model_type='text-completion'
)

# For embedding models in LM Studio
embedding_lm = dspy.LM(
    f"openai/{embedding_model}",  # e.g., "openai/text-embedding-nomic-embed-text-v1.5@q8_0"
    api_base="http://localhost:1234/v1",
    api_key="lm-studio",
    model_type='embedding'
)
```

## Using Adapters (New in 2.6)

DSPy 2.6 introduces adapters to improve output consistency:

```python
import dspy

# Create the base LM
lm = dspy.LM("openai/darkidol-llama-3.1-8b-instruct-1.2-uncensored", 
             api_base="http://localhost:1234/v1",
             api_key="lm-studio")

# Add JSON adapter to ensure structured JSON output
lm_with_json = lm.with_adapter('json')

# Configure DSPy to use this LM
dspy.configure(lm=lm_with_json)
```

## FAQ

### Q: Why are we getting deprecation warnings?

A: DSPy 2.5 marks certain LM clients as deprecated to prepare for their removal in DSPy 2.6. These warnings don't affect functionality in 2.5 but indicate code that needs to be changed before upgrading.

### Q: Do we need to migrate immediately?

A: No, our code will continue to work with DSPy 2.5.x. However, we should plan to migrate before upgrading to DSPy 2.6.

### Q: Will we lose functionality when migrating?

A: No, the new `dspy.LM` interface provides all the same functionality with a more consistent API across different LM providers.

### Q: How do I verify my migration was successful?

A: After updating your code, run tests to ensure your modules still work as expected. If no deprecation warnings appear, your migration was successful.

## Full Migration Example

Here's a complete example of migrating a BibleQA module:

### Before (DSPy 2.5):

```python
import dspy
from dspy.retrieve import Retrieve

# Configure LM
teacher_lm = dspy.GPT3(model="gpt-3.5-turbo")
dspy.settings.configure(lm=teacher_lm)

# Define signature
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="The Bible verse or passage")
    question = dspy.InputField(desc="Question about the verse")
    answer = dspy.OutputField(desc="Answer to the question")

# Create module
class BibleQAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQA)
    
    def forward(self, context, question):
        return self.qa_model(context=context, question=question)
```

### After (DSPy 2.6):

```python
import dspy
from dspy.retrieve import Retrieve

# Configure LM (new way)
teacher_lm = dspy.LM("openai/gpt-3.5-turbo")
dspy.configure(lm=teacher_lm)  # Note: configure() not settings.configure()

# Define signature (no change)
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="The Bible verse or passage")
    question = dspy.InputField(desc="Question about the verse")
    answer = dspy.OutputField(desc="Answer to the question")

# Create module (no change)
class BibleQAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQA)
    
    def forward(self, context, question):
        return self.qa_model(context=context, question=question)
```

## References

- [DSPy Documentation](https://dspy.ai)
- [DSPy Migration Guide - Official](https://github.com/stanfordnlp/dspy/blob/main/examples/migration.ipynb)
- [DSPy 2.6 Release Notes](https://github.com/stanfordnlp/dspy/releases) 