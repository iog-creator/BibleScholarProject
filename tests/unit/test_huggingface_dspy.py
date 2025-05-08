"""
Unit tests for the HuggingFace DSPy integration.
"""
import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test
try:
    from src.dspy_programs.huggingface_integration import (
        configure_huggingface_model,
        BibleQAModule,
        load_training_data,
        theological_accuracy_metric,
    )
except ImportError:
    print("Could not import HuggingFace DSPy integration modules")

class TestHuggingFaceDSPyIntegration(unittest.TestCase):
    """Tests for the HuggingFace DSPy integration."""
    
    @patch('dspy.LM')
    @patch('dspy.configure')
    def test_configure_huggingface_model(self, mock_configure, mock_lm):
        """Test configuring HuggingFace model."""
        # Mock the LM instance
        mock_lm_instance = MagicMock()
        mock_lm.return_value = mock_lm_instance
        
        # Call the function with test parameters
        result = configure_huggingface_model(
            model_name="test-model",
            api_key="test-api-key",
            provider="test-provider"
        )
        
        # Check that LM was created with correct parameters
        mock_lm.assert_called_once_with(
            "huggingface/test-model",
            api_key="test-api-key",
            provider="test-provider"
        )
        
        # Check that dspy.configure was called with the LM
        mock_configure.assert_called_once_with(lm=mock_lm_instance)
        
        # Check that the function returns the LM
        self.assertEqual(result, mock_lm_instance)
    
    def test_theological_accuracy_metric(self):
        """Test the theological accuracy metric."""
        # Create mock example and prediction
        example = MagicMock()
        example.answer = "God"
        
        pred = MagicMock()
        pred.answer = "God"
        
        # Test exact match
        score = theological_accuracy_metric(example, pred)
        self.assertEqual(score, 1.0)
        
        # Test case insensitive match
        pred.answer = "god"
        score = theological_accuracy_metric(example, pred)
        self.assertEqual(score, 1.0)
        
        # Test mismatch
        pred.answer = "Angels"
        score = theological_accuracy_metric(example, pred)
        self.assertEqual(score, 0.0)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_load_training_data_file_not_found(self, mock_open, mock_exists):
        """Test loading training data when file doesn't exist."""
        # Setup mock
        mock_exists.return_value = False
        
        # Call function
        result = load_training_data("nonexistent_file.jsonl")
        
        # Check result
        self.assertEqual(result, [])
        mock_open.assert_not_called()
    
    def test_bible_qa_module(self):
        """Test creating a BibleQAModule instance."""
        # Create a module
        module = BibleQAModule()
        
        # Check it has a qa_model attribute
        self.assertTrue(hasattr(module, 'qa_model'))
        
        # Check it has a forward method
        self.assertTrue(callable(getattr(module, 'forward', None)))

if __name__ == '__main__':
    unittest.main() 