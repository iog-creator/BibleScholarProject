"""
HuggingFace Integration for DSPy Training in BibleScholarProject

This module configures DSPy to use HuggingFace's Inference API as the teacher/optimizer
for training and optimizing smaller models for Bible research tasks.
"""
import os
import dspy
import json
from pathlib import Path
import logging
import requests
import datetime

# Configure logger
logger = logging.getLogger(__name__)

# Configure environment variables
# HUGGINGFACE_API_KEY should be set in your environment or .env file
if 'HUGGINGFACE_API_KEY' not in os.environ:
    logger.warning("HUGGINGFACE_API_KEY not found in environment variables.")
    logger.warning("Please set this variable for the teacher model.")
    
# Define available teacher models (HuggingFace models)
TEACHER_MODELS = {
    # High-quality teacher models
    'high': [
        'mistralai/Mixtral-8x7B-Instruct-v0.1',
        'meta-llama/Llama-2-70b-chat-hf',
        'NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO',
    ],
    # Balanced teacher models
    'balanced': [
        'meta-llama/Llama-2-13b-chat-hf',
        'microsoft/Phi-2',
        'google/gemma-7b',
    ],
    # Fast teacher models
    'fast': [
        'microsoft/phi-1_5',
        'HuggingFaceH4/zephyr-7b-beta',
        'stabilityai/stablelm-zephyr-3b',
    ],
    # Local models (LM Studio)
    'local': [
        'darkidol-llama-3.1-8b-instruct-1.2-uncensored',
        'gguf-flan-t5-small',
    ]
}

# Define target models to train (local models)
TARGET_MODELS = [
    'google/flan-t5-small',
    'google/flan-t5-base',
    'google/flan-t5-large',
]

def configure_huggingface_model(api_key=None, model_name=None):
    """
    Configure DSPy to use HuggingFace's Inference API.
    This is an alias of configure_teacher_model for backward compatibility.
    
    Args:
        api_key (str, optional): HuggingFace API key. Defaults to None.
        model_name (str, optional): HuggingFace model name. Defaults to None.
    
    Returns:
        The configured LM client
    """
    return configure_teacher_model(api_key, model_name)

def configure_teacher_model(api_key=None, model_name=None):
    """
    Configure DSPy to use HuggingFace's Inference API as the teacher model.
    
    Args:
        api_key (str, optional): HuggingFace API key. Defaults to None.
        model_name (str, optional): HuggingFace model name. Defaults to None.
        
    Returns:
        The configured LM client
    """
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('HUGGINGFACE_API_KEY')
    
    if not api_key:
        raise ValueError("HuggingFace API key is required.")
    
    # Use provided model or get from environment or use default
    model_name = model_name or os.environ.get('HUGGINGFACE_MODEL') or 'mistralai/Mixtral-8x7B-Instruct-v0.1'
    
    logger.info(f"Configuring HuggingFace model: {model_name}")
    
    # For mock testing when no real models are available
    if model_name == "mock":
        logger.info("Using mock teacher model for testing")
        # Create a simple mock LM
        class MockTeacherLM(dspy.LM):
            def __init__(self):
                pass
                
            def __call__(self, prompt, **kwargs):
                if "bible" in prompt.lower() or "genesis" in prompt.lower():
                    return "This is a response about the Bible."
                elif "jesus" in prompt.lower() or "christ" in prompt.lower():
                    return "Jesus Christ is the central figure of Christianity."
                else:
                    return "This is a mock teacher model response."
        
        lm = MockTeacherLM()
        dspy.configure(lm=lm)
        return lm
    
    # Check if the model is a local LM Studio model
    local_models = [model for model in TEACHER_MODELS.get('local', [])]
    lm_studio_api = os.environ.get('LM_STUDIO_API_URL')
    
    if model_name in local_models and lm_studio_api:
        logger.info(f"Using local LM Studio model: {model_name}")
        # Configure OpenAI-compatible API for LM Studio
        lm = dspy.OpenAI(
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",  # LM Studio doesn't need a real key
        )
    # For testing - if using dummy key, use a simple dummy LM
    elif api_key.startswith('dummy_') or 'test' in api_key.lower():
        logger.info("Using dummy LM for testing (dummy API key detected)")
        
        # Create a simple LM that returns fixed outputs for testing
        class DummyLM(dspy.LM):
            def __init__(self, model_name):
                self.model_name = model_name
                
            def __call__(self, prompt, **kwargs):
                # Simply return a fixed response for testing
                if "genesis" in prompt.lower() or "creation" in prompt.lower() or "beginning" in prompt.lower():
                    return "God created the heavens and the earth, as described in Genesis 1:1."
                elif "jesus" in prompt.lower() or "christ" in prompt.lower():
                    return "Jesus Christ is the central figure of Christianity, the Son of God."
                else:
                    return "This is a dummy response for testing purposes."
        
        lm = DummyLM(model_name=model_name)
    else:
        # Configure DSPy to use HuggingFace's Inference API
        lm = dspy.HFClientTGI(
            model=model_name,
            api_key=api_key,
            port=8080  # Default port for TGI
        )
    
    dspy.configure(lm=lm)
    return lm

def configure_local_student_model(model_name=None):
    """
    Configure DSPy to use a local model as the student model.
    
    Args:
        model_name (str, optional): Model name. Defaults to None.
        
    Returns:
        The configured local LM
    """
    # Use provided model or get from environment or use default
    model_name = model_name or os.environ.get('STUDENT_MODEL') or 'google/flan-t5-small'
    
    logger.info(f"Configuring local student model: {model_name}")
    
    # For LM Studio local models
    lm_studio_api = os.environ.get('LM_STUDIO_API_URL')
    if lm_studio_api and model_name in ['gguf-flan-t5-small']:
        logger.info(f"Using LM Studio for student model: {model_name}")
        return dspy.OpenAI(
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",  # LM Studio doesn't need a real key
        )
    
    # For mock/testing purposes
    if model_name == 'mock':
        logger.info("Using mock student model for testing")
        # Create a simple mock LM
        class MockStudentLM(dspy.LM):
            def __init__(self):
                pass
                
            def __call__(self, prompt, **kwargs):
                return "This is a mock student model response."
        
        return MockStudentLM()
    
    # Default to using transformers locally
    logger.info(f"Using local Hugging Face student model: {model_name}")
    try:
        # This is for compatibility with DSPy 2.5.7
        student_lm = dspy.LocalLM(model_name=model_name)
        return student_lm
    except Exception as e:
        logger.error(f"Error loading local student model: {e}")
        # Fallback to mock for testing
        return configure_local_student_model("mock")

def configure_embeddings_model(model_name=None):
    """
    Configure an embeddings model.
    
    Args:
        model_name (str, optional): Model name. Defaults to None.
        
    Returns:
        A function that generates embeddings
    """
    model_name = model_name or os.environ.get('LM_STUDIO_EMBEDDING_MODEL') or 'text-embedding-nomic-embed-text-v1.5@q8_0'
    lm_studio_api = os.environ.get('LM_STUDIO_API_URL')
    
    logger.info(f"Configuring embeddings model: {model_name}")
    
    if lm_studio_api:
        # Use LM Studio for embeddings
        def get_embeddings(text):
            url = f"{lm_studio_api}/embeddings"
            headers = {"Content-Type": "application/json"}
            data = {
                "model": model_name,
                "input": text
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result['data'][0]['embedding']
            except Exception as e:
                logger.error(f"Error getting embeddings: {e}")
                # Return a dummy embedding
                return [0.0] * 768
        
        return get_embeddings
    else:
        # Mock embeddings function for testing
        def mock_embeddings(text):
            return [0.0] * 768
            
        return mock_embeddings

# Define BibleQA signature and module
class BibleQASignature(dspy.Signature):
    """Signature for Bible Question Answering tasks."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    answer = dspy.OutputField(desc="Answer to the question based on the biblical context")

class BibleQAModule(dspy.Module):
    """Module for Bible Question Answering tasks."""
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.Predict(BibleQASignature)
        
    def forward(self, context, question):
        """Forward pass for the module."""
        return self.qa_model(context=context, question=question)

def load_training_data(data_path=None):
    """
    Load training data from a JSONL file.
    
    Args:
        data_path (str, optional): Path to the training data file. Defaults to None.
        
    Returns:
        list: List of training examples.
    """
    # Use provided path or get from environment or use default
    data_path = data_path or os.environ.get('DSPY_TRAINING_DATA') or 'data/processed/dspy_training_data/qa_dataset.jsonl'
    
    # Create PathLib object
    data_path = Path(data_path)
    
    if not data_path.exists():
        logger.warning(f"Training data file not found: {data_path}")
        # Create simple examples for testing
        examples = [
            dspy.Example(
                context="In the beginning God created the heavens and the earth.",
                question="Who created the heavens and the earth?",
                answer="God"
            ),
            dspy.Example(
                context="Jesus said to them, 'I am the way, and the truth, and the life. No one comes to the Father except through me.'",
                question="What did Jesus say about himself?",
                answer="Jesus said he is the way, the truth, and the life."
            ),
            dspy.Example(
                context="For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.",
                question="What is required for eternal life according to this verse?",
                answer="Believing in God's Son"
            )
        ]
        logger.info(f"Created {len(examples)} example records for testing")
        return examples
    
    logger.info(f"Loading training data from: {data_path}")
    
    # Load training data
    examples = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments
            
            try:
                example = json.loads(line)
                # Ensure all required fields are present
                if all(k in example for k in ['context', 'question', 'answer']):
                    examples.append(dspy.Example(
                        context=example['context'],
                        question=example['question'],
                        answer=example['answer']
                    ))
                else:
                    logger.warning(f"Line {i+1} is missing required fields. Skipping.")
            except json.JSONDecodeError:
                logger.warning(f"Line {i+1} is not valid JSON. Skipping.")
            except Exception as e:
                logger.warning(f"Error processing line {i+1}: {e}. Skipping.")
    
    if not examples:
        logger.warning("No valid examples found in the data file. Creating test examples.")
        # Create a few simple examples for testing
        examples = [
            dspy.Example(
                context="In the beginning God created the heavens and the earth.",
                question="Who created the heavens and the earth?",
                answer="God"
            ),
            dspy.Example(
                context="Jesus said to them, 'I am the way, and the truth, and the life. No one comes to the Father except through me.'",
                question="What did Jesus say about himself?",
                answer="Jesus said he is the way, the truth, and the life."
            )
        ]
    
    logger.info(f"Loaded {len(examples)} training examples.")
    return examples

def train_and_compile_model(teacher_lm, local_model, examples, num_traces=10):
    """
    Train and compile a DSPy model.
    
    Args:
        teacher_lm: The teacher LM configured with configure_teacher_model
        local_model: The local model configured with configure_local_student_model
        examples: List of training examples
        num_traces (int, optional): Number of traces to compile. Defaults to 10.
        
    Returns:
        compiled_model: The compiled DSPy module
    """
    # Create a Bible QA module
    module = BibleQAModule()
    
    # Make sure we have enough examples
    if len(examples) < num_traces + 5:
        logger.warning(f"Not enough examples for requested traces. Using available {len(examples)} examples.")
        # Adjust num_traces to what we have available
        if len(examples) <= 3:
            num_traces = 1
            valset = examples[0:1]  # Just use the first example for validation too
        else:
            num_traces = max(1, len(examples) - 2)
            valset = examples[num_traces:] 
    else:
        valset = examples[num_traces:num_traces+5]
        
    logger.info(f"Using {num_traces} examples for training and {len(valset)} for validation")
    
    try:
        # Define a simple custom metric in case the default one fails
        def simple_metric(example, pred):
            """Very simple exact match metric that's more robust to errors"""
            try:
                if hasattr(pred, 'answer') and hasattr(example, 'answer'):
                    # Simple string match
                    pred_ans = str(pred.answer).lower().strip()
                    true_ans = str(example.answer).lower().strip()
                    return 1.0 if pred_ans == true_ans else 0.0
                return 0.0
            except:
                return 0.0
        
        # Try to use the standard metric, or fall back to our simple one
        try:
            metric = dspy.evaluate.answer_exact_match
            logger.info("Using standard DSPy exact match metric")
        except Exception:
            logger.warning("Standard metric not available, using simple fallback metric")
            metric = simple_metric
        
        # We'll use DSPy 2.5.7 optimizers 
        try:
            # Different versions of DSPy have different APIs for compilation
            # Try to detect the right parameters to use
            optimizer = dspy.BootstrapFewShot(metric=metric)
            logger.info("Using BootstrapFewShot optimizer for compilation")
            
            # Set the LM to use for compilation
            with dspy.context(lm=teacher_lm):
                try:
                    # Try the new API first
                    logger.info("Trying compile with trainset/valset")
                    compiled_module = optimizer.compile(
                        module,
                        trainset=examples[:num_traces],
                        valset=valset
                    )
                except TypeError:
                    # If that fails, try the old API
                    logger.info("Trying compile with train/test")
                    compiled_module = optimizer.compile(
                        module,
                        train=examples[:num_traces],
                        test=valset
                    )
                except TypeError:
                    # If that fails too, try with just the dataset
                    logger.info("Trying compile with just dataset")
                    compiled_module = optimizer.compile(
                        module,
                        dataset=examples
                    )
                    
            return compiled_module
            
        except (AttributeError, ImportError, TypeError) as e:
            # If BootstrapFewShot is not available or has API issues
            logger.warning(f"BootstrapFewShot failed: {e}, returning unmodified module")
            return module
            
    except Exception as e:
        logger.error(f"Error in training/compilation: {e}")
        # If compilation fails, return the uncompiled module as fallback
        logger.warning("Returning uncompiled module as fallback")
        return module

def save_models(compiled_model, save_path=None):
    """
    Save the compiled model.
    
    Args:
        compiled_model: The compiled DSPy module
        save_path (str, optional): Path to save the model. Defaults to None.
    """
    # Use provided path or get from environment or use default
    save_path = save_path or os.environ.get('DSPY_MODEL_PATH') or 'models/dspy'
    
    # Create PathLib object
    save_path = Path(save_path)
    
    # Create directory if it doesn't exist
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving compiled model to: {save_path}")
    
    try:
        # Save the model
        compiled_model.save(save_path)
        logger.info(f"Successfully saved model to {save_path}")
    except (PermissionError, OSError) as e:
        logger.error(f"Permission error saving model: {e}")
        # Create model info file instead as a fallback
        model_info_path = save_path.parent / 'model_info.json'
        try:
            model_info = {
                "name": "bible_qa_model",
                "type": "bible_qa",
                "model_status": "mock",
                "error": str(e),
                "created_at": str(datetime.datetime.now())
            }
            
            with open(model_info_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            logger.info(f"Created model info file at {model_info_path}")
        except Exception as e2:
            logger.error(f"Error creating model info file: {e2}")
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        # Just log the error but don't fail completely

def main():
    """
    Main function for training and testing BibleQA models.
    """
    # Configure teacher model
    teacher_lm = configure_teacher_model()
    
    # Configure student model
    student_model = configure_local_student_model()
    
    # Load training data
    examples = load_training_data()
    
    # Train and compile model
    compiled_model = train_and_compile_model(teacher_lm, student_model, examples)
    
    # Save the models
    save_models(compiled_model)
    
    # Example inference
    example = examples[0]
    result = compiled_model(context=example.context, question=example.question)
    
    print(f"Example Question: {example.question}")
    print(f"Model Answer: {result.answer}")
    print(f"Ground Truth: {example.answer}")
    
if __name__ == "__main__":
    main() 