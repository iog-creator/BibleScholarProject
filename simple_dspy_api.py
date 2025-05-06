#!/usr/bin/env python
"""
Simplified DSPy API server for BibleScholarProject.
This implementation doesn't try to load models from disk, avoiding those issues.
"""
import os
import json
import logging
import datetime
from pathlib import Path
from flask import Flask, request, jsonify
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
    BibleQAModule
)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Index route."""
    return jsonify({
        "name": "Simplified DSPy API Server",
        "endpoints": [
            "/api/dspy/example - Test trained model"
        ]
    }), 200

@app.route('/api/dspy/example', methods=['POST'])
def test_model():
    """
    API endpoint to test a DSPy model with Bible QA.
    Creates a fresh BibleQAModule for each request.
    
    Expected JSON payload:
    {
        "context": "Biblical context or verse",
        "question": "Question about the context"
    }
    
    Returns:
        JSON response with the model's answer.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        context = data.get('context')
        question = data.get('question')
        
        if not context or not question:
            return jsonify({"status": "error", "message": "Both 'context' and 'question' are required"}), 400
        
        # Always use a fresh LM configuration
        api_key = os.environ.get('HUGGINGFACE_API_KEY', 'dummy_key_for_testing')
        teacher_model_name = os.environ.get('LM_STUDIO_CHAT_MODEL', 'darkidol-llama-3.1-8b-instruct-1.2-uncensored')
        
        # Configure the teacher model
        logger.info(f"Configuring model {teacher_model_name} for inference")
        teacher_lm = configure_teacher_model(api_key=api_key, model_name=teacher_model_name)
        
        # Create a new BibleQAModule for this request
        import dspy
        dspy.configure(lm=teacher_lm)
        module = BibleQAModule()
        
        # Run prediction
        try:
            result = module(context=context, question=question)
            
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
                    "answer": answer,
                    "model": teacher_model_name
                }
            })
        except Exception as e:
            logger.error(f"Error running prediction: {e}")
            import traceback
            traceback.print_exc()
            
            # Generate a simple prompt manually
            prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
            
            # Use the LM directly as fallback
            try:
                answer = teacher_lm(prompt)
                return jsonify({
                    "status": "success",
                    "result": {
                        "context": context,
                        "question": question,
                        "answer": answer,
                        "model": teacher_model_name,
                        "note": "Generated with fallback method due to error"
                    }
                })
            except Exception as e2:
                logger.error(f"Error with fallback prediction: {e2}")
                return jsonify({
                    "status": "error", 
                    "message": f"Error running prediction: {str(e)}"
                }), 500
    
    except Exception as e:
        logger.error(f"Error in test_model: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    API endpoint to check the health of the DSPy API.
    
    Returns:
        JSON response with health status.
    """
    try:
        # Check if environment is properly set
        api_key = os.environ.get('HUGGINGFACE_API_KEY')
        api_key_status = "set" if api_key else "not set"
        lm_studio_url = os.environ.get('LM_STUDIO_API_URL')
        lm_studio_status = "configured" if lm_studio_url else "not configured"
        
        return jsonify({
            "status": "healthy",
            "huggingface_api_key": api_key_status,
            "lm_studio": lm_studio_status,
            "timestamp": str(datetime.datetime.now())
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable or default to 5003
    port = int(os.environ.get('PORT', 5003))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True) 