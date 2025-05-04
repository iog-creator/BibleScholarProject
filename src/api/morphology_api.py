#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Morphology API

This module provides API endpoints for accessing Hebrew and Greek morphology code data.
"""

import os
import logging
from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.db_utils import get_db_connection
from src.utils.file_utils import append_dspy_training_example

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
morphology_api = Blueprint('morphology_api', __name__)

@morphology_api.route('/hebrew', methods=['GET'])
def get_hebrew_morphology_codes():
    """Get Hebrew morphology codes, optionally filtered by a prefix"""
    try:
        prefix = request.args.get('prefix', '')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get morphology codes with optional prefix filter
            query = """
                SELECT code, brief_explanation, full_explanation
                FROM bible.hebrew_morphology_codes
                WHERE code LIKE %s
                ORDER BY code
                LIMIT %s OFFSET %s
            """
            cur.execute(query, [f"{prefix}%", limit, offset])
            codes = cur.fetchall()
            
            # Get total count for pagination
            cur.execute("""
                SELECT COUNT(*) as count
                FROM bible.hebrew_morphology_codes
                WHERE code LIKE %s
            """, [f"{prefix}%"])
            total_count = cur.fetchone()["count"]
            
        conn.close()
        
        # Format the response
        response = {
            "codes": codes,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving Hebrew morphology codes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@morphology_api.route('/hebrew/<code>', methods=['GET'])
def get_hebrew_morphology_code(code):
    """Get a specific Hebrew morphology code by its code value"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the specific morphology code
            cur.execute("""
                SELECT code, brief_explanation, full_explanation, example
                FROM bible.hebrew_morphology_codes
                WHERE code = %s
            """, [code])
            code_data = cur.fetchone()
            
            if not code_data:
                return jsonify({"error": "Morphology code not found"}), 404
            
            # Get example words using this code
            cur.execute("""
                SELECT w.id, w.word, w.strongs_id, w.transliteration, w.translation,
                       v.book_name, v.chapter_num, v.verse_num
                FROM bible.hebrew_ot_words w
                JOIN bible.verses v ON w.verse_id = v.id
                WHERE w.grammar_code LIKE %s
                LIMIT 10
            """, [f"%{code}%"])
            examples = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "code": code_data,
            "examples": examples
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving Hebrew morphology code {code}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@morphology_api.route('/greek', methods=['GET'])
def get_greek_morphology_codes():
    """Get Greek morphology codes, optionally filtered by a prefix"""
    try:
        prefix = request.args.get('prefix', '')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get morphology codes with optional prefix filter
            query = """
                SELECT code, brief_explanation, full_explanation
                FROM bible.greek_morphology_codes
                WHERE code LIKE %s
                ORDER BY code
                LIMIT %s OFFSET %s
            """
            cur.execute(query, [f"{prefix}%", limit, offset])
            codes = cur.fetchall()
            
            # Get total count for pagination
            cur.execute("""
                SELECT COUNT(*) as count
                FROM bible.greek_morphology_codes
                WHERE code LIKE %s
            """, [f"{prefix}%"])
            total_count = cur.fetchone()["count"]
            
        conn.close()
        
        # Format the response
        response = {
            "codes": codes,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving Greek morphology codes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@morphology_api.route('/greek/<code>', methods=['GET'])
def get_greek_morphology_code(code):
    """Get a specific Greek morphology code by its code value"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the specific morphology code
            cur.execute("""
                SELECT code, brief_explanation, full_explanation, example
                FROM bible.greek_morphology_codes
                WHERE code = %s
            """, [code])
            code_data = cur.fetchone()
            
            if not code_data:
                return jsonify({"error": "Morphology code not found"}), 404
            
            # Get example words using this code
            cur.execute("""
                SELECT w.id, w.word, w.strongs_id, w.grammar_code, w.transliteration, w.translation,
                       v.book_name, v.chapter_num, v.verse_num
                FROM bible.greek_nt_words w
                JOIN bible.verses v ON w.verse_id = v.id
                WHERE w.grammar_code LIKE %s
                LIMIT 10
            """, [f"%{code}%"])
            examples = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "code": code_data,
            "examples": examples
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving Greek morphology code {code}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@morphology_api.route('/search', methods=['GET'])
def search_morphology_codes():
    """Search both Hebrew and Greek morphology codes by keyword"""
    try:
        keyword = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({"error": "Search query is required"}), 400
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Search Hebrew morphology codes
            cur.execute("""
                SELECT 'hebrew' as language, code, brief_explanation, full_explanation
                FROM bible.hebrew_morphology_codes
                WHERE code ILIKE %s
                   OR brief_explanation ILIKE %s
                   OR full_explanation ILIKE %s
                LIMIT %s
            """, [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit])
            hebrew_codes = cur.fetchall()
            
            # Search Greek morphology codes
            cur.execute("""
                SELECT 'greek' as language, code, brief_explanation, full_explanation
                FROM bible.greek_morphology_codes
                WHERE code ILIKE %s
                   OR brief_explanation ILIKE %s
                   OR full_explanation ILIKE %s
                LIMIT %s
            """, [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit])
            greek_codes = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "query": keyword,
            "hebrew_results": hebrew_codes,
            "greek_results": greek_codes,
            "total_results": len(hebrew_codes) + len(greek_codes)
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error searching morphology codes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@morphology_api.route('/stats', methods=['GET'])
def get_morphology_stats():
    """Get statistics about morphology codes"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get Hebrew morphology code counts
            cur.execute("SELECT COUNT(*) as count FROM bible.hebrew_morphology_codes")
            hebrew_count = cur.fetchone()["count"]
            
            # Get Greek morphology code counts
            cur.execute("SELECT COUNT(*) as count FROM bible.greek_morphology_codes")
            greek_count = cur.fetchone()["count"]
            
            # Get most common Hebrew codes in use
            cur.execute("""
                SELECT SUBSTRING(grammar_code FROM '([A-Za-z0-9]+)') as code, COUNT(*) as count
                FROM bible.hebrew_ot_words
                WHERE grammar_code IS NOT NULL
                GROUP BY code
                ORDER BY count DESC
                LIMIT 10
            """)
            common_hebrew_codes = cur.fetchall()
            
            # Get most common Greek codes in use
            cur.execute("""
                SELECT SUBSTRING(grammar_code FROM '([A-Za-z0-9-]+)') as code, COUNT(*) as count
                FROM bible.greek_nt_words
                WHERE grammar_code IS NOT NULL
                GROUP BY code
                ORDER BY count DESC
                LIMIT 10
            """)
            common_greek_codes = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "code_counts": {
                "hebrew": hebrew_count,
                "greek": greek_count,
                "total": hebrew_count + greek_count
            },
            "most_common": {
                "hebrew": common_hebrew_codes,
                "greek": common_greek_codes
            }
        }
        
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/morphology_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving morphology stats: {str(e)}")
        return jsonify({"error": str(e)}), 500 