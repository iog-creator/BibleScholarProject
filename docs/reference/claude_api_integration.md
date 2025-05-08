# Claude API Integration Reference

This reference document details the integration between BibleScholarProject and Anthropic's Claude API.

## Overview

The BibleScholarProject can use Anthropic's Claude API as an alternative to local models or HuggingFace models. Claude integration provides:
- High-quality teacher models for DSPy training
- Advanced reasoning capabilities for Bible question answering
- Consistency in theological explanations
- Integration with existing DSPy framework

## Environment Configuration

Claude API integration is configured through environment variables in `.env.dspy`:

```
# Anthropic/Claude API configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-3-opus-20240229
```

Available Claude models:
- `claude-3-opus-20240229` (highest quality)
- `claude-3-sonnet-20240229` (balanced quality/speed)
- `claude-3-haiku-20240307` (fastest)
- `claude-2.1` (legacy)
- `claude-2.0` (legacy)

## Usage Scenarios

### Teacher-Student DSPy Training

Claude can be used as a high-quality teacher model in the DSPy framework, guiding smaller models like T5:

```python
# Configure Claude as teacher
from src.dspy_programs.huggingface_integration import configure_claude_model
teacher_lm = configure_claude_model()

# Configure local student model
student_lm = configure_local_student_model(model_name="google/flan-t5-small")

# Train with Claude as teacher
compiled_model = train_and_compile_model(teacher_lm, student_lm, examples)
```

### Direct Bible QA

Claude can directly answer Bible questions without using a local model:

```python
# Use Claude for Bible QA
python bible_qa_api.py --use-claude --claude-model="claude-3-opus-20240229"
```

## Implementation Details

### DSPy Integration

The project integrates Claude with DSPy using the Anthropic Python client:

```python
def configure_claude_model(api_key=None, model_name=None):
    """Configure DSPy to use Anthropic's Claude API as the teacher model."""
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    model_name = model_name or os.environ.get('CLAUDE_MODEL') or 'claude-3-opus-20240229'
    
    # Create Claude DSPy LM
    lm = dspy.ClaudeLM(
        model=model_name,
        api_key=api_key,
        temperature=0.3,
        max_tokens=1024
    )
    dspy.configure(lm=lm)
    return lm
```

### API Endpoints

The Bible QA API has been extended to support Claude:

`POST /api/question` 
- Works with Claude when launched with `--use-claude`
- Same interface as the standard endpoint

### Testing and Verification

The project includes test scripts to verify Claude integration:

```bash
# Test Claude integration
python scripts/test_claude_integration.py

# Or use the batch file
test_claude_integration.bat
```

## Performance Considerations

When using Claude API:

1. **Latency**: API calls introduce network latency
2. **Costs**: Claude API usage incurs costs based on token usage
3. **Quality**: Claude models typically provide higher quality than local models
4. **Reliability**: Depends on internet connectivity and Anthropic API availability

## Error Handling

The system includes comprehensive error handling for Claude integration:

```python
try:
    # Attempt to use Claude
    from src.dspy_programs.huggingface_integration import configure_claude_model
    lm = configure_claude_model(api_key=api_key, model_name=model_name)
except Exception as e:
    logger.error(f"Error initializing Claude: {e}")
    # Fall back to other models
    initialize_local_model()
```

## Command Line Options

The following command line options are available for Claude integration:

```
python bible_qa_api.py --use-claude             # Use Claude API with default model
python bible_qa_api.py --use-claude --claude-model=claude-3-sonnet-20240229   # Specify model
python bible_qa_api.py --test --use-claude      # Test with Claude before starting
```

## Best Practices

1. **API Key Security**: Store your API key securely in `.env.dspy`
2. **Cost Management**: Use a lower-tier Claude model for testing
3. **Hybrid Approach**: Use Claude as teacher, local models for inference
4. **Fallback Handling**: Implement proper fallbacks to local models
5. **Token Optimization**: Craft prompts carefully to minimize token usage 