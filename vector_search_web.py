#!/usr/bin/env python3
"""
Simplified Vector Search Web Application for BibleScholarProject
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import requests
import sys

# Import the vector search API
from src.api.vector_search_api import vector_search_api

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vector_search_web')

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# Register the vector search API
app.register_blueprint(vector_search_api, url_prefix='/api')

# API Base URL - use local host if running on same server
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
logger.info(f"Using API Base URL: {API_BASE_URL}")

# Database connection
def get_db_connection():
    """
    Get a connection to the PostgreSQL database.
    Tries to use secure connection if available, otherwise falls back to standard connection.
    Returns None if connection fails.
    """
    try:
        # First try to use secure connection with read-only mode
        try:
            from src.database.secure_connection import get_secure_connection
            logger.info("Using secure READ-ONLY database connection")
            return get_secure_connection(mode='read')
        except ImportError:
            # Secure connection module not available, use regular connection
            logger.info("Secure connection not available, using standard connection")
            pass
        
        # Fall back to standard connection
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        logger.info("Using standard database connection")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    """Redirect to vector search page."""
    return redirect(url_for('vector_search_page'))

@app.route('/health')
def health_check():
    """Health check endpoint for API connection verification."""
    return jsonify({"status": "OK"}), 200

@app.route('/vector-search')
def vector_search_page():
    """
    Display vector-based semantic search form and results.
    """
    query = request.args.get('q', '')
    translation = request.args.get('translation', 'KJV')
    
    results = None
    error = None
    
    if query:
        try:
            # Make the API request to get semantic search results
            response = requests.get(f"{API_BASE_URL}/api/vector-search",
                                  params={'q': query, 'translation': translation, 'limit': 20})
            
            if response.status_code == 200:
                results = response.json()
            else:
                error = response.json().get('error', 'Unknown error')
                logger.error(f"Vector search API error: {error}")
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            error = f"An error occurred: {str(e)}"
    
    # Get available translations for the dropdown
    try:
        trans_response = requests.get(f"{API_BASE_URL}/api/available-translations")
        available_translations = []
        if trans_response.status_code == 200:
            available_translations = [t['translation_source'] for t in trans_response.json().get('translations', [])]
    except Exception:
        # Default translations if we can't get the list
        available_translations = ['KJV', 'ASV']
    
    return render_template('vector_search.html',
                          query=query,
                          translation=translation,
                          results=results,
                          error=error,
                          available_translations=available_translations)

@app.route('/similar-verses')
def similar_verses_page():
    """
    Display similar verses page.
    """
    book = request.args.get('book', '')
    chapter = request.args.get('chapter', '')
    verse = request.args.get('verse', '')
    translation = request.args.get('translation', 'KJV')
    
    results = None
    error = None
    
    if book and chapter and verse:
        try:
            # Make API request to similar-verses endpoint
            response = requests.get(f"{API_BASE_URL}/api/similar-verses",
                                   params={'book': book, 'chapter': chapter, 'verse': verse, 
                                           'translation': translation, 'limit': 20})
            
            if response.status_code == 200:
                results = response.json()
            else:
                error = response.json().get('error', 'Unknown error')
                logger.error(f"Similar verses API error: {error}")
                
        except Exception as e:
            logger.error(f"Error finding similar verses: {e}")
            error = f"An error occurred: {str(e)}"
    
    # Get available translations for the dropdown
    try:
        trans_response = requests.get(f"{API_BASE_URL}/api/available-translations")
        available_translations = []
        if trans_response.status_code == 200:
            available_translations = [t['translation_source'] for t in trans_response.json().get('translations', [])]
    except Exception:
        # Default translations if we can't get the list
        available_translations = ['KJV', 'ASV']
    
    return render_template('similar_verses.html',
                          book=book,
                          chapter=chapter,
                          verse=verse,
                          translation=translation,
                          results=results,
                          error=error,
                          available_translations=available_translations)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5001) 