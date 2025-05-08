"""
Integration tests for Claude API integration with BibleScholarProject.

These tests verify that the Claude API integration functions correctly with
the BibleScholarProject codebase. They test both the API connection and the
DSPy integration functionality.
"""

import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Import required modules
try:
    from src.dspy_programs.huggingface_integration import configure_claude_model, BibleQAModule
    import dspy
except ImportError:
    pytest.skip("Required modules not found", allow_module_level=True)

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle test skipping
def requires_anthropic_key(func):
    """Decorator to skip tests if no Anthropic API key is available."""
    def wrapper(*args, **kwargs):
        load_dotenv('.env.dspy')
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set in environment")
        try:
            import anthropic
        except ImportError:
            pytest.skip("Anthropic package not installed")
        return func(*args, **kwargs)
    return wrapper

# Test functions
@requires_anthropic_key
def test_claude_api_connection():
    """Test basic connection to the Claude API."""
    import anthropic
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = "What is the first verse of the Bible?"
    response = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    assert response is not None
    assert response.content[0].text is not None
    assert len(response.content[0].text) > 0
    
    # Log the response for debugging
    logger.info(f"Claude API Response: {response.content[0].text}")

@requires_anthropic_key
def test_dspy_claude_integration():
    """Test DSPy integration with Claude."""
    # Configure Claude as the LM for DSPy
    lm = configure_claude_model()
    dspy.settings.configure(lm=lm)
    
    # Define a simple DSPy signature for testing
    class SimpleQA(dspy.Signature):
        question = dspy.InputField()
        answer = dspy.OutputField()
    
    # Create a basic module
    basic_qa = dspy.Predict(SimpleQA)
    
    # Test the module with a simple Bible question
    result = basic_qa(question="What is the first book of the Bible?")
    
    assert result is not None
    assert result.answer is not None
    assert len(result.answer) > 0
    assert "Genesis" in result.answer
    
    # Log the result for debugging
    logger.info(f"DSPy Claude Integration Result: {result.answer}")

@requires_anthropic_key
def test_bible_qa_with_claude():
    """Test the Bible QA module with Claude as the LM."""
    # Configure Claude
    lm = configure_claude_model()
    dspy.settings.configure(lm=lm)
    
    # Create the Bible QA module
    bible_qa = BibleQAModule()
    
    # Test with a simple Bible question
    context = "In the beginning God created the heavens and the earth."
    question = "Who created the heavens and the earth?"
    
    result = bible_qa(context=context, question=question)
    
    assert result is not None
    assert result.answer is not None
    assert len(result.answer) > 0
    assert "God" in result.answer
    
    # Log the result for debugging
    logger.info(f"Bible QA Claude Test Result: {result.answer}")

@requires_anthropic_key
def test_bible_qa_with_theological_question():
    """Test the Bible QA module with a more complex theological question."""
    # Configure Claude
    lm = configure_claude_model()
    dspy.settings.configure(lm=lm)
    
    # Create the Bible QA module
    bible_qa = BibleQAModule()
    
    # Test with a theological question
    context = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
    question = "What does this verse teach about salvation?"
    
    result = bible_qa(context=context, question=question)
    
    assert result is not None
    assert result.answer is not None
    assert len(result.answer) > 0
    
    # Check for key theological concepts in the answer
    theological_terms = ["salvation", "believe", "faith", "eternal", "life", "love"]
    assert any(term in result.answer.lower() for term in theological_terms)
    
    # Log the result for debugging
    logger.info(f"Theological Question Result: {result.answer}")

if __name__ == "__main__":
    # Run tests directly if script is executed
    try:
        test_claude_api_connection()
        print("✓ Claude API connection test passed")
        
        test_dspy_claude_integration()
        print("✓ DSPy Claude integration test passed")
        
        test_bible_qa_with_claude()
        print("✓ Bible QA with Claude test passed")
        
        test_bible_qa_with_theological_question()
        print("✓ Theological question test passed")
        
        print("All Claude integration tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1) 