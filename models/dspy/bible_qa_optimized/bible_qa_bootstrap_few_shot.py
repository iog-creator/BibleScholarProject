#!/usr/bin/env python3
"""
Bible QA model optimized with DSPy 2.6
"""
import dspy

class BibleQASignature(dspy.Signature):
    """Answer questions about Bible verses with theological accuracy."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns", default=[])
    answer = dspy.OutputField(desc="Answer to the question")

class BibleQAModule(dspy.Module):
    """Chain of Thought module for Bible QA."""
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQASignature)

    def forward(self, context, question, history=None):
        prediction = self.qa_model(context=context, question=question, history=history or [])
        return prediction

def get_model():
    """Return a fresh instance of the model."""
    return BibleQAModule()
