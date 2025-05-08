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

# Import Anthropic client for Claude integration
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic package not installed. Claude API integration will not be available.")
    logging.warning("Install with: pip install anthropic")

# Configure logger
logger = logging.getLogger(__name__)

# Configure environment variables
# HUGGINGFACE_API_KEY should be set in your environment or .env file
if 'HUGGINGFACE_API_KEY' not in os.environ:
    logger.warning("HUGGINGFACE_API_KEY not found in environment variables.")
    logger.warning("Please set this variable for the teacher model.")
    
# Define available teacher models (HuggingFace models)
TEACHER_MODELS = {
    # Highest-quality teacher models (least biased)
    'highest': [
        'meta-llama/Llama-3-70b-instruct',
        'anthropic/claude-3-opus-20240229',
        'anthropic/claude-3-sonnet-20240229',
        'meta-llama/Meta-Llama-3-70B',
    ],
    # High-quality teacher models
    'high': [
        'meta-llama/Llama-3-8b-instruct',
        'meta-llama/Llama-2-70b-chat-hf',
        'mistralai/Mixtral-8x7B-Instruct-v0.1',
        'NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO',
        'meta-llama/Meta-Llama-3-8B',
    ],
    # Balanced teacher models
    'balanced': [
        'meta-llama/Llama-2-13b-chat-hf',
        'microsoft/Phi-2',
        'google/gemma-7b',
        'mistralai/Mistral-7B-Instruct-v0.2',
    ],
    # Fast teacher models
    'fast': [
        'microsoft/phi-1_5',
        'HuggingFaceH4/zephyr-7b-beta',
        'stabilityai/stablelm-zephyr-3b',
        'meta-llama/Meta-Llama-3-1B',
    ],
    # Local models (LM Studio)
    'local': [
        'llama-3-8b-instruct',
        'llama-3-70b-instruct',
        'darkidol-llama-3.1-8b-instruct-1.2-uncensored',
        'gguf-flan-t5-small',
        'claude-3-opus',
    ],
    # Claude models (Anthropic)
    'claude': [
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-2.1',
        'claude-2.0'
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
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('HUGGINGFACE_API_KEY')
    
    if not api_key:
        raise ValueError("HuggingFace API key is required. Set HUGGINGFACE_API_KEY environment variable.")
    
    # Use provided model or get from environment or use default
    model_name = model_name or os.environ.get('HUGGINGFACE_MODEL') or 'meta-llama/Llama-3-70b-instruct'
    
    logger.info(f"Configuring HuggingFace model: {model_name}")
    
    # For mock testing when no real models are available
    if model_name == "mock" or api_key.startswith('dummy_') or 'test' in api_key.lower():
        logger.info("Using mock HuggingFace model for testing")
        
        # Create a mock LM
        class MockHFLM(dspy.LM):
            def __init__(self, model_name="hf-mock"):
                self.model = model_name
                
            def __call__(self, prompt, **kwargs):
                # Return a realistic response for testing
                if "bible" in prompt.lower() or "genesis" in prompt.lower():
                    return "According to the Bible, in Genesis 1:1, it states 'In the beginning God created the heavens and the earth.' This is the foundational verse establishing God as the creator of all things."
                elif "jesus" in prompt.lower() or "christ" in prompt.lower():
                    return "Jesus Christ, also known as Jesus of Nazareth, is the central figure of Christianity. Christians believe he is the Son of God and the awaited Messiah prophesied in the Old Testament."
                else:
                    return "This is a mock response for testing the HuggingFace API integration."
        
        lm = MockHFLM(model_name)
        dspy.configure(lm=lm)
        return lm
    
    try:
        # Standard DSPy approach for HuggingFace integration
        # Using the approach documented in DSPy documentation
        try:
            # First try the direct HuggingFace LM from DSPy
            lm = dspy.LM(
                model=f"huggingface/{model_name}",
                api_key=api_key,
                temperature=0.3,
                max_tokens=1024
            )
        except (AttributeError, ImportError, TypeError):
            # Fallback to older DSPy versions with different interfaces
            logger.warning("Using alternative HuggingFace integration method")
            try:
                # Try HuggingFaceLM if available
                lm = dspy.HuggingFaceLM(
                    model=model_name,
                    api_key=api_key,
                    temperature=0.3,
                    max_tokens=1024
                )
            except (AttributeError, ImportError):
                # Try HFClientTGI as a fallback
                logger.warning("Using HFClientTGI as fallback")
                lm = dspy.HFClientTGI(
                    model=model_name,
                    api_key=api_key
                )
        
        dspy.configure(lm=lm)
        logger.info(f"Successfully configured HuggingFace model: {model_name}")
        return lm
    except Exception as e:
        logger.error(f"Failed to configure HuggingFace model: {e}")
        raise

def configure_claude_model(api_key=None, model_name=None):
    """
    Configure DSPy to use Anthropic's Claude API as the teacher model.
    
    Args:
        api_key (str, optional): Anthropic API key. Defaults to None.
        model_name (str, optional): Claude model name. Defaults to None.
        
    Returns:
        The configured LM client
    """
    if not ANTHROPIC_AVAILABLE:
        logger.error("Anthropic package not installed. Cannot configure Claude model.")
        logger.error("Install with: pip install anthropic")
        raise ImportError("Anthropic package not installed")
        
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
    
    # Use provided model or get from environment or use default
    model_name = model_name or os.environ.get('CLAUDE_MODEL') or 'claude-3-opus-20240229'
    
    logger.info(f"Configuring Claude model: {model_name}")
    
    # Verify valid Claude model name
    claude_models = TEACHER_MODELS.get('claude', [])
    if model_name not in claude_models and not model_name.startswith('claude-'):
        logger.warning(f"Unrecognized Claude model: {model_name}")
        logger.warning(f"Available Claude models: {', '.join(claude_models)}")
        logger.warning("Using model anyway, assuming it's a valid Anthropic model")
    
    # For mock testing when no real models are available
    if model_name == "mock" or api_key.startswith('dummy_') or 'test' in api_key.lower():
        logger.info("Using mock Claude model for testing")
        
        # Create a mock LM for Claude
        class MockClaudeLM(dspy.LM):
            def __init__(self, model_name="claude-3-mock"):
                self.model = model_name
                
            def __call__(self, prompt, **kwargs):
                # Return a realistic Claude-like response for testing
                if "bible" in prompt.lower() or "genesis" in prompt.lower():
                    return "According to the Bible, in Genesis 1:1, it states 'In the beginning God created the heavens and the earth.' This is the foundational verse establishing God as the creator of all things."
                elif "jesus" in prompt.lower() or "christ" in prompt.lower():
                    return "Jesus Christ, also known as Jesus of Nazareth, is the central figure of Christianity. Christians believe he is the Son of God and the awaited Messiah prophesied in the Old Testament."
                else:
                    return "I'm Claude, an AI assistant by Anthropic. I'm designed to be helpful, harmless, and honest. This is a mock response for testing the Claude API integration."
        
        lm = MockClaudeLM(model_name)
        dspy.configure(lm=lm)
        return lm
    
    try:
        # Create the Claude DSPy LM
        try:
            # Try to use ClaudeLM class if available in newer DSPy
            lm = dspy.ClaudeLM(
                model=model_name,
                api_key=api_key,
                temperature=0.3,
                max_tokens=1024
            )
        except (AttributeError, ImportError):
            # Fallback for older DSPy versions - create a custom Claude LM wrapper
            logger.warning("ClaudeLM not available in DSPy, using custom Claude integration")
            
            class CustomClaudeLM(dspy.LM):
                def __init__(self, model_name, api_key):
                    self.model = model_name
                    self.client = anthropic.Anthropic(api_key=api_key)
                    self.max_tokens = 1024
                    self.temperature = 0.3
                    self.stop_sequences = None
                    self.top_p = 1.0
                    
                    # Add attributes to make DSPy happy
                    self.kwargs = {
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "top_p": self.top_p,
                        "stop_sequences": self.stop_sequences,
                    }
                    # Standard name that DSPy expects
                    self.provider = f"anthropic-{model_name}"
                
                def __call__(self, prompt=None, **kwargs):
                    """
                    Process a prompt and return a response compatible with DSPy.
                    
                    Args:
                        prompt: The text prompt to send to Claude
                        **kwargs: Additional parameters for the API call
                        
                    Returns:
                        A string response that DSPy can handle
                    """
                    try:
                        # Handle different ways DSPy might send the prompt
                        if isinstance(prompt, dict) and "text" in prompt:
                            prompt = prompt["text"]
                        elif isinstance(prompt, (list, tuple)) and prompt:
                            # If it's a list or tuple, join the elements
                            prompt = " ".join(str(p) for p in prompt)
                            
                        # Ensure we have a valid prompt
                        if not prompt or not isinstance(prompt, str):
                            raise ValueError(f"Invalid prompt: {prompt}")
                            
                        # Set parameters from kwargs
                        max_tokens = kwargs.get('max_tokens', self.max_tokens)
                        temperature = kwargs.get('temperature', self.temperature)
                        top_p = kwargs.get('top_p', self.top_p)
                        stop_sequences = kwargs.get('stop_sequences', self.stop_sequences)
                        
                        # Build the API parameters
                        params = {
                            "model": self.model,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "messages": [{"role": "user", "content": prompt}]
                        }
                        
                        # Add optional parameters only if they're set
                        if top_p != 1.0:
                            params["top_p"] = top_p
                        if stop_sequences:
                            params["stop_sequences"] = stop_sequences
                        
                        # Make API call to Claude
                        response = self.client.messages.create(**params)
                        
                        # Return the response text directly - DSPy can handle a string response
                        return response.content[0].text
                    except Exception as e:
                        logger.error(f"Error calling Claude API: {e}")
                        # Return a simple error message - DSPy can handle this
                        return f"Error: {str(e)}"
                
                def generate(self, prompt, **kwargs):
                    """Alternative interface for DSPy compatibility"""
                    return self.__call__(prompt, **kwargs)
                
                # Add additional methods for DSPy compatibility
                def batch(self, prompts, **kwargs):
                    """
                    Process a batch of prompts and return a list of responses.
                    
                    Args:
                        prompts: List of prompts to process
                        **kwargs: Additional parameters for API calls
                        
                    Returns:
                        List of string responses
                    """
                    return [self.__call__(prompt, **kwargs) for prompt in prompts]
            
            lm = CustomClaudeLM(model_name=model_name, api_key=api_key)
        
        dspy.configure(lm=lm)
        logger.info(f"Successfully configured Claude model: {model_name}")
        return lm
    except Exception as e:
        logger.error(f"Failed to configure Claude model: {e}")
        raise

def configure_teacher_model(api_key=None, model_name=None):
    """
    Configure DSPy to use HuggingFace's Inference API as the teacher model.
    
    Args:
        api_key (str, optional): HuggingFace API key. Defaults to None.
        model_name (str, optional): HuggingFace model name. Defaults to None.
        
    Returns:
        The configured LM client
    """
    # Check if this is a Claude model request
    if model_name and (model_name.startswith('claude-') or model_name in TEACHER_MODELS.get('claude', [])):
        logger.info(f"Detected Claude model request: {model_name}")
        return configure_claude_model(api_key=os.environ.get('ANTHROPIC_API_KEY'), model_name=model_name)
    
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('HUGGINGFACE_API_KEY')
    
    if not api_key:
        raise ValueError("HuggingFace API key is required.")
    
    # Use provided model or get from environment or use default
    model_name = model_name or os.environ.get('HUGGINGFACE_MODEL') or 'meta-llama/Llama-3-70b-instruct'
    
    logger.info(f"Configuring model: {model_name}")
    
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
    
    # For HuggingFace API access to student model (rare case)
    hf_api_key = os.environ.get('HUGGINGFACE_API_KEY')
    if hf_api_key and 'STUDENT_HF_INFERENCE' in os.environ:
        logger.info(f"Using HuggingFace for student model: {model_name}")
        return dspy.HFClientTGI(
            model=model_name,
            api_key=hf_api_key
        )
    
    # Default - use local HuggingFace model
    try:
        # Must have transformers package installed
        import transformers
        logger.info(f"Loading local HuggingFace model: {model_name}")
        return dspy.HFModel(model_name)
    except ImportError:
        logger.error("Cannot load local model - transformers package not installed")
        raise ImportError("Please install transformers: pip install transformers")

def configure_embeddings_model(model_name=None):
    """
    Configure DSPy to use an embeddings model for retrieval.
    
    Args:
        model_name (str, optional): Embeddings model name. Defaults to None.
        
    Returns:
        A function to get embeddings
    """
    try:
        # Try to connect to a local embedding service (LM Studio)
        lm_studio_api = os.environ.get('LM_STUDIO_API_URL')
        embedding_model = os.environ.get('LM_STUDIO_EMBEDDING_MODEL')
        
        if lm_studio_api and embedding_model:
            logger.info(f"Using LM Studio for embeddings: {embedding_model}")
            
            def get_embeddings(text):
                """Get embeddings from LM Studio API."""
                response = requests.post(
                    f"{lm_studio_api}/embeddings",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": embedding_model,
                        "input": text
                    }
                )
                if response.status_code == 200:
                    return response.json()["data"][0]["embedding"]
                else:
                    logger.error(f"Error getting embeddings: {response.text}")
                    return None
                    
            return get_embeddings
        else:
            # Fall back to a mock embeddings function for testing
            logger.warning("No embeddings model configured, using mock embeddings")
            
            def mock_embeddings(text):
                """Mock embeddings function for testing."""
                import hashlib
                import numpy as np
                # Generate a deterministic embedding based on text hash
                hash_obj = hashlib.md5(text.encode())
                seed = int(hash_obj.hexdigest(), 16) % (2**32)
                np.random.seed(seed)
                return np.random.rand(384).tolist()  # 384 dimensions
                
            return mock_embeddings
    except Exception as e:
        logger.error(f"Error configuring embeddings model: {e}")
        raise

class BibleQASignature(dspy.Signature):
    """Signature for Bible Question Answering tasks."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    answer = dspy.OutputField(desc="Answer to the question based on the biblical context")

class BibleQAModule(dspy.Module):
    """Module for Bible Question Answering tasks."""
    
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(BibleQASignature)
    
    def forward(self, context, question):
        """Answer a Bible question using a chain-of-thought approach."""
        return self.prog(context=context, question=question)

def load_training_data(data_path=None):
    """
    Load the Bible QA training data from disk.
    
    Args:
        data_path (str, optional): Path to the training data. Defaults to None.
        
    Returns:
        List of DSPy Example objects
    """
    # Define the default path
    default_path = 'data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json'
    data_path = data_path or os.getenv('DSPY_TRAINING_DATA', default_path)
    
    logger.info(f"Loading training data from {data_path}")
    
    try:
        # Make the data directory if needed
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Check if the file exists
        if not os.path.exists(data_path):
            logger.error(f"Training data file not found: {data_path}")
            
            # Create a simple mock dataset for testing
            mock_examples = [
                {
                    "context": "In the beginning God created the heavens and the earth. Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters.",
                    "question": "Who created the heavens and the earth?",
                    "answer": "God created the heavens and the earth."
                },
                {
                    "context": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
                    "question": "What did God give because he loved the world?",
                    "answer": "God gave his one and only Son."
                },
                {
                    "context": "Jesus went throughout Galilee, teaching in their synagogues, proclaiming the good news of the kingdom, and healing every disease and sickness among the people.",
                    "question": "What did Jesus do in Galilee?",
                    "answer": "Jesus taught in synagogues, proclaimed the good news of the kingdom, and healed diseases and sicknesses."
                }
            ]
            
            # Save this basic dataset for future use
            with open(data_path, 'w') as f:
                json.dump(mock_examples, f, indent=2)
                
            logger.warning(f"Created a basic mock dataset with {len(mock_examples)} examples at {data_path}")
            examples_data = mock_examples
        else:
            # Load the dataset
            with open(data_path, 'r', encoding='utf-8') as f:
                examples_data = json.load(f)
                
        # Convert to DSPy examples
        examples = []
        for ex in examples_data:
            context = ex.get('context', '')
            question = ex.get('question', '')
            answer = ex.get('answer', '')
            
            # Skip examples with missing fields
            if not question or not answer:
                continue
                
            # Create DSPy Example object
            dspy_example = dspy.Example(
                context=context,
                question=question,
                answer=answer
            ).with_inputs('context', 'question')
            
            examples.append(dspy_example)
            
        logger.info(f"Loaded {len(examples)} training examples")
        return examples
    except Exception as e:
        logger.error(f"Error loading training data: {e}")
        
        # Return a minimal set of examples for testing
        logger.warning("Using minimal test dataset")
        return [
            dspy.Example(
                context="In the beginning God created the heavens and the earth.",
                question="Who created the heavens and the earth?",
                answer="God created the heavens and the earth."
            ).with_inputs('context', 'question')
        ]

def train_and_compile_model(teacher_lm, local_model, examples, num_traces=10):
    """
    Train and compile a DSPy model for Bible QA.
    
    Args:
        teacher_lm: The teacher language model for optimization
        local_model: The student model (local or HF) to optimize
        examples: List of training examples
        num_traces: Number of demos to generate per example
        
    Returns:
        The compiled/optimized model
    """
    # Ensure we have a config directory
    os.makedirs('models', exist_ok=True)
    os.makedirs('models/dspy', exist_ok=True)
    os.makedirs('models/dspy/bible_qa_t5', exist_ok=True)
    
    # Create a timestamp for the model
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = f'models/dspy/bible_qa_t5/bible_qa_t5_{timestamp}'
    os.makedirs(model_dir, exist_ok=True)
    
    # Create a basic model if none provided
    if not local_model:
        logger.warning("No local model provided, creating default BibleQAModule")
        model = BibleQAModule()
    else:
        model = BibleQAModule()
        
    logger.info(f"Created model: {type(model).__name__}")
    
    # Split examples into train/dev
    train_examples = examples[:int(0.9 * len(examples))]
    dev_examples = examples[int(0.9 * len(examples)):]
    
    if len(dev_examples) == 0 and len(train_examples) > 0:
        dev_examples = [train_examples[0]]
        
    logger.info(f"Train examples: {len(train_examples)}")
    logger.info(f"Dev examples: {len(dev_examples)}")
    
    # Define evaluation metric
    def simple_metric(example, pred):
        """Simple evaluation metric comparing answers directly."""
        # Convert both to lowercase and strip whitespace
        gold = example.answer.lower().strip()
        prediction = pred.answer.lower().strip()
        
        # Direct match
        if prediction == gold:
            return 1.0
            
        # Calculate rough token overlap (simplistic)
        gold_tokens = set(gold.split())
        pred_tokens = set(prediction.split())
        
        if not gold_tokens or not pred_tokens:
            return 0.0
            
        overlap = gold_tokens.intersection(pred_tokens)
        score = len(overlap) / max(len(gold_tokens), len(pred_tokens))
        
        return score
    
    try:
        # Configure optimizers
        if len(train_examples) <= 2:
            # For very small datasets, use basic few-shot
            logger.info("Using basic few-shot learning (small dataset)")
            teleprompter = dspy.teleprompt.BootstrapFewShot(k=min(3, len(train_examples)))
        else:
            # For larger datasets, use more sophisticated optimization
            logger.info("Using forward-chaining optimization")
            # Forward chaining works well for reasoning tasks
            teleprompter = dspy.teleprompt.ForwardChaining(
                max_bootstrapped_demos=3,
                max_labeled_demos=5,
                metric=simple_metric
            )
        
        # Compile the model with the teacher
        with dspy.configure(lm=teacher_lm):
            logger.info("Starting model compilation with teacher LM")
            compiled_model = teleprompter.compile(
                model,
                train_data=train_examples,
                eval_data=dev_examples,
                metric=simple_metric,
                num_threads=1,  # Adjust based on your system
                max_traces=num_traces
            )
        
        logger.info("Model compilation complete")
        
        # Save compilation metadata
        metadata = {
            "timestamp": timestamp,
            "model_type": "BibleQAModule",
            "num_train_examples": len(train_examples),
            "num_dev_examples": len(dev_examples),
            "num_traces": num_traces
        }
        
        with open(f"{model_dir}/model.info", "w") as f:
            json.dump(metadata, f, indent=2)
            
        with open(f"{model_dir}/model.json", "w") as f:
            json.dump({"model_type": "BibleQAModule"}, f)
            
        return compiled_model
    except Exception as e:
        logger.error(f"Error compiling model: {e}")
        # Return the uncompiled model in case of error
        return model

def save_models(compiled_model, save_path=None):
    """
    Save the compiled model to disk.
    
    Args:
        compiled_model: The compiled DSPy model
        save_path: Path to save the model (default: None, uses timestamp)
        
    Returns:
        Path where the model was saved
    """
    # Create a timestamp for the model if no path provided
    if not save_path:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = f'models/dspy/bible_qa_t5/bible_qa_t5_{timestamp}'
    
    # Ensure the directory exists
    os.makedirs(save_path, exist_ok=True)
    
    try:
        # Save the compiled model
        model_pkl_path = f"{save_path}/model.pkl"
        with open(model_pkl_path, 'wb') as f:
            import pickle
            pickle.dump(compiled_model, f)
        
        logger.info(f"Saved compiled model to {model_pkl_path}")
        
        # Try to save in MLflow if available
        try:
            import mlflow
            from mlflow.tracking import MlflowClient
            
            # Initialize MLflow
            mlflow.set_tracking_uri("file:./mlruns")
            mlflow.set_experiment("bible_qa_dspy")
            
            # Start a run
            with mlflow.start_run(run_name=f"bible_qa_{os.path.basename(save_path)}"):
                # Log parameters
                mlflow.log_param("model_type", "BibleQAModule")
                mlflow.log_param("timestamp", datetime.datetime.now().isoformat())
                
                # Log the model file
                mlflow.log_artifact(model_pkl_path)
                
                # Log config if exists
                model_info_path = f"{save_path}/model.info"
                if os.path.exists(model_info_path):
                    mlflow.log_artifact(model_info_path)
            
            logger.info("Logged model to MLflow")
        except Exception as e:
            logger.warning(f"Could not save to MLflow: {e}")
        
        # Create a symlink to latest
        latest_symlink = 'models/dspy/bible_qa_t5/bible_qa_t5_latest'
        
        # Check if on Windows (can't use symlinks easily)
        if os.name == 'nt':
            # On Windows, just copy the model files
            import shutil
            
            # Create the latest directory if it doesn't exist
            os.makedirs(latest_symlink, exist_ok=True)
            
            # Copy model files
            for file in os.listdir(save_path):
                source = os.path.join(save_path, file)
                destination = os.path.join(latest_symlink, file)
                shutil.copy2(source, destination)
                
            logger.info(f"Copied model files to {latest_symlink}")
        else:
            # On Unix, create a proper symlink
            if os.path.exists(latest_symlink) or os.path.islink(latest_symlink):
                os.remove(latest_symlink)
                
            os.symlink(os.path.abspath(save_path), latest_symlink, target_is_directory=True)
            logger.info(f"Created symlink from {latest_symlink} to {save_path}")
        
        return save_path
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return None

def main():
    """Main function for direct script execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train and compile a DSPy model for Bible QA')
    parser.add_argument('--teacher-model', type=str, default=None, help='HuggingFace teacher model')
    parser.add_argument('--student-model', type=str, default=None, help='Local student model to optimize')
    parser.add_argument('--num-traces', type=int, default=10, help='Number of demos to generate per example')
    parser.add_argument('--use-local-teacher', action='store_true', help='Use local LM Studio model as teacher')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/dspy_training.log'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting DSPy training for Bible QA")
    
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Configure teacher model
    if args.use_local_teacher:
        # Use LM Studio model
        teacher_model = configure_teacher_model(api_key="dummy_key", model_name=args.teacher_model or "mock")
    else:
        # Use HuggingFace model
        teacher_model = configure_teacher_model(model_name=args.teacher_model)
    
    # Configure student model
    student_model = configure_local_student_model(model_name=args.student_model)
    
    # Load training data
    examples = load_training_data()
    
    # Train and compile the model
    compiled_model = train_and_compile_model(
        teacher_model, 
        student_model, 
        examples,
        num_traces=args.num_traces
    )
    
    # Save the compiled model
    save_path = save_models(compiled_model)
    
    logger.info(f"Training complete. Model saved to {save_path}")
    
    return 0

if __name__ == "__main__":
    main() 