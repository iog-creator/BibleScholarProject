"""
External Resources API for STEPBible Explorer (Simplified Version).
"""

import os
import logging
from flask import jsonify, request, Blueprint

# Configure logging
logger = logging.getLogger(__name__)

# Create a Blueprint for the external resources API
external_resources_bp = Blueprint('external_resources', __name__)

# Initialize the API
def initialize_api():
    """Initialize the external resources API."""
    logger.info("Initializing External Resources API")
    logger.info("Loaded API keys for: No APIs configured")

# Call initialize_api immediately
initialize_api()

# API Endpoints
@external_resources_bp.route('/api/external/status', methods=['GET'])
def api_status():
    """Check the status of external API integrations."""
    return jsonify({
        "status": "active",
        "available_apis": [],
        "cache_size": 0,
        "cache_duration_seconds": 86400
    }) 