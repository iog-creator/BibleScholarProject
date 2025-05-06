#!/usr/bin/env python
"""
Simple script to train a DSPy model and save it to disk for testing the API.
"""
import os
import json
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    print("Loaded environment variables from .env.dspy")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import DSPy modules
from src.dspy_programs.huggingface_integration import (
    configure_teacher_model,
    configure_local_student_model,
    load_training_data,
    train_and_compile_model,
    save_models,
    BibleQAModule
)

def main():
    """Train a simple DSPy model and save it to disk."""
    try:
        # For testing we'll use either LM Studio local models or mock models
        use_local_models = os.environ.get('LM_STUDIO_API_URL') is not None
        
        # Configure teacher model
        logger.info("Configuring teacher model...")
        if use_local_models:
            # Use local LM Studio model
            teacher_model = os.environ.get('LM_STUDIO_CHAT_MODEL', 'darkidol-llama-3.1-8b-instruct-1.2-uncensored')
            # For LM Studio we need the LM_STUDIO_API_URL in env but don't need a real API key
            teacher_lm = configure_teacher_model(api_key="dummy_test_key", model_name=teacher_model)
        else:
            # Use dummy teacher model
            teacher_lm = configure_teacher_model(api_key="dummy_test_key", model_name="mock")
        
        # Configure student model
        logger.info("Configuring student model...")
        if use_local_models:
            # Use local LM Studio model for student
            student_model = configure_local_student_model(model_name=os.environ.get('LM_STUDIO_COMPLETION_MODEL', 'gguf-flan-t5-small'))
        else:
            # Use mock student model
            student_model = configure_local_student_model(model_name="mock")
        
        # Load training data
        logger.info("Loading training data...")
        examples = load_training_data()
        
        # Limit to just 5 examples for quick testing
        examples = examples[:5]
        logger.info(f"Using {len(examples)} examples for training")
        
        # Train and compile model
        logger.info("Training and compiling model...")
        compiled_model = train_and_compile_model(
            teacher_lm=teacher_lm,
            local_model=student_model,
            examples=examples,
            num_traces=3  # Just 3 traces for quick testing
        )
        
        # Save the model - use a timestamp to avoid permission issues with existing files
        logger.info("Saving model...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        models_dir = Path('models/dspy')
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = models_dir / f'bible_qa_{timestamp}'
        
        # Save to a timestamped location 
        save_models(compiled_model, save_path=model_path)
        
        # Create model info file for the API to read
        model_info = {
            "name": "bible_qa_model",
            "type": "bible_qa",
            "student_model": "LM Studio model" if use_local_models else "mock",
            "teacher_model": teacher_model if use_local_models else "mock",
            "training_examples": len(examples),
            "created_at": timestamp,
            "model_path": str(model_path)
        }
        
        with open(models_dir / 'model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        
        # Create a symlink to the latest model (for standard location)
        latest_path = models_dir / 'bible_qa_compiled'
        try:
            # Instead of creating a symlink or writing directly to the file that has permission issues,
            # update the model_info.json file with the reference information
            model_info["latest_model_path"] = str(model_path)
            
            # Write updated model_info back to the file
            with open(models_dir / 'model_info.json', 'w') as f:
                json.dump(model_info, f, indent=2)
            
            logger.info(f"Updated model_info.json with latest model reference")
        except Exception as e:
            logger.error(f"Could not update model reference: {e}")
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Model info saved to {models_dir / 'model_info.json'}")
        return True
    
    except Exception as e:
        logger.error(f"Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("Successfully trained and saved model")
    else:
        print("Failed to train model") 