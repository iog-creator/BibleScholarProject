"""
Comprehensive Search API for BibleScholarProject.
"""

from flask import Blueprint, jsonify

# Create Blueprint for comprehensive search API
comprehensive_search_api = Blueprint('comprehensive_search', __name__)

@comprehensive_search_api.route('/status', methods=['GET'])
def status():
    """Status endpoint for comprehensive search API."""
    return jsonify({
        "status": "ok",
        "message": "Comprehensive Search API is running",
        "version": "1.0.0"
    }) 