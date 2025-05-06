"""
Documentation Organizer Module

This module provides DSPy-based functionality for:
1. Creating documentation organization solutions
2. Identifying patterns in documentation
3. Generating implementation plans
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import dspy

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data/processed/dspy_training_data')
TRAINING_FILE = 'documentation_organization_formatted.jsonl'

class DocumentationOrganization(dspy.Signature):
    """Generate solutions for documentation organization problems."""
    problem = dspy.InputField(desc="Documentation organization problem to solve")
    solution = dspy.OutputField(desc="Proposed solution to the problem")
    steps = dspy.OutputField(desc="List of implementation steps")
    patterns = dspy.OutputField(desc="Documentation patterns applied in this solution")

class DocumentationOrganizer(dspy.Module):
    """Module for generating documentation organization solutions."""
    
    def __init__(self, use_cot: bool = True):
        super().__init__()
        
        # Use Chain of Thought for better reasoning
        if use_cot:
            self.solver = dspy.ChainOfThought(DocumentationOrganization)
        else:
            self.solver = dspy.Predict(DocumentationOrganization)
    
    def forward(self, problem: str) -> dspy.Prediction:
        """Generate a solution for a documentation organization problem."""
        return self.solver(problem=problem)

class DocumentationPatternAnalyzer(dspy.Module):
    """Module for analyzing documentation patterns in existing files."""
    
    def __init__(self):
        super().__init__()
        self.pattern_finder = dspy.ChainOfThought("documentation_content -> patterns")
    
    def forward(self, documentation_content: str) -> List[str]:
        """Identify documentation patterns in the provided content."""
        result = self.pattern_finder(documentation_content=documentation_content)
        # Convert patterns string to list if necessary
        if isinstance(result.patterns, str):
            return [p.strip() for p in result.patterns.split(',')]
        return result.patterns

def load_training_examples(file_path: Optional[str] = None) -> List[dspy.Example]:
    """Load training examples from the JSONL file."""
    if file_path is None:
        file_path = DATA_DIR / TRAINING_FILE
    else:
        file_path = Path(file_path)
    
    logger.info(f"Loading documentation examples from {file_path}")
    
    examples = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('//') or not line.strip():
                    continue
                    
                data = json.loads(line)
                # Parse the output sections
                output_parts = data['output'].split('\n\n')
                solution = output_parts[0].replace('SOLUTION: ', '')
                
                steps_part = output_parts[1].replace('IMPLEMENTATION STEPS:\n', '')
                steps = [s.strip('- ') for s in steps_part.split('\n')]
                
                patterns_part = output_parts[2].replace('PATTERNS:\n', '')
                patterns = [p.strip('- ') for p in patterns_part.split('\n')]
                
                # Create and add the example
                example = dspy.Example(
                    problem=data['input'].replace('DOCUMENTATION PROBLEM: ', ''),
                    solution=solution,
                    steps=steps,
                    patterns=patterns
                ).with_inputs('problem')
                
                examples.append(example)
                
        logger.info(f"Loaded {len(examples)} documentation organization examples")
        return examples
    except Exception as e:
        logger.error(f"Error loading examples: {e}")
        return []

def train_documentation_organizer(
    trainset: List[dspy.Example], 
    valset: Optional[List[dspy.Example]] = None,
    optimizer_name: str = "bootstrap",
    metric_fn = None,
    save_path: Optional[str] = None
) -> DocumentationOrganizer:
    """Train a documentation organizer using the specified optimizer."""
    
    if valset is None and trainset:
        # Use last example as validation if no validation set provided
        valset = trainset[-1:]
        trainset = trainset[:-1]
    
    # Default metric if none provided
    if metric_fn is None:
        def pattern_quality(pred, gold, trace=None):
            # Evaluate pattern quality using Jaccard similarity
            pred_patterns = set(p.lower() for p in pred.patterns)
            gold_patterns = set(p.lower() for p in gold.patterns)
            
            # Return 0 if either set is empty
            if not pred_patterns or not gold_patterns:
                return 0.0
                
            # Calculate overlap
            intersection = len(pred_patterns.intersection(gold_patterns))
            union = len(pred_patterns.union(gold_patterns))
            
            return intersection / union
        
        metric_fn = pattern_quality
    
    # Create the model and optimizer
    model = DocumentationOrganizer()
    
    # Choose the optimizer based on name
    if optimizer_name.lower() == "bootstrap":
        from dspy.teleprompt import BootstrapFewShot
        optimizer = BootstrapFewShot(metric=metric_fn)
    elif optimizer_name.lower() == "dsp":
        from dspy.teleprompt import LabeledFewShot
        optimizer = LabeledFewShot(metric=metric_fn)
    elif optimizer_name.lower() == "simba":
        from dspy.teleprompt import SIMBA
        optimizer = SIMBA(metric=metric_fn)
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")
    
    # Compile the model
    logger.info(f"Training DocumentationOrganizer with {optimizer_name} optimizer")
    optimized_model = optimizer.compile(model, trainset=trainset, valset=valset)
    
    # Save the model if requested
    if save_path:
        logger.info(f"Saving optimized model to {save_path}")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        optimized_model.save(save_path)
    
    return optimized_model

def generate_solution(model: DocumentationOrganizer, problem: str) -> Dict[str, Any]:
    """Generate a solution for a documentation problem."""
    result = model(problem=problem)
    
    return {
        "problem": problem,
        "solution": result.solution,
        "steps": result.steps,
        "patterns": result.patterns
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Configure DSPy with a default language model
    try:
        # Try to use OpenAI first
        lm = dspy.OpenAI(model="gpt-3.5-turbo")
        dspy.settings.configure(lm=lm)
    except:
        try:
            # Fall back to Anthropic if available
            lm = dspy.Anthropic(model="claude-instant-1")
            dspy.settings.configure(lm=lm)
        except:
            logger.warning("Could not configure a language model - please set one up manually")
    
    # Load examples and train a model for basic testing
    examples = load_training_examples()
    if examples:
        # Use 80% for training, 20% for validation
        split_point = int(0.8 * len(examples))
        trainset, valset = examples[:split_point], examples[split_point:]
        
        # Train a model
        model = train_documentation_organizer(
            trainset=trainset,
            valset=valset,
            optimizer_name="bootstrap",
            save_path="models/documentation_organizer.dspy"
        )
        
        # Test with a sample problem
        test_problem = "API documentation is inconsistent across different endpoints"
        solution = generate_solution(model, test_problem)
        
        # Print the result
        print("\nTest Result:")
        print(f"Problem: {solution['problem']}")
        print(f"Solution: {solution['solution']}")
        print("\nImplementation Steps:")
        for i, step in enumerate(solution['steps'], 1):
            print(f"{i}. {step}")
        print("\nDocumentation Patterns:")
        for pattern in solution['patterns']:
            print(f"- {pattern}") 