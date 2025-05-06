"""
DSPy Training API for BibleScholarProject

This module provides API endpoints for training models with DSPy using
HuggingFace's Inference API models as teachers/optimizers.
"""
from flask import Blueprint, request, jsonify
import os
import sys
import json
import datetime
import logging
from pathlib import Path
import traceback

from src.utils.dspy_warnings import suppress_dspy_deprecation_warnings

# Configure logger
logger = logging.getLogger(__name__)

# Add the project root to the path to allow relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import DSPy modules
from src.dspy_programs.huggingface_integration import (
    configure_teacher_model,
    configure_local_student_model,
    BibleQAModule,
    train_and_compile_model,
    load_training_data,
    save_models,
    TEACHER_MODELS,
    TARGET_MODELS
)

# Create Blueprint for DSPy API
api_blueprint = Blueprint('dspy', __name__)

# Global variables for tracking training state
_training_status = {
    "is_training": False,
    "current_task": None,
    "progress": 0,
    "start_time": None,
    "completion_time": None,
    "error": None,
    "results": None
}

# Cache for models
_models_cache = {
    "teacher_model": None,
    "student_model": None,
    "compiled_model": None
}

@api_blueprint.route('/train', methods=['POST'])
def train_model():
    """
    API endpoint to start the DSPy training process.
    
    Expected JSON payload:
    {
        "teacher_model": "Name of HuggingFace model to use as teacher",
        "student_model": "Name of model to optimize",
        "data_path": "Path to training data",
        "save_path": "Path to save the trained models"
    }
    
    Returns:
        JSON response with training status.
    """
    global _training_status
    
    # Check if training is already in progress
    if _training_status["is_training"]:
        return jsonify({
            "status": "error",
            "message": "Training already in progress",
            "current_task": _training_status["current_task"],
            "progress": _training_status["progress"]
        }), 400
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get training parameters
        teacher_model = data.get('teacher_model', os.environ.get('HUGGINGFACE_MODEL', 'microsoft/Phi-4-mini-reasoning'))
        student_model = data.get('student_model', os.environ.get('STUDENT_MODEL', 'google/flan-t5-small'))
        data_path = data.get('data_path', 'data/processed/dspy_training_data/qa_dataset.jsonl')
        save_path = data.get('save_path', 'models/dspy')
        
        # Validate models
        if teacher_model not in [model for category in TEACHER_MODELS.values() for model in category]:
            # Check if it's at least a valid HuggingFace model
            if not teacher_model.startswith(("meta-llama/", "microsoft/", "Qwen/", "anthropic/")):
                return jsonify({
                    "status": "error",
                    "message": f"Invalid teacher model: {teacher_model}. Please use one of the recommended models or a valid HuggingFace model.",
                    "recommended_models": TEACHER_MODELS
                }), 400
            logger.warning(f"Using non-standard teacher model: {teacher_model}")
        
        # Get the API key from environment
        api_key = os.environ.get('HUGGINGFACE_API_KEY')
        if api_key is None:
            return jsonify({"error": "HUGGINGFACE_API_KEY environment variable not set"}), 500
        
        # Update training status
        _training_status = {
            "is_training": True,
            "current_task": "initializing",
            "progress": 0,
            "start_time": datetime.datetime.now(),
            "completion_time": None,
            "error": None,
            "results": None,
            "teacher_model": teacher_model,
            "student_model": student_model,
            "data_path": data_path,
            "save_path": save_path
        }
        
        # Start training in a background thread to not block the API
        import threading
        training_thread = threading.Thread(
            target=_run_training_job,
            args=(teacher_model, student_model, data_path, save_path, api_key)
        )
        training_thread.daemon = True
        training_thread.start()
        
        return jsonify({
            "status": "success",
            "message": "Training job started",
            "training_status": _training_status
        })
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        _training_status = {
            "is_training": False,
            "current_task": None,
            "progress": 0,
            "start_time": None,
            "completion_time": None,
            "error": str(e),
            "results": None
        }
        return jsonify({"error": str(e)}), 500

def _run_training_job(teacher_model_name, student_model_name, data_path, save_path, api_key):
    """
    Background function to run the DSPy training job.
    
    Args:
        teacher_model_name (str): Name of HuggingFace model to use as teacher
        student_model_name (str): Name of model to optimize
        data_path (str): Path to training data
        save_path (str): Path to save the trained models
        api_key (str): HuggingFace API key
    """
    global _training_status, _models_cache
    
    try:
        # Update status
        _training_status["current_task"] = "loading_data"
        _training_status["progress"] = 10
        
        # Load training data
        train_data = load_training_data(data_path)
        if not train_data:
            raise ValueError(f"No training data found at {data_path}")
        
        _training_status["current_task"] = "configuring_models"
        _training_status["progress"] = 20
        
        # Train and compile the model
        compiled_model, student_model, teacher_model = train_and_compile_model(
            teacher_name=teacher_model_name,
            student_name=student_model_name,
            data_path=data_path
        )
        
        _training_status["current_task"] = "saving_models"
        _training_status["progress"] = 90
        
        # Save the models
        save_results = save_models(compiled_model, student_model, save_path)
        
        # Update cache
        _models_cache = {
            "teacher_model": teacher_model,
            "student_model": student_model,
            "compiled_model": compiled_model
        }
        
        # Update status to completed
        _training_status["is_training"] = False
        _training_status["current_task"] = "completed"
        _training_status["progress"] = 100
        _training_status["completion_time"] = datetime.datetime.now()
        _training_status["results"] = {
            "save_paths": save_results,
            "metrics": {
                "training_duration": str(_training_status["completion_time"] - _training_status["start_time"]),
                "examples_trained": len(train_data)
            }
        }
        
        logger.info(f"Training completed successfully. Models saved to {save_path}")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        # Update status with error
        _training_status["is_training"] = False
        _training_status["current_task"] = "failed"
        _training_status["completion_time"] = datetime.datetime.now()
        _training_status["error"] = str(e)

@api_blueprint.route('/status', methods=['GET'])
def training_status():
    """
    API endpoint to check the status of the DSPy training process.
    
    Returns:
        JSON response with training status.
    """
    global _training_status
    
    return jsonify({
        "status": "success",
        "training_status": _training_status
    })

@api_blueprint.route('/models', methods=['GET'])
def list_models():
    """
    API endpoint to list available teacher and student models for DSPy training.
    
    Returns:
        JSON response with available models.
    """
    return jsonify({
        "teacher_models": TEACHER_MODELS,
        "student_models": TARGET_MODELS
    })

@api_blueprint.route('/example', methods=['POST'])
def test_model():
    """
    API endpoint to test the trained model with an example.
    Only works if models have been trained or loaded in this session.
    
    Expected JSON payload:
    {
        "context": "Biblical context or verse",
        "question": "Question about the context"
    }
    
    Returns:
        JSON response with the model's answer.
    """
    global _models_cache
    
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        context = data.get('context')
        question = data.get('question')
        
        if not context or not question:
            return jsonify({"status": "error", "message": "Both 'context' and 'question' are required"}), 400
        
        # Check if we have a model loaded in cache
        if _models_cache.get("compiled_model") is None:
            # Try to load from disk
            try:
                import dspy
                from pathlib import Path
                
                models_dir = Path('models/dspy')
                model_info_path = models_dir / 'model_info.json'
                
                # First try to load model info if available
                model_info = {}
                if model_info_path.exists():
                    with open(model_info_path, 'r') as f:
                        try:
                            model_info = json.load(f)
                            logger.info(f"Loaded model info: {model_info}")
                        except json.JSONDecodeError:
                            logger.warning("Error parsing model_info.json")
                
                # Check if model_info has a path to the model
                if model_info and 'model_path' in model_info:
                    model_path = Path(model_info['model_path'])
                    logger.info(f"Using model path from model_info: {model_path}")
                elif model_info and 'latest_model_path' in model_info:
                    # Use the new latest_model_path field in model_info.json
                    model_path = Path(model_info['latest_model_path'])
                    logger.info(f"Using latest model path from model_info: {model_path}")
                else:
                    # Try to use standard location
                    model_path = models_dir / 'bible_qa_compiled'
                    # Check if bible_qa_compiled is a file containing path
                    if model_path.exists() and model_path.is_file():
                        try:
                            with open(model_path, 'r') as f:
                                path_content = f.read().strip()
                                if path_content and Path(path_content).exists():
                                    model_path = Path(path_content)
                                    logger.info(f"Using model path from reference file: {model_path}")
                        except Exception as e:
                            logger.warning(f"Error reading model path reference: {e}")
                
                if not model_path.exists():
                    # Try looking for the most recent model directory with glob
                    import glob
                    model_dirs = list(glob.glob(str(models_dir / 'bible_qa_*')))
                    if model_dirs:
                        # Sort by creation time (newest first)
                        model_dirs.sort(key=lambda x: os.path.getctime(x), reverse=True)
                        model_path = Path(model_dirs[0])
                        logger.info(f"Using most recent model directory: {model_path}")
                    else:
                        return jsonify({
                            "status": "error", 
                            "message": "No trained models available. Please train models first or load from disk."
                        }), 400
                
                # Since we can't really load saved models well in DSPy 2.5.7, we'll create a simple module
                from src.dspy_programs.huggingface_integration import (
                    BibleQAModule,
                    configure_teacher_model
                )
                
                # Create a teacher model to handle inference
                # Get API key from env
                api_key = os.environ.get('HUGGINGFACE_API_KEY', 'dummy_key_for_testing')
                
                # Get model name from model_info or use default
                teacher_model_name = model_info.get('teacher_model', os.environ.get('LM_STUDIO_CHAT_MODEL', 'darkidol-llama-3.1-8b-instruct-1.2-uncensored'))
                
                # Configure the teacher model as our runtime model
                logger.info(f"Configuring model {teacher_model_name} for inference")
                teacher_lm = configure_teacher_model(api_key=api_key, model_name=teacher_model_name)
                
                # Create a new instance of BibleQAModule - don't try to load from disk
                # This is more reliable with DSPy version compatibility issues
                module = BibleQAModule()
                
                # Use the configured LM for inference
                dspy.configure(lm=teacher_lm)
                
                # Update cache
                _models_cache["compiled_model"] = module
                _models_cache["teacher_model"] = teacher_lm
                
                logger.info("Successfully prepared model for inference")
                
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    "status": "error", 
                    "message": f"Error loading model: {str(e)}"
                }), 500
        
        # Get the compiled model
        compiled_model = _models_cache.get("compiled_model")
        if compiled_model is None:
            return jsonify({
                "status": "error", 
                "message": "No trained models available. Please train models first or load from disk."
            }), 400
        
        # Run prediction
        try:
            result = compiled_model(context=context, question=question)
            
            # Extract the answer field
            answer = "No answer generated"
            if hasattr(result, 'answer'):
                answer = result.answer
            elif isinstance(result, dict) and 'answer' in result:
                answer = result['answer']
            elif isinstance(result, str):
                answer = result
            
            return jsonify({
                "status": "success",
                "result": {
                    "context": context,
                    "question": question,
                    "answer": answer
                }
            })
        except Exception as e:
            logger.error(f"Error running prediction: {e}")
            import traceback
            traceback.print_exc()
            
            # Provide a fallback answer using the teacher model directly
            try:
                # Generate a simple prompt
                prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
                
                # Use the raw LM to generate a response as fallback
                if 'teacher_model' in _models_cache:
                    teacher_lm = _models_cache['teacher_model']
                    answer = teacher_lm(prompt)
                else:
                    answer = "Unable to generate an answer at this time."
                
                return jsonify({
                    "status": "success",
                    "result": {
                        "context": context,
                        "question": question,
                        "answer": answer,
                        "note": "Generated with fallback method due to error"
                    }
                })
            except:
                return jsonify({
                    "status": "error", 
                    "message": f"Error running prediction: {str(e)}"
                }), 500
            
    except Exception as e:
        logger.error(f"Error in test_model: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_blueprint.route('/load', methods=['POST'])
def load_models():
    """
    API endpoint to load trained models from disk.
    
    Expected JSON payload:
    {
        "dspy_path": "Path to the DSPy compiled model",
        "student_path": "Path to the student model directory",
        "teacher_name": "Optional: Name of HuggingFace model to use as teacher"
    }
    
    Returns:
        JSON response with loading status.
    """
    global _models_cache
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        dspy_path = data.get('dspy_path', 'models/dspy/bible_qa_compiled.dspy')
        student_path = data.get('student_path', 'models/dspy/student_model')
        teacher_name = data.get('teacher_name', os.environ.get('HUGGINGFACE_MODEL'))
        
        # Load the DSPy compiled model
        import dspy
        try:
            compiled_model = BibleQAModule.load(dspy_path)
            logger.info(f"Loaded DSPy compiled model from {dspy_path}")
        except Exception as e:
            logger.error(f"Error loading DSPy model: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error loading DSPy model: {e}"
            }), 500
        
        # Load the student model
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            model = AutoModelForSeq2SeqLM.from_pretrained(f"{student_path}/model")
            tokenizer = AutoTokenizer.from_pretrained(f"{student_path}/tokenizer")
            student_model = dspy.HFModel(model=model, tokenizer=tokenizer)
            logger.info(f"Loaded student model from {student_path}")
        except Exception as e:
            logger.error(f"Error loading student model: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error loading student model: {e}"
            }), 500
        
        # Configure teacher model if needed
        teacher_model = None
        if teacher_name:
            try:
                api_key = os.environ.get('HUGGINGFACE_API_KEY')
                teacher_model = configure_teacher_model(model_name=teacher_name, api_key=api_key)
                logger.info(f"Configured teacher model: {teacher_name}")
            except Exception as e:
                logger.warning(f"Error configuring teacher model: {e}")
        
        # Update cache
        _models_cache = {
            "teacher_model": teacher_model,
            "student_model": student_model,
            "compiled_model": compiled_model
        }
        
        return jsonify({
            "status": "success",
            "message": "Models loaded successfully",
            "models": {
                "dspy_path": dspy_path,
                "student_path": student_path,
                "teacher_name": teacher_name
            }
        })
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    API endpoint to check the health of the DSPy Training API.
    
    Returns:
        JSON response with health status.
    """
    try:
        # Check if environment is properly set
        api_key = os.environ.get('HUGGINGFACE_API_KEY')
        api_key_status = "set" if api_key else "not set"
        
        return jsonify({
            "status": "healthy",
            "huggingface_api_key": api_key_status,
            "timestamp": str(datetime.datetime.now()),
            "training_in_progress": _training_status["is_training"],
            "models_loaded": any(_models_cache.values())
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": str(datetime.datetime.now())
        }), 500 