#!/usr/bin/env python
"""
Minimal DSPy API server for BibleScholarProject.
"""
import os
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Index route."""
    return "Minimal Bible QA API Server"

@app.route('/test', methods=['POST'])
def test_model():
    """Simple test endpoint with hardcoded responses"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        context = data.get('context', '')
        question = data.get('question', '')
        
        if not context or not question:
            return jsonify({"error": "Both 'context' and 'question' are required"}), 400
        
        # Hard-coded responses for specific Bible questions
        if "beginning" in context.lower() and "created" in question.lower():
            answer = "God created the heavens and the earth."
        elif "jesus" in context.lower() and "son" in question.lower():
            answer = "Jesus is the Son of God."
        else:
            # Default answer
            answer = "The answer can be found in the Bible context: " + context[:20] + "..."
        
        logger.info(f"Processed question: {question}")
        logger.info(f"Generated answer: {answer}")
        
        return jsonify({
            "answer": answer,
            "context": context,
            "question": question
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app
    app.run(host='0.0.0.0', port=5004) 