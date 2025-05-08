#!/usr/bin/env python3
"""
Test module for DSPy LM Studio integration
"""
import dspy

class SimpleModule(dspy.Module):
    """A simple module for testing save/load functionality."""
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict("question -> answer")
    
    def forward(self, question):
        return self.predictor(question=question)

def get_model():
    """Return a fresh instance of the model."""
    return SimpleModule()
