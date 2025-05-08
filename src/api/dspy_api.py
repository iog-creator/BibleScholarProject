"""
DSPy Training API for BibleScholarProject with DSPy 2.6 Features

This API provides endpoints for Bible question answering with DSPy 2.6 features:
- Multi-turn conversation history
- Enhanced theological accuracy via assertions
- MLflow integration for tracking

Version: 2.0.0
"""
from flask import Blueprint, request, jsonify, session
import os
import sys
import json
import logging
import dspy
import mlflow
from datetime import datetime

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dspy_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Blueprint for DSPy API
api_blueprint = Blueprint('dspy', __name__)

# Initialize model (loaded on first request)
dspy_model = None
model_loading_error = None

# Conversation history storage
# In a production environment, this would use a database
conversation_histories = {}

# Import the dspy modules once the blueprint is ready
@api_blueprint.before_app_first_request
def initialize_dspy_model():
    """Initialize the DSPy model when the app starts."""
    global dspy_model, model_loading_error
    
    try:
        # Import DSPy components
        from src.dspy_programs.bible_qa_dspy26 import BibleQAModule
        from src.dspy_programs.huggingface_integration import configure_teacher_model
        
        # Set up MLflow for tracking
        mlflow.set_tracking_uri("file:./mlruns")
        mlflow.set_experiment("dspy_api_usage")
        
        # Configure LM
        lm = configure_teacher_model(model_category="high")
        dspy.settings.configure(lm=lm)
        
        # Find the latest model
        model_dir = "models/dspy"
        if os.path.exists(model_dir):
            model_files = [f for f in os.listdir(model_dir) 
                          if f.startswith("bible_qa_") and f.endswith(".dspy")]
            
            if model_files:
                # Sort by modification time (newest first)
                model_files.sort(key=lambda f: os.path.getmtime(os.path.join(model_dir, f)), reverse=True)
                model_path = os.path.join(model_dir, model_files[0])
                
                # Load the model
                logger.info(f"Loading DSPy model from {model_path}")
                dspy_model = dspy.Module.load(model_path)
                logger.info("DSPy model loaded successfully")
            else:
                # Fall back to a new model if no saved model is found
                logger.warning("No trained model found, using default BibleQAModule")
                dspy_model = BibleQAModule()
        else:
            # Fall back to a new model if directory doesn't exist
            logger.warning(f"Model directory {model_dir} not found, using default BibleQAModule")
            dspy_model = BibleQAModule()
            
    except Exception as e:
        logger.error(f"Error initializing DSPy model: {e}")
        model_loading_error = str(e)

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    global dspy_model, model_loading_error
    
    status = "ok" if dspy_model is not None else "error"
    message = "DSPy API is running with model loaded" if dspy_model is not None else f"Error loading model: {model_loading_error}"
    
    return jsonify({
        "status": status,
        "message": message,
        "version": "2.0.0",
        "dspy_version": dspy.__version__
    })

@api_blueprint.route('/ask', methods=['POST'])
def ask_question():
    """
    Ask a question without context.
    
    Expected JSON payload:
    {
        "question": "Who was Moses?",
        "session_id": "optional-session-id-for-conversation-history"
    }
    """
    global dspy_model
    
    if dspy_model is None:
        return jsonify({
            "error": "DSPy model not initialized",
            "details": model_loading_error
        }), 500
    
    # Get request data
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        question = data.get('question')
        if not question:
            return jsonify({"error": "No question provided"}), 400
            
        # Get session ID for conversation history
        session_id = data.get('session_id', request.remote_addr)
        
        # Get conversation history for this session
        history = conversation_histories.get(session_id, [])
        
        # Generate prediction
        with mlflow.start_run(run_name=f"api_ask_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            mlflow.log_param("question", question)
            mlflow.log_param("history_length", len(history))
            
            prediction = dspy_model(
                context="",
                question=question,
                history=history
            )
            
            mlflow.log_metric("response_length", len(prediction.answer))
        
        # Update conversation history
        history.append((question, prediction.answer))
        
        # Limit history to last 10 turns
        if len(history) > 10:
            history = history[-10:]
            
        # Store updated history
        conversation_histories[session_id] = history
        
        # Return the answer
        return jsonify({
            "question": question,
            "answer": prediction.answer,
            "session_id": session_id,
            "history_length": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return jsonify({
            "error": "Error processing request",
            "details": str(e)
        }), 500

@api_blueprint.route('/ask_with_context', methods=['POST'])
def ask_with_context():
    """
    Ask a question with Bible context.
    
    Expected JSON payload:
    {
        "question": "Who was Moses?",
        "context": "Moses led the Israelites out of Egypt...",
        "session_id": "optional-session-id-for-conversation-history"
    }
    """
    global dspy_model
    
    if dspy_model is None:
        return jsonify({
            "error": "DSPy model not initialized",
            "details": model_loading_error
        }), 500
    
    # Get request data
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        question = data.get('question')
        if not question:
            return jsonify({"error": "No question provided"}), 400
            
        context = data.get('context', "")
        
        # Get session ID for conversation history
        session_id = data.get('session_id', request.remote_addr)
        
        # Get conversation history for this session
        history = conversation_histories.get(session_id, [])
        
        # Generate prediction
        with mlflow.start_run(run_name=f"api_ask_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            mlflow.log_param("question", question)
            mlflow.log_param("context_length", len(context))
            mlflow.log_param("history_length", len(history))
            
            prediction = dspy_model(
                context=context,
                question=question,
                history=history
            )
            
            mlflow.log_metric("response_length", len(prediction.answer))
        
        # Update conversation history
        history.append((question, prediction.answer))
        
        # Limit history to last 10 turns
        if len(history) > 10:
            history = history[-10:]
            
        # Store updated history
        conversation_histories[session_id] = history
        
        # Return the answer
        return jsonify({
            "question": question,
            "answer": prediction.answer,
            "context": context,
            "session_id": session_id,
            "history_length": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return jsonify({
            "error": "Error processing request",
            "details": str(e)
        }), 500

@api_blueprint.route('/conversation', methods=['GET'])
def get_conversation_history():
    """
    Get conversation history for a session.
    
    Query parameters:
    - session_id: Optional session ID (uses IP address if not provided)
    """
    # Get session ID
    session_id = request.args.get('session_id', request.remote_addr)
    
    # Get conversation history
    history = conversation_histories.get(session_id, [])
    
    # Format conversation
    conversation = [
        {"role": "user", "content": q, "turn": i+1} if i % 2 == 0 else 
        {"role": "assistant", "content": a, "turn": i+1} 
        for i, (q, a) in enumerate(history)
    ]
    
    return jsonify({
        "session_id": session_id,
        "conversation": conversation,
        "turns": len(history)
    })

@api_blueprint.route('/conversation', methods=['DELETE'])
def clear_conversation_history():
    """
    Clear conversation history for a session.
    
    Query parameters:
    - session_id: Optional session ID (uses IP address if not provided)
    """
    # Get session ID
    session_id = request.args.get('session_id', request.remote_addr)
    
    # Clear conversation history
    if session_id in conversation_histories:
        del conversation_histories[session_id]
    
    return jsonify({
        "status": "ok",
        "message": f"Conversation history cleared for session {session_id}"
    }) 