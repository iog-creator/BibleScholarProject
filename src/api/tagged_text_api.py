#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tagged Text API

This module provides API endpoints for accessing tagged Bible text data.
"""

import os
import logging
import re
from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.db_utils import get_db_connection
from src.utils.file_utils import append_dspy_training_example

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
tagged_text_api = Blueprint('tagged_text_api', __name__)

@tagged_text_api.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about tagged text data"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get verse counts by translation source
            cur.execute("""
                SELECT translation_source, COUNT(*) as verse_count 
                FROM bible.verses 
                GROUP BY translation_source
            """)
            verse_counts = cur.fetchall()
            
            # Get book counts by translation source
            cur.execute("""
                SELECT translation_source, COUNT(DISTINCT book_name) as book_count 
                FROM bible.verses 
                GROUP BY translation_source
            """)
            book_counts = cur.fetchall()
            
            # Get Hebrew word count
            cur.execute("SELECT COUNT(*) as count FROM bible.hebrew_ot_words")
            hebrew_word_count = cur.fetchone()
            
            # Get Greek word count
            cur.execute("SELECT COUNT(*) as count FROM bible.greek_nt_words")
            greek_word_count = cur.fetchone()
            
            # Get Arabic word count
            has_arabic = True
            try:
                cur.execute("SELECT COUNT(*) as count FROM bible.arabic_words")
                arabic_word_count = cur.fetchone()
            except psycopg2.Error:
                has_arabic = False
                arabic_word_count = {"count": 0}
            
        conn.close()
        
        # Format the response
        response = {
            "verses": {
                "total": sum(vc["verse_count"] for vc in verse_counts),
                "by_source": {vc["translation_source"]: vc["verse_count"] for vc in verse_counts}
            },
            "books": {
                "by_source": {bc["translation_source"]: bc["book_count"] for bc in book_counts}
            },
            "words": {
                "hebrew": hebrew_word_count["count"],
                "greek": greek_word_count["count"],
            }
        }
        
        if has_arabic:
            response["words"]["arabic"] = arabic_word_count["count"]
            
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/tagged_text_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving tagged text stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@tagged_text_api.route('/verse', methods=['GET'])
def get_verse():
    """Get a verse with its tagged words"""
    try:
        # Get parameters
        book = request.args.get('book', 'Genesis')
        chapter = request.args.get('chapter', 1, type=int)
        verse = request.args.get('verse', 1, type=int)
        translation = request.args.get('translation', None)
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get verse information
            query = """
                SELECT v.id, v.book_name, v.chapter_num, v.verse_num, 
                       v.text, v.translation_source
                FROM bible.verses v
                WHERE v.book_name = %s AND v.chapter_num = %s AND v.verse_num = %s
            """
            params = [book, chapter, verse]
            
            if translation:
                query += " AND v.translation_source = %s"
                params.append(translation)
            
            cur.execute(query, params)
            verse_data = cur.fetchone()
            
            if not verse_data:
                return jsonify({"error": "Verse not found"}), 404
            
            # Determine if this is OT or NT
            is_ot = is_old_testament(book)
            
            # Get tagged words for the verse
            if is_ot:
                cur.execute("""
                    SELECT w.id, w.word, w.strongs_id, w.grammar_code, w.transliteration, 
                           w.position as word_num, w.translation 
                    FROM bible.hebrew_ot_words w
                    WHERE w.verse_id = %s
                    ORDER BY w.position
                """, [verse_data["id"]])
            else:
                cur.execute("""
                    SELECT w.id, w.word, w.strongs_id, w.grammar_code, w.transliteration, 
                           w.word_num, w.translation 
                    FROM bible.greek_nt_words w
                    WHERE w.verse_id = %s
                    ORDER BY w.word_num
                """, [verse_data["id"]])
            
            words = cur.fetchall()
            
            # Also check if we have Arabic words for this reference
            arabic_words = []
            try:
                # First find the arabic verse
                cur.execute("""
                    SELECT id FROM bible.arabic_verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                """, [book, chapter, verse])
                arabic_verse = cur.fetchone()
                
                if arabic_verse:
                    cur.execute("""
                        SELECT id, word, strongs_id, transliteration, position as word_num, 
                               translation, original_word
                        FROM bible.arabic_words
                        WHERE verse_id = %s
                        ORDER BY position
                    """, [arabic_verse["id"]])
                    arabic_words = cur.fetchall()
            except psycopg2.Error as e:
                # Arabic table might not exist, which is fine
                logger.debug(f"Arabic words retrieval failed, table may not exist: {str(e)}")
        
        conn.close()
        
        # Format the response
        response = {
            "verse": verse_data,
            "words": words
        }
        
        if arabic_words:
            response["arabic_words"] = arabic_words
            
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/tagged_text_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving verse: {str(e)}")
        return jsonify({"error": str(e)}), 500

@tagged_text_api.route('/search', methods=['GET'])
def search_by_strongs():
    """Search for occurrences of words by Strong's ID"""
    try:
        # Get parameters
        strongs_id = request.args.get('strongs_id', '').strip()
        book = request.args.get('book', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not strongs_id:
            return jsonify({"error": "Strong's ID is required"}), 400
        
        # Determine if this is a Hebrew or Greek Strong's number
        is_hebrew = strongs_id.upper().startswith('H')
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Construct query based on Hebrew or Greek
            table = "bible.hebrew_ot_words" if is_hebrew else "bible.greek_nt_words"
            verse_join = "bible.verses"
            strongs_pattern = strongs_id.upper()
            
            # Special handling for extended Strong's IDs with letter suffixes
            if is_hebrew and not re.match(r'^H\d+[a-zA-Z]?$', strongs_pattern):
                strongs_pattern = f"{strongs_pattern}%"
            
            query = f"""
                SELECT v.book_name, v.chapter_num, v.verse_num, v.text as verse_text,
                       w.word, w.strongs_id, w.grammar_code, w.transliteration,
                       w.{'position' if is_hebrew else 'word_num'} as word_num, w.translation
                FROM {table} w
                JOIN {verse_join} v ON w.verse_id = v.id
                WHERE w.strongs_id LIKE %s
            """
            params = [strongs_pattern]
            
            if book:
                query += " AND v.book_name = %s"
                params.append(book)
            
            query += " ORDER BY v.book_name, v.chapter_num, v.verse_num"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            occurrences = cur.fetchall()
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table} w
                JOIN {verse_join} v ON w.verse_id = v.id
                WHERE w.strongs_id LIKE %s
            """
            count_params = [strongs_pattern]
            
            if book:
                count_query += " AND v.book_name = %s"
                count_params.append(book)
            
            cur.execute(count_query, count_params)
            total_count = cur.fetchone()["count"]
            
            # Get lexicon entry for this Strong's ID
            lexicon_entry = None
            lexicon_table = "bible.hebrew_entries" if is_hebrew else "bible.greek_entries"
            
            try:
                # For extended Strong's IDs, try both with and without the letter suffix
                base_strongs = re.sub(r'([A-Z])(\d+)[a-zA-Z]?', r'\1\2', strongs_id.upper())
                
                cur.execute(f"""
                    SELECT id, strongs_id, word, transliteration, definition
                    FROM {lexicon_table}
                    WHERE strongs_id = %s OR strongs_id = %s
                    LIMIT 1
                """, [strongs_id.upper(), base_strongs])
                
                lexicon_result = cur.fetchone()
                if lexicon_result:
                    lexicon_entry = lexicon_result
            except Exception as e:
                logger.warning(f"Error fetching lexicon entry: {str(e)}")
        
        conn.close()
        
        # Format the response
        response = {
            "strongs_id": strongs_id,
            "occurrences": occurrences,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        if lexicon_entry:
            response["lexicon_entry"] = lexicon_entry
            
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/tagged_text_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error searching by Strong's ID: {str(e)}")
        return jsonify({"error": str(e)}), 500

@tagged_text_api.route('/concordance', methods=['GET'])
def generate_concordance():
    """Generate a concordance for a Strong's ID"""
    try:
        # Get parameters
        strongs_id = request.args.get('strongs_id', '').strip()
        context_words = request.args.get('context', 5, type=int)
        book = request.args.get('book', None)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not strongs_id:
            return jsonify({"error": "Strong's ID is required"}), 400
        
        # Determine if this is a Hebrew or Greek Strong's number
        is_hebrew = strongs_id.upper().startswith('H')
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Construct base query
            table = "bible.hebrew_ot_words" if is_hebrew else "bible.greek_nt_words"
            verse_join = "bible.verses"
            word_position = "position" if is_hebrew else "word_num"
            strongs_pattern = strongs_id.upper()
            
            # Special handling for extended Strong's IDs with letter suffixes
            if is_hebrew and not re.match(r'^H\d+[a-zA-Z]?$', strongs_pattern):
                strongs_pattern = f"{strongs_pattern}%"
            
            # First get the target words
            target_query = f"""
                SELECT v.id AS verse_id, v.book_name, v.chapter_num, v.verse_num, 
                       w.id AS word_id, w.{word_position} AS position, w.word,
                       w.strongs_id, w.transliteration, w.translation
                FROM {table} w
                JOIN {verse_join} v ON w.verse_id = v.id
                WHERE w.strongs_id LIKE %s
            """
            params = [strongs_pattern]
            
            if book:
                target_query += " AND v.book_name = %s"
                params.append(book)
            
            target_query += " ORDER BY v.book_name, v.chapter_num, v.verse_num"
            target_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(target_query, params)
            target_words = cur.fetchall()
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table} w
                JOIN {verse_join} v ON w.verse_id = v.id
                WHERE w.strongs_id LIKE %s
            """
            count_params = [strongs_pattern]
            
            if book:
                count_query += " AND v.book_name = %s"
                count_params.append(book)
            
            cur.execute(count_query, count_params)
            total_count = cur.fetchone()["count"]
            
            # Now get context words for each target word
            concordance_entries = []
            
            for target in target_words:
                verse_id = target["verse_id"]
                position = target["position"]
                
                # Get context words before and after
                context_query = f"""
                    SELECT w.{word_position} AS position, w.word, w.strongs_id, 
                           w.transliteration, w.translation
                    FROM {table} w
                    WHERE w.verse_id = %s
                      AND w.{word_position} BETWEEN %s AND %s
                    ORDER BY w.{word_position}
                """
                context_params = [
                    verse_id, 
                    max(1, position - context_words), 
                    position + context_words
                ]
                
                cur.execute(context_query, context_params)
                context_words_data = cur.fetchall()
                
                # Add to concordance entries
                entry = {
                    "reference": f"{target['book_name']} {target['chapter_num']}:{target['verse_num']}",
                    "book_name": target["book_name"],
                    "chapter_num": target["chapter_num"],
                    "verse_num": target["verse_num"],
                    "target_word": {
                        "word": target["word"],
                        "strongs_id": target["strongs_id"],
                        "transliteration": target["transliteration"],
                        "translation": target["translation"],
                        "position": target["position"]
                    },
                    "context_words": context_words_data
                }
                
                concordance_entries.append(entry)
            
            # Get lexicon entry for this Strong's ID
            lexicon_entry = None
            lexicon_table = "bible.hebrew_entries" if is_hebrew else "bible.greek_entries"
            
            try:
                # For extended Strong's IDs, try both with and without the letter suffix
                base_strongs = re.sub(r'([A-Z])(\d+)[a-zA-Z]?', r'\1\2', strongs_id.upper())
                
                cur.execute(f"""
                    SELECT id, strongs_id, word, transliteration, definition
                    FROM {lexicon_table}
                    WHERE strongs_id = %s OR strongs_id = %s
                    LIMIT 1
                """, [strongs_id.upper(), base_strongs])
                
                lexicon_result = cur.fetchone()
                if lexicon_result:
                    lexicon_entry = lexicon_result
            except Exception as e:
                logger.warning(f"Error fetching lexicon entry: {str(e)}")
        
        conn.close()
        
        # Format the response
        response = {
            "strongs_id": strongs_id,
            "concordance": concordance_entries,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        if lexicon_entry:
            response["lexicon_entry"] = lexicon_entry
            
        context = f"{request.path} | {request.args.to_dict()}"
        labels = response
        metadata = None
        append_dspy_training_example('data/processed/dspy_training_data/tagged_text_api.jsonl', context, labels, metadata)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating concordance: {str(e)}")
        return jsonify({"error": str(e)}), 500

def is_old_testament(book):
    """Determine if a book is in the Old Testament"""
    ot_books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
        "Ezra", "Nehemiah", "Esther", "Job", "Psalms",
        "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
        "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
        "Micah", "Nahum", "Habakkuk", "Zephaniah",
        "Haggai", "Zechariah", "Malachi"
    ]
    return book in ot_books 