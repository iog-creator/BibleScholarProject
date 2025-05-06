#!/usr/bin/env python
"""
Documentation Pattern Training Script

This script demonstrates how to load and use the documentation organization
patterns dataset for training AI models to recognize and implement good 
documentation practices.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/documentation_training.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data/processed/dspy_training_data')
DOCUMENTATION_DATASET = DATA_DIR / 'documentation_organization_dataset.jsonl'

def load_dataset():
    """Load the documentation organization dataset."""
    logger.info(f"Loading documentation organization dataset from {DOCUMENTATION_DATASET}")
    
    try:
        examples = []
        with open(DOCUMENTATION_DATASET, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('//') or not line.strip():
                    continue
                    
                example = json.loads(line)
                examples.append(example)
                
        logger.info(f"Loaded {len(examples)} documentation organization examples")
        return examples
    except Exception as e:
        logger.error(f"Error loading dataset: {e}", exc_info=True)
        sys.exit(1)

def create_training_examples(examples):
    """Convert raw examples to input/output training pairs for DSPy."""
    training_examples = []
    
    for example in examples:
        # Convert problem/solution to input/output format
        training_example = {
            "input": f"DOCUMENTATION PROBLEM: {example['problem']}",
            "output": f"SOLUTION: {example['solution']}\n\nIMPLEMENTATION STEPS:\n" + 
                      "\n".join([f"- {step}" for step in example['implementation_steps']]) +
                      "\n\nPATTERNS:\n" + 
                      "\n".join([f"- {pattern}" for pattern in example['patterns']])
        }
        
        training_examples.append(training_example)
        
    return training_examples

def save_formatted_examples(examples, output_file):
    """Save the formatted examples to a JSONL file."""
    output_path = DATA_DIR / output_file
    logger.info(f"Saving {len(examples)} formatted examples to {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("// Formatted documentation organization examples for training\n")
            f.write(f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for example in examples:
                f.write(json.dumps(example) + "\n")
                
        logger.info("Successfully saved formatted examples")
    except Exception as e:
        logger.error(f"Error saving formatted examples: {e}", exc_info=True)

def demonstrate_dspy_usage():
    """Demonstrate how to use the dataset with DSPy."""
    logger.info("Demonstrating DSPy usage for documentation pattern learning")
    
    try:
        # This is just a demonstration - not actual execution
        code = """
        import dspy
        import json
        from pathlib import Path
        
        # Load formatted examples
        dataset_path = Path('data/processed/dspy_training_data/documentation_organization_formatted.jsonl')
        
        # Define input/output signature for documentation organization
        class DocumentationOrganization(dspy.Signature):
            \"\"\"Generate solutions for documentation organization problems.\"\"\"
            problem = dspy.InputField(desc="Documentation organization problem to solve")
            solution = dspy.OutputField(desc="Proposed solution to the problem")
            steps = dspy.OutputField(desc="Step-by-step implementation plan")
            patterns = dspy.OutputField(desc="Documentation patterns applied in the solution")
        
        # Load examples properly
        with open(dataset_path, 'r', encoding='utf-8') as f:
            examples = []
            for line in f:
                if line.startswith('//') or not line.strip():
                    continue
                data = json.loads(line)
                # Parse the output sections
                output_parts = data['output'].split('\\n\\n')
                solution = output_parts[0].replace('SOLUTION: ', '')
                steps_part = output_parts[1].replace('IMPLEMENTATION STEPS:\\n', '')
                steps = steps_part.split('\\n')
                steps = [s.strip('- ') for s in steps]
                patterns_part = output_parts[2].replace('PATTERNS:\\n', '') 
                patterns = patterns_part.split('\\n')
                patterns = [p.strip('- ') for p in patterns]
                
                # Create DSPy example
                example = dspy.Example(
                    problem=data['input'].replace('DOCUMENTATION PROBLEM: ', ''),
                    solution=solution,
                    steps=steps,
                    patterns=patterns
                ).with_inputs('problem')
                examples.append(example)
        
        # Split into training and validation sets
        trainset = examples[:4]
        valset = examples[4:]
        
        # Define a DSPy module for documentation organization
        class DocumentationOrganizer(dspy.Module):
            def __init__(self):
                super().__init__()
                self.solution_generator = dspy.ChainOfThought(DocumentationOrganization)
                
            def forward(self, problem):
                # Generate solution for the documentation problem
                return self.solution_generator(problem=problem)
        
        # Define metric function
        def pattern_quality(pred, gold):
            # Custom metric that evaluates pattern quality
            pred_patterns = set(p.lower() for p in pred.patterns)
            gold_patterns = set(p.lower() for p in gold.patterns)
            
            # Calculate pattern overlap (Jaccard similarity)
            intersection = len(pred_patterns.intersection(gold_patterns))
            union = len(pred_patterns.union(gold_patterns))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        # Optimize using bootstrap few-shot
        from dspy.teleprompt import BootstrapFewShot
        
        optimizer = BootstrapFewShot(metric=pattern_quality)
        optimized_module = optimizer.compile(
            DocumentationOrganizer(), 
            trainset=trainset, 
            valset=valset,
            max_bootstrapped_demos=3
        )
        
        # Save optimized module
        optimized_module.save('models/documentation_organizer.dspy')
        
        # Test the optimized module
        test_problem = "API documentation is inconsistent across different endpoints"
        result = optimized_module(problem=test_problem)
        
        print(f"Problem: {test_problem}")
        print(f"Solution: {result.solution}")
        print(f"Steps: {result.steps}")
        print(f"Patterns: {result.patterns}")
        """
        
        logger.info("DSPy usage demonstration complete")
    except Exception as e:
        logger.error(f"Error in DSPy usage demonstration: {e}", exc_info=True)

def main():
    """Main function to process documentation organization dataset."""
    try:
        # Load the dataset
        examples = load_dataset()
        
        # Create formatted training examples
        formatted_examples = create_training_examples(examples)
        
        # Save formatted examples
        save_formatted_examples(formatted_examples, "documentation_organization_formatted.jsonl")
        
        # Demonstrate DSPy usage
        demonstrate_dspy_usage()
        
        logger.info("Documentation pattern training preparation completed successfully")
    except Exception as e:
        logger.error(f"Error in documentation pattern training: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 