"""
Comprehensive Search API module.

This module provides endpoints for semantic search across all Bible database resources:
- Verses across translations
- Lexicon entries
- Word-level morphological data
- Proper names and relationships
- Cross-language theological terms
- Arabic text
"""

from flask import Blueprint

comprehensive_search_api = Blueprint('comprehensive_search_api', __name__)

# Import route definitions after Blueprint creation to avoid circular imports
from . import routes 