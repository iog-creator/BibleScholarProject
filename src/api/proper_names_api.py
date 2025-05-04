#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Proper Names API

This module provides API endpoints for accessing biblical proper names data.
"""

import os
import logging
from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.db_utils import get_db_connection

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
proper_names_api = Blueprint('proper_names_api', __name__)

@proper_names_api.route('/', methods=['GET'])
def get_proper_names():
    """Get biblical proper names with optional filtering and sorting"""
    try:
        # Get query parameters
        search_term = request.args.get('q', '')
        sort_by = request.args.get('sort', 'name')  # name, occurrences, type
        sort_dir = request.args.get('dir', 'asc')  # asc, desc
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        name_type = request.args.get('type', '')  # person, place, ethnic
        min_occurrences = request.args.get('min_occurrences', 0, type=int)
        
        # Validate input parameters
        valid_sort_fields = ['name', 'occurrences', 'type']
        if sort_by not in valid_sort_fields:
            sort_by = 'name'
            
        if sort_dir.lower() not in ['asc', 'desc']:
            sort_dir = 'asc'
            
        # Build query
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT n.id, n.name, n.transliteration, n.name_type, n.strongs_id,
                       n.full_description, COUNT(o.id) as occurrence_count
                FROM bible.proper_names n
                LEFT JOIN bible.name_occurrences o ON n.id = o.name_id
                WHERE 1=1
            """
            params = []
            
            # Add search filter if provided
            if search_term:
                query += " AND (n.name ILIKE %s OR n.transliteration ILIKE %s OR n.strongs_id = %s)"
                params.extend([f"%{search_term}%", f"%{search_term}%", search_term.upper()])
                
            # Add type filter if provided
            if name_type:
                query += " AND n.name_type = %s"
                params.append(name_type)
                
            # Group by name fields for counting
            query += " GROUP BY n.id, n.name, n.transliteration, n.name_type, n.strongs_id, n.full_description"
            
            # Add minimum occurrences filter if provided
            if min_occurrences > 0:
                query += " HAVING COUNT(o.id) >= %s"
                params.append(min_occurrences)
                
            # Add sorting
            if sort_by == 'name':
                query += f" ORDER BY n.name {sort_dir}"
            elif sort_by == 'occurrences':
                query += f" ORDER BY occurrence_count {sort_dir}"
            elif sort_by == 'type':
                query += f" ORDER BY n.name_type {sort_dir}, n.name ASC"
                
            # Add pagination
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            names = cur.fetchall()
            
            # Get total count for pagination
            count_query = """
                SELECT COUNT(*) as count
                FROM (
                    SELECT n.id, COUNT(o.id) as occurrence_count
                    FROM bible.proper_names n
                    LEFT JOIN bible.name_occurrences o ON n.id = o.name_id
                    WHERE 1=1
            """
            count_params = []
            
            # Add filters to count query
            if search_term:
                count_query += " AND (n.name ILIKE %s OR n.transliteration ILIKE %s OR n.strongs_id = %s)"
                count_params.extend([f"%{search_term}%", f"%{search_term}%", search_term.upper()])
                
            if name_type:
                count_query += " AND n.name_type = %s"
                count_params.append(name_type)
                
            count_query += " GROUP BY n.id"
            
            if min_occurrences > 0:
                count_query += " HAVING COUNT(o.id) >= %s"
                count_params.append(min_occurrences)
                
            count_query += ") as filtered_names"
            
            cur.execute(count_query, count_params)
            total_count = cur.fetchone()["count"]
            
            # Get type counts for filtering
            cur.execute("""
                SELECT name_type, COUNT(*) as count
                FROM bible.proper_names
                GROUP BY name_type
                ORDER BY count DESC
            """)
            type_counts = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "names": names,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "type_counts": {
                t["name_type"]: t["count"] for t in type_counts
            }
        }
        
        if search_term:
            response["search_term"] = search_term
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving proper names: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proper_names_api.route('/<int:name_id>', methods=['GET'])
def get_proper_name(name_id):
    """Get a specific proper name by ID with its occurrences"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get name details
            cur.execute("""
                SELECT id, name, transliteration, name_type, strongs_id, full_description
                FROM bible.proper_names
                WHERE id = %s
            """, [name_id])
            name_data = cur.fetchone()
            
            if not name_data:
                return jsonify({"error": "Name not found"}), 404
            
            # Get occurrences
            cur.execute("""
                SELECT o.id, o.reference, o.context_text,
                       v.book_name, v.chapter_num, v.verse_num, v.text as verse_text
                FROM bible.name_occurrences o
                JOIN bible.verses v ON o.reference = CONCAT(v.book_name, ' ', v.chapter_num, ':', v.verse_num)
                WHERE o.name_id = %s
                ORDER BY v.book_name, v.chapter_num, v.verse_num
            """, [name_id])
            occurrences = cur.fetchall()
            
            # Get related names (if any)
            cur.execute("""
                SELECT r.related_name_id, n.name, n.transliteration, n.name_type,
                       r.relationship_type, COUNT(o.id) as occurrence_count
                FROM bible.name_relationships r
                JOIN bible.proper_names n ON r.related_name_id = n.id
                LEFT JOIN bible.name_occurrences o ON n.id = o.name_id
                WHERE r.name_id = %s
                GROUP BY r.related_name_id, n.name, n.transliteration, n.name_type, r.relationship_type
                ORDER BY n.name
            """, [name_id])
            related_names = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "name": name_data,
            "occurrences": occurrences,
            "occurrence_count": len(occurrences),
            "related_names": related_names
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving proper name {name_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proper_names_api.route('/search', methods=['GET'])
def search_proper_names():
    """Search proper names by name, transliteration, or Strong's ID"""
    try:
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not search_term:
            return jsonify({"error": "Search query is required"}), 400
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Search for names
            cur.execute("""
                SELECT n.id, n.name, n.transliteration, n.name_type, n.strongs_id,
                       COUNT(o.id) as occurrence_count
                FROM bible.proper_names n
                LEFT JOIN bible.name_occurrences o ON n.id = o.name_id
                WHERE n.name ILIKE %s
                   OR n.transliteration ILIKE %s
                   OR n.strongs_id ILIKE %s
                GROUP BY n.id, n.name, n.transliteration, n.name_type, n.strongs_id
                ORDER BY 
                    CASE WHEN n.name ILIKE %s THEN 0
                         WHEN n.name ILIKE %s THEN 1
                         ELSE 2
                    END,
                    occurrence_count DESC
                LIMIT %s
            """, [
                f"{search_term}%",   # Exact start match
                f"%{search_term}%",  # Contains match
                f"%{search_term}%",  # Strong's match
                f"{search_term}%",   # For ordering - exact start match
                f"%{search_term}%",  # For ordering - contains match
                limit
            ])
            names = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "query": search_term,
            "results": names,
            "total_results": len(names)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error searching proper names: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proper_names_api.route('/stats', methods=['GET'])
def get_name_stats():
    """Get statistics about proper names"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get name type counts
            cur.execute("""
                SELECT name_type, COUNT(*) as count
                FROM bible.proper_names
                GROUP BY name_type
                ORDER BY count DESC
            """)
            type_counts = cur.fetchall()
            
            # Get total name count
            cur.execute("SELECT COUNT(*) as count FROM bible.proper_names")
            total_count = cur.fetchone()["count"]
            
            # Get total occurrence count
            cur.execute("SELECT COUNT(*) as count FROM bible.name_occurrences")
            occurrence_count = cur.fetchone()["count"]
            
            # Get most frequent names
            cur.execute("""
                SELECT n.id, n.name, n.transliteration, n.name_type, COUNT(o.id) as occurrence_count
                FROM bible.proper_names n
                JOIN bible.name_occurrences o ON n.id = o.name_id
                GROUP BY n.id, n.name, n.transliteration, n.name_type
                ORDER BY occurrence_count DESC
                LIMIT 10
            """)
            most_frequent = cur.fetchall()
            
            # Get distribution by books
            cur.execute("""
                SELECT SUBSTRING(o.reference FROM '^[^\\s]+') as book,
                       COUNT(*) as occurrence_count
                FROM bible.name_occurrences o
                GROUP BY book
                ORDER BY occurrence_count DESC
                LIMIT 15
            """)
            book_distribution = cur.fetchall()
            
        conn.close()
        
        # Format the response
        response = {
            "total_names": total_count,
            "total_occurrences": occurrence_count,
            "type_counts": {
                t["name_type"]: t["count"] for t in type_counts
            },
            "most_frequent_names": most_frequent,
            "book_distribution": book_distribution
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving name stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proper_names_api.route('/types', methods=['GET'])
def get_name_types():
    """Get all available name types"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT name_type, COUNT(*) as count
                FROM bible.proper_names
                GROUP BY name_type
                ORDER BY count DESC
            """)
            types = cur.fetchall()
            
        conn.close()
        
        return jsonify({"types": types})
        
    except Exception as e:
        logger.error(f"Error retrieving name types: {str(e)}")
        return jsonify({"error": str(e)}), 500 