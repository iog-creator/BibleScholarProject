# Claude API Setup Guide

This guide provides detailed instructions for setting up and configuring the Claude API integration for the BibleScholarProject.

## Prerequisites

Before integrating Claude API, you need:

1. An Anthropic account with API access
2. A valid API key from Anthropic
3. Python 3.8+ with the Anthropic package installed

## Installation

1. Install the Anthropic Python package:

```bash
pip install anthropic>=0.21.0
```

2. Verify the package is installed:

```bash
python -c "import anthropic; print(f'Anthropic package version: {anthropic.__version__}')"
```

## Configuration

### Setting Environment Variables

1. Copy the example environment file if you haven't already:

```bash
cp .env.example.dspy .env.dspy
```

2. Edit the `.env.dspy` file and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-3-opus-20240229
```

3. Choose the appropriate Claude model for your needs:
   - `claude-3-opus-20240229`: Highest quality, most capabilities
   - `claude-3-sonnet-20240229`: Balanced quality and speed
   - `claude-3-haiku-20240307`: Fastest, least expensive option

### Verifying Setup

Run the Claude API integration test script to verify everything is working:

```bash
python scripts/test_claude_integration.py
```

If successful, you should see output confirming all tests passed.

## Usage Options

### Using Claude as Teacher Model

To train a T5 model using Claude as the teacher:

```bash
python train_t5_bible_qa.py --teacher "claude-3-opus-20240229" --optimizer "bootstrap" --track-with-mlflow
```

This will utilize Claude's knowledge to optimize the smaller T5 model.

### Using Claude Directly for Inference

To use Claude directly for Bible QA without a local model:

```bash
python bible_qa_api.py --use-claude
```

This will start the Bible QA API server using Claude for inference.

### Testing with Claude

You can test the Claude integration with:

```bash
test_claude_integration.bat
```

This batch file tests all aspects of Claude integration.

## Troubleshooting

### Common Issues

1. **API Key Invalid or Not Found**
   - Verify the API key is correctly entered in `.env.dspy`
   - Check for extra spaces or newlines in the API key
   - Try regenerating the API key in your Anthropic dashboard

2. **Package Installation Problems**
   - Make sure `anthropic>=0.21.0` is listed in `requirements.txt`
   - Try reinstalling with `pip install -U anthropic`

3. **Authorization Errors**
   - Ensure your Anthropic account has API access enabled
   - Check if your API usage quota is exhausted
   - Verify the API key has the correct permissions

4. **Model Not Available**
   - Verify the model name is spelled correctly
   - Check if the specified model is available in your Anthropic subscription
   - Try a different model if the specified one is unavailable

### Getting Support

If you encounter issues that aren't covered here:

1. Check the Anthropic documentation: https://docs.anthropic.com/
2. Review the error logs in the `logs/` directory
3. Consult the project's error handling documentation

## Best Practices

1. **API Key Security**
   - Never commit your API key to version control
   - Use environment variables for API keys
   - Restrict API key permissions to only what's needed

2. **Cost Management**
   - Monitor your API usage regularly
   - Use lower-tier models for testing
   - Consider batching requests when possible

3. **Fallback Mechanisms**
   - Always have a local model as fallback
   - Implement proper error handling
   - Set up timeouts for API requests

4. **Local Development**
   - For development, consider using local models instead of the API
   - Test thoroughly with smaller contexts before large batch operations 