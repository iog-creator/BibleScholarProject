"""
External Resources API for STEPBible Explorer.

This module provides API endpoints for integrating with external biblical resources,
such as commentaries, academic repositories, and biblical reference materials.
"""

import os
import json
import time
import logging
import requests
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Blueprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create a Blueprint for the external resources API
external_resources_bp = Blueprint('external_resources', __name__)

# Initialize cache storage
resource_cache = {}
api_keys = {}

# Cache configuration
CACHE_DURATION = int(os.getenv('EXTERNAL_RESOURCE_CACHE_DURATION', 86400))  # Default: 1 day in seconds

def load_api_keys():
    """Load API keys for external services from environment variables."""
    api_keys['BIBLE_GATEWAY'] = os.getenv('BIBLE_GATEWAY_API_KEY', '')
    api_keys['ESV_API'] = os.getenv('ESV_API_KEY', '')
    api_keys['BIBLE_ORG'] = os.getenv('BIBLE_ORG_API_KEY', '')
    api_keys['DIGITAL_THEOLOGICAL_LIBRARY'] = os.getenv('DTL_API_KEY', '')
    api_keys['ARCHAEOLOGICAL_DB'] = os.getenv('ARCHAEOLOGICAL_DB_API_KEY', '')
    
    # Log available API integrations
    available_apis = [name for name, key in api_keys.items() if key]
    logger.info(f"Loaded API keys for: {', '.join(available_apis) if available_apis else 'No APIs configured'}")
    
    return api_keys

# Decorator for API key validation
def require_api_key(api_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not api_keys.get(api_name):
                return jsonify({
                    "error": f"No API key configured for {api_name}",
                    "status": "error"
                }), 503
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Cache utility functions
def get_from_cache(cache_key):
    """Retrieve data from cache if available and not expired."""
    if cache_key in resource_cache:
        cached_item = resource_cache[cache_key]
        if cached_item['expires_at'] > datetime.now():
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_item['data']
        else:
            # Cache expired
            logger.debug(f"Cache expired for key: {cache_key}")
            del resource_cache[cache_key]
    return None

def save_to_cache(cache_key, data, duration=CACHE_DURATION):
    """Save data to cache with expiration time."""
    expires_at = datetime.now() + timedelta(seconds=duration)
    resource_cache[cache_key] = {
        'data': data,
        'expires_at': expires_at
    }
    logger.debug(f"Saved to cache: {cache_key}, expires: {expires_at}")
    return data

# Initialize the API
def initialize_api():
    """Initialize the external resources API."""
    logger.info("Initializing External Resources API")
    load_api_keys()

# Call initialize_api immediately for testing purposes
initialize_api()

# API Endpoints

@external_resources_bp.route('/api/external/status', methods=['GET'])
def api_status():
    """Check the status of external API integrations."""
    available_apis = [name for name, key in api_keys.items() if key]
    return jsonify({
        "status": "active",
        "available_apis": available_apis,
        "cache_size": len(resource_cache),
        "cache_duration_seconds": CACHE_DURATION
    })

@external_resources_bp.route('/api/external/commentaries/<book>/<chapter>/<verse>', methods=['GET'])
def get_commentaries(book, chapter, verse):
    """
    Get commentaries for a specific Bible reference from external sources.
    
    Args:
        book (str): Bible book name
        chapter (int): Chapter number
        verse (int): Verse number
        
    Returns:
        JSON with commentary content from available sources
    """
    cache_key = f"commentaries_{book}_{chapter}_{verse}"
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # Initialize results
    results = {
        "reference": f"{book} {chapter}:{verse}",
        "commentaries": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Process available commentary sources
    if api_keys.get('BIBLE_GATEWAY'):
        bg_commentary = fetch_bible_gateway_commentary(book, chapter, verse)
        if bg_commentary:
            results["commentaries"].append(bg_commentary)
    
    if api_keys.get('DIGITAL_THEOLOGICAL_LIBRARY'):
        dtl_commentary = fetch_dtl_commentary(book, chapter, verse)
        if dtl_commentary:
            results["commentaries"].append(dtl_commentary)
    
    # Save to cache and return
    save_to_cache(cache_key, results)
    return jsonify(results)

@external_resources_bp.route('/api/external/archaeological/<location>', methods=['GET'])
def get_archaeological_data(location):
    """
    Get archaeological data for a biblical location.
    
    Args:
        location (str): Biblical location name
        
    Returns:
        JSON with archaeological information
    """
    cache_key = f"archaeological_{location}"
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # Initialize results
    results = {
        "location": location,
        "archaeological_data": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Process available archaeological sources
    if api_keys.get('ARCHAEOLOGICAL_DB'):
        arch_data = fetch_archaeological_data(location)
        if arch_data:
            results["archaeological_data"] = arch_data
    
    # Save to cache and return
    save_to_cache(cache_key, results)
    return jsonify(results)

@external_resources_bp.route('/api/external/translations/<reference>', methods=['GET'])
def get_translations(reference):
    """
    Get multiple Bible translations for a verse reference.
    
    Args:
        reference (str): Bible reference (e.g., "John 3:16")
        
    Returns:
        JSON with verse text in multiple translations
    """
    translations = request.args.get('translations', 'ESV,NIV,KJV')
    translation_list = translations.split(',')
    
    cache_key = f"translations_{reference}_{translations}"
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # Initialize results
    results = {
        "reference": reference,
        "translations": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Fetch from available translation APIs
    if api_keys.get('ESV_API') and 'ESV' in translation_list:
        esv_text = fetch_esv_translation(reference)
        if esv_text:
            results["translations"]["ESV"] = esv_text
    
    if api_keys.get('BIBLE_GATEWAY'):
        for translation in translation_list:
            if translation != 'ESV' or not api_keys.get('ESV_API'):
                text = fetch_bible_gateway_translation(reference, translation)
                if text:
                    results["translations"][translation] = text
    
    # Save to cache and return
    save_to_cache(cache_key, results)
    return jsonify(results)

@external_resources_bp.route('/api/external/manuscripts/<reference>', methods=['GET'])
def get_manuscript_data(reference):
    """
    Get manuscript data and variants for a verse reference.
    
    Args:
        reference (str): Bible reference (e.g., "John 1:1")
        
    Returns:
        JSON with manuscript information and variants
    """
    cache_key = f"manuscripts_{reference}"
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # Initialize results
    results = {
        "reference": reference,
        "manuscripts": [],
        "variants": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Process available manuscript sources
    if api_keys.get('DIGITAL_THEOLOGICAL_LIBRARY'):
        manuscript_data = fetch_manuscript_data(reference)
        if manuscript_data:
            results.update(manuscript_data)
    
    # Save to cache and return
    save_to_cache(cache_key, results)
    return jsonify(results)

@external_resources_bp.route('/api/external/lexicons/<strongs_id>', methods=['GET'])
def get_external_lexicon(strongs_id):
    """
    Get lexicon information from external sources.
    
    Args:
        strongs_id (str): Strong's number (e.g., "G1234" or "H5678")
        
    Returns:
        JSON with lexicon entries from external sources
    """
    cache_key = f"external_lexicon_{strongs_id}"
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # Initialize results
    results = {
        "strongs_id": strongs_id,
        "external_entries": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Process available lexicon sources
    if api_keys.get('BIBLE_ORG'):
        lexicon_data = fetch_bible_org_lexicon(strongs_id)
        if lexicon_data:
            results["external_entries"].append(lexicon_data)
    
    # Save to cache and return
    save_to_cache(cache_key, results)
    return jsonify(results)

@external_resources_bp.route('/api/external/citations/<reference>', methods=['GET'])
def get_citation_formats(reference):
    """
    Get standardized citation formats for a Bible reference.
    
    Args:
        reference (str): Bible reference (e.g., "John 3:16")
        
    Returns:
        JSON with citation formats
    """
    style = request.args.get('style', 'chicago')
    
    results = {
        "reference": reference,
        "citations": {
            "chicago": format_chicago_citation(reference),
            "mla": format_mla_citation(reference),
            "apa": format_apa_citation(reference),
            "sbl": format_sbl_citation(reference)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(results)

@external_resources_bp.route('/api/external/cache/clear', methods=['POST'])
def clear_cache():
    """Admin endpoint to clear the external resources cache."""
    global resource_cache
    cache_size = len(resource_cache)
    resource_cache = {}
    
    return jsonify({
        "status": "success",
        "message": f"Cleared {cache_size} items from cache",
        "timestamp": datetime.now().isoformat()
    })

# Helper functions for external API fetching

def fetch_bible_gateway_commentary(book, chapter, verse):
    """Fetch commentary from Bible Gateway API."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching Bible Gateway commentary for {book} {chapter}:{verse}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "source": "Bible Gateway",
            "title": "Matthew Henry's Commentary",
            "content": f"Commentary text for {book} {chapter}:{verse} would appear here.",
            "url": f"https://www.biblegateway.com/passage/?search={book}+{chapter}%3A{verse}&version=NIV",
            "attribution": "Matthew Henry's Commentary on the Whole Bible, Bible Gateway"
        }
    except Exception as e:
        logger.error(f"Error fetching Bible Gateway commentary: {e}")
        return None

def fetch_dtl_commentary(book, chapter, verse):
    """Fetch commentary from Digital Theological Library."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching DTL commentary for {book} {chapter}:{verse}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "source": "Digital Theological Library",
            "title": "Critical and Exegetical Commentary",
            "content": f"Scholarly commentary for {book} {chapter}:{verse} from academic sources.",
            "scholars": ["Scholar A", "Scholar B"],
            "year": 2023,
            "attribution": "Digital Theological Library, Academic Commentary Collection"
        }
    except Exception as e:
        logger.error(f"Error fetching DTL commentary: {e}")
        return None

def fetch_archaeological_data(location):
    """Fetch archaeological data for a biblical location."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching archaeological data for {location}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "location_name": location,
            "modern_name": f"Modern equivalent of {location}",
            "coordinates": {"lat": 31.7683, "lng": 35.2137},
            "excavation_periods": ["1920-1925", "1978-1982", "2005-Present"],
            "artifacts": [
                {"name": "Example artifact 1", "date": "8th century BCE", "description": "Description of artifact 1"},
                {"name": "Example artifact 2", "date": "1st century CE", "description": "Description of artifact 2"}
            ],
            "references": [
                {"title": "Archaeological Reference 1", "author": "Author Name", "year": 2010},
                {"title": "Archaeological Reference 2", "author": "Author Name", "year": 2018}
            ],
            "attribution": "Archaeological Database API"
        }
    except Exception as e:
        logger.error(f"Error fetching archaeological data: {e}")
        return None

def fetch_esv_translation(reference):
    """Fetch ESV translation from the ESV API."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching ESV translation for {reference}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "translation": "ESV",
            "text": f"The ESV text for {reference} would appear here.",
            "copyright": "ESV® Bible (The Holy Bible, English Standard Version®) ©2001 by Crossway Bibles",
            "attribution": "Scripture quotations marked 'ESV' are from the ESV® Bible (The Holy Bible, English Standard Version®), copyright © 2001 by Crossway Bibles, a publishing ministry of Good News Publishers. Used by permission. All rights reserved."
        }
    except Exception as e:
        logger.error(f"Error fetching ESV translation: {e}")
        return None

def fetch_bible_gateway_translation(reference, translation):
    """Fetch a Bible translation from Bible Gateway."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching {translation} translation for {reference}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "translation": translation,
            "text": f"The {translation} text for {reference} would appear here.",
            "copyright": f"Copyright information for {translation}",
            "attribution": f"Bible Gateway, {translation} translation"
        }
    except Exception as e:
        logger.error(f"Error fetching {translation} translation: {e}")
        return None

def fetch_manuscript_data(reference):
    """Fetch manuscript data and variants for a reference."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching manuscript data for {reference}")
        time.sleep(0.1)  # Simulate API latency
        
        return {
            "manuscripts": [
                {"id": "p66", "name": "Papyrus 66", "date": "c. 200 CE", "content": "Greek text sample from P66"},
                {"id": "01", "name": "Codex Sinaiticus", "date": "4th century", "content": "Greek text sample from Sinaiticus"}
            ],
            "variants": [
                {
                    "type": "textual_variant",
                    "description": "Some manuscripts read X instead of Y",
                    "manuscripts_supporting": ["p66", "B", "א"],
                    "manuscripts_opposing": ["A", "D", "W"],
                    "scholarly_notes": "This variant affects the understanding of the passage in the following ways..."
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching manuscript data: {e}")
        return None

def fetch_bible_org_lexicon(strongs_id):
    """Fetch lexicon data from Bible.org."""
    try:
        # Mock implementation - replace with actual API call
        logger.info(f"Fetching Bible.org lexicon data for {strongs_id}")
        time.sleep(0.1)  # Simulate API latency
        
        is_hebrew = strongs_id.startswith('H')
        
        return {
            "source": "Bible.org Enhanced Strong's Lexicon",
            "strongs_id": strongs_id,
            "original_word": "λόγος" if not is_hebrew else "דָּבָר",
            "transliteration": "logos" if not is_hebrew else "dabar",
            "definition": f"Extended definition for {strongs_id} from Bible.org",
            "etymology": "Etymology information would appear here",
            "usage_examples": [
                {"reference": "John 1:1", "translation": "Word"},
                {"reference": "Romans 1:16", "translation": "message"}
            ],
            "related_words": ["G3056", "G4487"] if not is_hebrew else ["H561", "H1697"],
            "semantic_domain": ["Communication", "Abstract Concepts"],
            "attribution": "Bible.org Enhanced Strong's Lexicon"
        }
    except Exception as e:
        logger.error(f"Error fetching Bible.org lexicon data: {e}")
        return None

def format_chicago_citation(reference):
    """Format citation in Chicago style."""
    return f"The Holy Bible, {reference}."

def format_mla_citation(reference):
    """Format citation in MLA style."""
    return f"The Bible. {reference}. Authorized King James Version, Oxford UP, 1998."

def format_apa_citation(reference):
    """Format citation in APA style."""
    return f"{reference} (King James Version)."

def format_sbl_citation(reference):
    """Format citation in Society of Biblical Literature style."""
    return f"{reference} (NRSV)."

# Main Flask application
def create_external_resources_app():
    """Create a Flask application for the external resources API."""
    app = Flask(__name__)
    app.register_blueprint(external_resources_bp)
    
    # Initialize API keys
    with app.app_context():
        load_api_keys()
    
    return app

if __name__ == "__main__":
    app = create_external_resources_app()
    app.run(debug=True, port=5002) 