#!/usr/bin/env python3
"""
Web application for STEPBible lexicons and tagged Bible texts.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('web_app')

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# API Base URL - use local host if running on same server
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
logger.info(f"Using API Base URL: {API_BASE_URL}")

@app.route('/')
def index():
    """Simple home page."""
    return "Web application is running!"

if __name__ == '__main__':
    print("Starting web application on port 5001...")
    app.run(debug=True, port=5001) 