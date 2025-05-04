#!/usr/bin/env python3
"""
REST API for the STEPBible lexicons.
Provides endpoints to query Hebrew and Greek lexicon data.
"""

import os
import logging
from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lexicon_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('lexicon_api')

# Initialize Flask app
app = Flask(__name__)

# Register cross-language API blueprint
from src.api.cross_language_api import api_blueprint as cross_language_api
app.register_blueprint(cross_language_api, url_prefix='/api/cross_language')

# Database connection
def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@app.route('/api/lexicon/stats', methods=['GET'])
def get_lexicon_stats():
    """
    Get statistics about the lexicon data.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get Hebrew entries count
            cur.execute("SELECT COUNT(*) FROM bible.hebrew_entries")
            hebrew_count = cur.fetchone()[0]
            
            # Get Greek entries count
            cur.execute("SELECT COUNT(*) FROM bible.greek_entries")
            greek_count = cur.fetchone()[0]
            
            # Get word relationships count
            cur.execute("SELECT COUNT(*) FROM bible.word_relationships")
            relationships_count = cur.fetchone()[0]
            
            # Get relationship types
            cur.execute("""
                SELECT relationship_type, COUNT(*) 
                FROM bible.word_relationships 
                GROUP BY relationship_type
            """)
            relationship_types = {row[0]: row[1] for row in cur.fetchall()}
            
            # Get tagged words count
            cur.execute("SELECT COUNT(*) FROM bible.greek_nt_words")
            greek_words_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words")
            hebrew_words_count = cur.fetchone()[0]
            
            # Get verse count
            cur.execute("SELECT COUNT(*) FROM bible.verses")
            verse_count = cur.fetchone()[0]
            
            # Get proper names count
            cur.execute("SELECT COUNT(*) FROM bible.proper_names")
            proper_names_count = cur.fetchone()[0]
            
            # Get proper name forms count
            cur.execute("SELECT COUNT(*) FROM bible.proper_name_forms")
            proper_name_forms_count = cur.fetchone()[0]
            
            # Get proper name references count
            cur.execute("SELECT COUNT(*) FROM bible.proper_name_references")
            proper_name_refs_count = cur.fetchone()[0]
            
            return jsonify({
                'hebrew_lexicon': {
                    'count': hebrew_count
                },
                'greek_lexicon': {
                    'count': greek_count
                },
                'word_relationships': {
                    'count': relationships_count,
                    'types': relationship_types
                },
                'tagged_words': {
                    'greek': greek_words_count,
                    'hebrew': hebrew_words_count
                },
                'verses': {
                    'count': verse_count
                },
                'proper_names': {
                    'count': proper_names_count,
                    'forms': proper_name_forms_count,
                    'references': proper_name_refs_count
                }
            })
    except Exception as e:
        logger.error(f"Error getting lexicon stats: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/lexicon/hebrew/<strongs_id>', methods=['GET'])
def get_hebrew_entry(strongs_id):
    """
    Get a Hebrew lexicon entry by Strong's ID.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT strongs_id, extended_strongs, hebrew_word, 
                       transliteration, pos, gloss, definition 
                FROM bible.hebrew_entries 
                WHERE strongs_id = %s
            """, (strongs_id,))
            entry = cur.fetchone()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            # Get related words
            cur.execute("""
                SELECT wr.target_id, wr.relationship_type, ge.greek_word, ge.transliteration, ge.gloss
                FROM bible.word_relationships wr
                JOIN bible.greek_entries ge ON wr.target_id = ge.strongs_id
                WHERE wr.source_id = %s
                UNION
                SELECT wr.target_id, wr.relationship_type, he.hebrew_word, he.transliteration, he.gloss
                FROM bible.word_relationships wr
                JOIN bible.hebrew_entries he ON wr.target_id = he.strongs_id
                WHERE wr.source_id = %s
            """, (strongs_id, strongs_id))
            related_words = [dict(row) for row in cur.fetchall()]
            
            result = dict(entry)
            result['related_words'] = related_words
            
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting Hebrew entry {strongs_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/lexicon/greek/<strongs_id>', methods=['GET'])
def get_greek_entry(strongs_id):
    """
    Get a Greek lexicon entry by Strong's ID.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT strongs_id, extended_strongs, greek_word, 
                       transliteration, pos, gloss, definition 
                FROM bible.greek_entries 
                WHERE strongs_id = %s
            """, (strongs_id,))
            entry = cur.fetchone()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            # Get related words
            cur.execute("""
                SELECT wr.target_id, wr.relationship_type, he.hebrew_word, he.transliteration, he.gloss
                FROM bible.word_relationships wr
                JOIN bible.hebrew_entries he ON wr.target_id = he.strongs_id
                WHERE wr.source_id = %s
                UNION
                SELECT wr.target_id, wr.relationship_type, ge.greek_word, ge.transliteration, ge.gloss
                FROM bible.word_relationships wr
                JOIN bible.greek_entries ge ON wr.target_id = ge.strongs_id
                WHERE wr.source_id = %s
            """, (strongs_id, strongs_id))
            related_words = [dict(row) for row in cur.fetchall()]
            
            result = dict(entry)
            result['related_words'] = related_words
            
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting Greek entry {strongs_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/lexicon/search', methods=['GET'])
def search_lexicon():
    """
    Search the lexicon by keyword.
    """
    query = request.args.get('q', '')
    lang = request.args.get('lang', 'both')  # 'hebrew', 'greek', or 'both'
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        conn = get_db_connection()
        results = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if lang in ('hebrew', 'both'):
                cur.execute("""
                    SELECT 'hebrew' as language, strongs_id, hebrew_word, transliteration, gloss, definition 
                    FROM bible.hebrew_entries 
                    WHERE 
                        to_tsvector('english', gloss || ' ' || coalesce(definition, '')) @@ plainto_tsquery('english', %s)
                        OR hebrew_word ILIKE %s
                        OR transliteration ILIKE %s
                    LIMIT 50
                """, (query, f'%{query}%', f'%{query}%'))
                results.extend([dict(row) for row in cur.fetchall()])
            
            if lang in ('greek', 'both'):
                cur.execute("""
                    SELECT 'greek' as language, strongs_id, greek_word, transliteration, gloss, definition 
                    FROM bible.greek_entries 
                    WHERE 
                        to_tsvector('english', gloss || ' ' || coalesce(definition, '')) @@ plainto_tsquery('english', %s)
                        OR greek_word ILIKE %s
                        OR transliteration ILIKE %s
                    LIMIT 50
                """, (query, f'%{query}%', f'%{query}%'))
                results.extend([dict(row) for row in cur.fetchall()])
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching lexicon for '{query}': {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/tagged/verse', methods=['GET'])
def get_tagged_verse():
    """
    Get a tagged verse (Hebrew or Greek) with word details.
    """
    try:
        book = request.args.get('book', '')
        chapter = request.args.get('chapter', 0, type=int)
        verse = request.args.get('verse', 0, type=int)
        
        if not book or chapter <= 0 or verse <= 0:
            return jsonify({'error': 'Book, chapter, and verse are required parameters'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Check if this is an OT or NT book to determine which tagged text to use
            is_ot_book = False
            is_nt_book = False
            
            # Simple check based on common book categorization
            ot_books = ['Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', 'Rut', '1Sa', '2Sa', '1Ki', '2Ki', 
                        '1Ch', '2Ch', 'Ezr', 'Neh', 'Est', 'Job', 'Psa', 'Pro', 'Ecc', 'Sng', 'Isa', 'Jer', 
                        'Lam', 'Ezk', 'Dan', 'Hos', 'Jol', 'Amo', 'Oba', 'Jon', 'Mic', 'Nam', 'Hab', 'Zep', 
                        'Hag', 'Zec', 'Mal']
            
            nt_books = ['Mat', 'Mrk', 'Luk', 'Jhn', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Php', 'Col', 
                        '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe', '2Pe', '1Jn', '2Jn', 
                        '3Jn', 'Jud', 'Rev']
            
            if book in ot_books:
                is_ot_book = True
            elif book in nt_books:
                is_nt_book = True
            
            if is_ot_book:
                # Use Hebrew OT endpoint
                return get_hebrew_tagged_verse()
            elif is_nt_book:
                # Use existing Greek NT functionality (keep the existing code)
                
                # Get the verse
                cur.execute(
                    """
                    SELECT id, book_name, chapter_num, verse_num, verse_text, translation_source
                    FROM bible.verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                    AND (translation_source = 'TAGNT' OR translation_source IS NULL)
                    """,
                    (book, chapter, verse)
                )
                verse_row = cur.fetchone()
                
                if not verse_row:
                    return jsonify({'error': f'Verse {book} {chapter}:{verse} not found'}), 404
                
                verse_columns = [desc[0] for desc in cur.description]
                verse_data = dict(zip(verse_columns, verse_row))
                
                # Get the tagged words
                cur.execute(
                    """
                    SELECT id, word_num, word_text, strongs_id, grammar_code, transliteration, translation
                    FROM bible.greek_nt_words
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                    ORDER BY word_num
                    """,
                    (book, chapter, verse)
                )
                
                word_columns = [desc[0] for desc in cur.description]
                words = []
                
                for word_row in cur.fetchall():
                    word_data = dict(zip(word_columns, word_row))
                    
                    # If the word has a Strong's ID, get the lexicon entry
                    if word_data['strongs_id']:
                        cur.execute(
                            """
                            SELECT id, strongs_id, lemma, transliteration, definition, short_definition
                            FROM bible.greek_lexicon
                            WHERE strongs_id = %s
                            """,
                            (word_data['strongs_id'],)
                        )
                        
                        lexicon_row = cur.fetchone()
                        if lexicon_row:
                            lexicon_columns = [desc[0] for desc in cur.description]
                            word_data['lexicon'] = dict(zip(lexicon_columns, lexicon_row))
                    
                    # If the word has a grammar code, get the morphology
                    if word_data['grammar_code']:
                        cur.execute(
                            """
                            SELECT code, code_type, description, explanation
                            FROM bible.greek_morphology_codes
                            WHERE code = %s
                            """,
                            (word_data['grammar_code'],)
                        )
                        
                        morph_row = cur.fetchone()
                        if morph_row:
                            morph_columns = [desc[0] for desc in cur.description]
                            word_data['morphology'] = dict(zip(morph_columns, morph_row))
                    
                    words.append(word_data)
                
                verse_data['words'] = words
                
                return jsonify(verse_data)
            else:
                return jsonify({'error': f'Unknown book: {book}'}), 400
    
    except Exception as e:
        logger.error(f"Error getting tagged verse: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/tagged/search', methods=['GET'])
def search_tagged_texts():
    """
    Search the tagged texts by Strong's ID or translation.
    """
    strongs_id = request.args.get('strongs_id', '')
    translation = request.args.get('translation', '')
    language = request.args.get('language', 'both')  # 'hebrew', 'greek', or 'both'
    
    if not strongs_id and not translation:
        return jsonify({'error': 'Either strongs_id or translation parameter is required'}), 400
    
    try:
        conn = get_db_connection()
        results = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if language in ('greek', 'both'):
                query = """
                    SELECT DISTINCT v.book_name, v.chapter_num, v.verse_num, v.verse_text,
                           w.word_text, w.translation, w.strongs_id, 'greek' as language
                    FROM bible.verses v
                    JOIN bible.verse_word_links vwl ON v.id = vwl.verse_id
                    JOIN bible.greek_nt_words w ON vwl.greek_word_id = w.id
                    WHERE 1=1
                """
                params = []
                
                if strongs_id:
                    query += " AND w.strongs_id = %s"
                    params.append(strongs_id)
                
                if translation:
                    query += " AND w.translation ILIKE %s"
                    params.append(f'%{translation}%')
                
                query += " LIMIT 100"
                
                cur.execute(query, params)
                results.extend([dict(row) for row in cur.fetchall()])
            
            if language in ('hebrew', 'both'):
                query = """
                    SELECT DISTINCT v.book_name, v.chapter_num, v.verse_num, v.verse_text,
                           w.word_text, w.translation, w.strongs_id, 'hebrew' as language
                    FROM bible.verses v
                    JOIN bible.verse_word_links vwl ON v.id = vwl.verse_id
                    JOIN bible.hebrew_ot_words w ON vwl.hebrew_word_id = w.id
                    WHERE 1=1
                """
                params = []
                
                if strongs_id:
                    query += " AND w.strongs_id = %s"
                    params.append(strongs_id)
                
                if translation:
                    query += " AND w.translation ILIKE %s"
                    params.append(f'%{translation}%')
                
                query += " LIMIT 100"
                
                cur.execute(query, params)
                results.extend([dict(row) for row in cur.fetchall()])
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching tagged texts: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# Add endpoints for Hebrew morphology codes
@app.route('/api/morphology/hebrew', methods=['GET'])
def get_hebrew_morphology_codes():
    """Get Hebrew morphology codes."""
    try:
        # Get optional filter parameters
        code_filter = request.args.get('code', '')
        type_filter = request.args.get('type', '')
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build query with filters if provided
        query = "SELECT id, code, code_type, description, explanation, example FROM bible.hebrew_morphology_codes WHERE 1=1"
        params = []
        
        if code_filter:
            query += " AND code LIKE %s"
            params.append(f"%{code_filter}%")
        
        if type_filter:
            query += " AND code_type = %s"
            params.append(type_filter)
        
        # Add order by
        query += " ORDER BY code, code_type"
        
        # Execute query
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            codes = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        return jsonify(codes)
    
    except Exception as e:
        logging.error(f"Error getting Hebrew morphology codes: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/morphology/hebrew/<code>', methods=['GET'])
def get_hebrew_morphology_code(code):
    """Get specific Hebrew morphology code."""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Try exact match first
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, code, code_type, description, explanation, example FROM bible.hebrew_morphology_codes WHERE code = %s",
                (code,)
            )
            codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
        
        # If no exact match, try pattern matching
        if not codes:
            with conn.cursor() as cur:
                # Try normalized format (remove spaces, etc.)
                normalized_code = code.strip().replace(' ', '')
                cur.execute(
                    "SELECT id, code, code_type, description, explanation, example FROM bible.hebrew_morphology_codes WHERE REPLACE(code, ' ', '') = %s",
                    (normalized_code,)
                )
                codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
                
                # If still no match, try LIKE match
                if not codes:
                    cur.execute(
                        "SELECT id, code, code_type, description, explanation, example FROM bible.hebrew_morphology_codes WHERE code LIKE %s",
                        (f"%{code}%",)
                    )
                    codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
        
        if not codes:
            return jsonify({'error': f'Morphology code {code} not found'}), 404
        
        return jsonify(codes[0] if len(codes) == 1 else codes)
    
    except Exception as e:
        logging.error(f"Error getting Hebrew morphology code {code}: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

# Add endpoints for Greek morphology codes
@app.route('/api/morphology/greek', methods=['GET'])
def get_greek_morphology_codes():
    """Get Greek morphology codes."""
    try:
        # Get optional filter parameters
        code_filter = request.args.get('code', '')
        type_filter = request.args.get('type', '')
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build query with filters if provided
        query = "SELECT id, code, code_type, description, explanation, example FROM bible.greek_morphology_codes WHERE 1=1"
        params = []
        
        if code_filter:
            query += " AND code LIKE %s"
            params.append(f"%{code_filter}%")
        
        if type_filter:
            query += " AND code_type = %s"
            params.append(type_filter)
        
        # Add order by
        query += " ORDER BY code, code_type"
        
        # Execute query
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            codes = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        return jsonify(codes)
    
    except Exception as e:
        logging.error(f"Error getting Greek morphology codes: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/morphology/greek/<code>', methods=['GET'])
def get_greek_morphology_code(code):
    """Get specific Greek morphology code."""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Try exact match first
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, code, code_type, description, explanation, example FROM bible.greek_morphology_codes WHERE code = %s",
                (code,)
            )
            codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
        
        # If no exact match, try pattern matching
        if not codes:
            with conn.cursor() as cur:
                # Try normalized format (remove spaces, etc.)
                normalized_code = code.strip().replace(' ', '')
                cur.execute(
                    "SELECT id, code, code_type, description, explanation, example FROM bible.greek_morphology_codes WHERE REPLACE(code, ' ', '') = %s",
                    (normalized_code,)
                )
                codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
                
                # If still no match, try LIKE match
                if not codes:
                    cur.execute(
                        "SELECT id, code, code_type, description, explanation, example FROM bible.greek_morphology_codes WHERE code LIKE %s",
                        (f"%{code}%",)
                    )
                    codes = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
        
        if not codes:
            return jsonify({'error': f'Morphology code {code} not found'}), 404
        
        return jsonify(codes[0] if len(codes) == 1 else codes)
    
    except Exception as e:
        logging.error(f"Error getting Greek morphology code {code}: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

# Add endpoints for proper names
@app.route('/api/names', methods=['GET'])
def get_proper_names():
    """Get proper names with optional filtering."""
    try:
        # Get optional filter parameters
        name_filter = request.args.get('name', '')
        type_filter = request.args.get('type', '')
        limit = request.args.get('limit', 100, type=int)
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get total count first (for header)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM bible.proper_names")
            total_count = cur.fetchone()[0]
        
        # Build query with filters if provided
        query = "SELECT id, name, type, gender, description, short_description FROM bible.proper_names WHERE 1=1"
        params = []
        
        if name_filter:
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")
        
        if type_filter:
            query += " AND type = %s"
            params.append(type_filter)
        
        # Add order by and limit
        query += " ORDER BY name LIMIT %s"
        params.append(limit)
        
        # Execute query
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            names = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        # Add the total count to header
        response = jsonify(names)
        response.headers['X-Total-Count'] = str(total_count)
        return response
    
    except Exception as e:
        logging.error(f"Error getting proper names: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/names/<int:name_id>', methods=['GET'])
def get_proper_name(name_id):
    """Get a specific proper name with all details including forms, references, and relationships."""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get the name details
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, type, gender, description, short_description 
                FROM bible.proper_names 
                WHERE id = %s
                """,
                (name_id,)
            )
            result = cur.fetchone()
            
            if not result:
                return jsonify({'error': f'Proper name with id {name_id} not found'}), 404
            
            columns = [desc[0] for desc in cur.description]
            name_data = dict(zip(columns, result))
            
            # Get forms
            cur.execute(
                """
                SELECT id, language, form, transliteration, strongs_id
                FROM bible.proper_name_forms
                WHERE proper_name_id = %s
                ORDER BY language, form
                """,
                (name_id,)
            )
            form_columns = [desc[0] for desc in cur.description]
            forms = [dict(zip(form_columns, row)) for row in cur.fetchall()]
            
            # For each form, get references
            for form in forms:
                cur.execute(
                    """
                    SELECT reference, context
                    FROM bible.proper_name_references
                    WHERE proper_name_form_id = %s
                    ORDER BY reference
                    """,
                    (form['id'],)
                )
                ref_columns = [desc[0] for desc in cur.description]
                form['references'] = [dict(zip(ref_columns, row)) for row in cur.fetchall()]
            
            # Get relationships
            cur.execute(
                """
                SELECT r.relationship_type, 
                       p.id as related_id, 
                       p.name as related_name, 
                       p.type as related_type,
                       p.gender as related_gender
                FROM bible.proper_name_relationships r
                JOIN bible.proper_names p ON r.target_name_id = p.id
                WHERE r.source_name_id = %s
                """,
                (name_id,)
            )
            rel_columns = [desc[0] for desc in cur.description]
            relationships = [dict(zip(rel_columns, row)) for row in cur.fetchall()]
            
            # Add to result
            name_data['forms'] = forms
            name_data['relationships'] = relationships
            
            return jsonify(name_data)
    
    except Exception as e:
        logging.error(f"Error getting proper name {name_id}: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/names/search', methods=['GET'])
def search_proper_names():
    """Search proper names by name or references."""
    try:
        # Get search parameters
        search_term = request.args.get('q', '')
        search_type = request.args.get('type', 'name')  # 'name', 'reference', 'strongs'
        name_type = request.args.get('name_type', '')   # 'Person', 'Location', etc.
        gender = request.args.get('gender', '')         # 'Male', 'Female'
        book = request.args.get('book', '')             # Filter by book code
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not search_term and not name_type and not gender and not book:
            return jsonify({'error': 'At least one search filter is required'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get total count for pagination (based on filters)
        total_count = 0
        
        with conn.cursor() as cur:
            # Build the base query
            if search_type == 'name':
                # Search by name
                query = """
                SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description
                FROM bible.proper_names n
                WHERE 1=1
                """
                params = []
                
                if search_term:
                    query += " AND n.name ILIKE %s"
                    params.append(f"%{search_term}%")
                
                if name_type:
                    query += " AND n.type = %s"
                    params.append(name_type)
                    
                if gender:
                    query += " AND n.gender = %s"
                    params.append(gender)
                
                # If filtering by book, join with forms and references
                if book:
                    query = """
                    SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description
                    FROM bible.proper_names n
                    JOIN bible.proper_name_forms f ON n.id = f.proper_name_id
                    JOIN bible.proper_name_references r ON f.id = r.proper_name_form_id
                    WHERE 1=1
                    """
                    
                    if search_term:
                        query += " AND n.name ILIKE %s"
                        params.append(f"%{search_term}%")
                    
                    if name_type:
                        query += " AND n.type = %s"
                        params.append(name_type)
                        
                    if gender:
                        query += " AND n.gender = %s"
                        params.append(gender)
                    
                    query += " AND r.reference LIKE %s"
                    params.append(f"{book}%")
                
                # Get total count for pagination
                count_query = query.replace("SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description", 
                                           "SELECT COUNT(DISTINCT n.id)")
                cur.execute(count_query, params)
                total_count = cur.fetchone()[0]
                
                # Add order and pagination 
                query += " ORDER BY n.name LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                
            elif search_type == 'reference':
                # Search by Bible reference
                query = """
                SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description
                FROM bible.proper_names n
                JOIN bible.proper_name_forms f ON n.id = f.proper_name_id
                JOIN bible.proper_name_references r ON f.id = r.proper_name_form_id
                WHERE r.reference LIKE %s
                """
                params = [f"%{search_term}%"]
                
                if name_type:
                    query += " AND n.type = %s"
                    params.append(name_type)
                    
                if gender:
                    query += " AND n.gender = %s"
                    params.append(gender)
                
                if book and book != search_term:
                    query += " AND r.reference LIKE %s"
                    params.append(f"{book}%")
                
                # Get total count for pagination
                count_query = query.replace("SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description", 
                                           "SELECT COUNT(DISTINCT n.id)")
                cur.execute(count_query, params)
                total_count = cur.fetchone()[0]
                
                # Add order and pagination
                query += " ORDER BY n.name LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                
            elif search_type == 'strongs':
                # Search by Strong's ID
                query = """
                SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description
                FROM bible.proper_names n
                JOIN bible.proper_name_forms f ON n.id = f.proper_name_id
                WHERE f.strongs_id = %s
                """
                params = [search_term]
                
                if name_type:
                    query += " AND n.type = %s"
                    params.append(name_type)
                    
                if gender:
                    query += " AND n.gender = %s"
                    params.append(gender)
                
                if book:
                    query += """ 
                    AND EXISTS (
                        SELECT 1 FROM bible.proper_name_references r 
                        WHERE r.proper_name_form_id = f.id AND r.reference LIKE %s
                    )
                    """
                    params.append(f"{book}%")
                
                # Get total count for pagination
                count_query = query.replace("SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description", 
                                           "SELECT COUNT(DISTINCT n.id)")
                cur.execute(count_query, params)
                total_count = cur.fetchone()[0]
                
                # Add order and pagination
                query += " ORDER BY n.name LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
            
            else:
                return jsonify({'error': f'Invalid search type: {search_type}'}), 400
            
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            # Add metadata
            response = jsonify({
                'results': results,
                'metadata': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'filters': {
                        'search_term': search_term,
                        'search_type': search_type,
                        'name_type': name_type,
                        'gender': gender,
                        'book': book
                    }
                }
            })
            
            return response
    
    except Exception as e:
        logging.error(f"Error searching proper names: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

# Add endpoint for Hebrew OT tagged verse
@app.route('/api/tagged/hebrew/verse', methods=['GET'])
def get_hebrew_tagged_verse():
    """Get a tagged Hebrew OT verse with word details."""
    try:
        book = request.args.get('book', '')
        chapter = request.args.get('chapter', 0, type=int)
        verse = request.args.get('verse', 0, type=int)
        
        if not book or chapter <= 0 or verse <= 0:
            return jsonify({'error': 'Book, chapter, and verse are required parameters'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Get the verse
            cur.execute(
                """
                SELECT id, book_name, chapter_num, verse_num, verse_text, translation_source
                FROM bible.verses
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = 'TAHOT'
                """,
                (book, chapter, verse)
            )
            verse_row = cur.fetchone()
            
            if not verse_row:
                return jsonify({'error': f'Verse {book} {chapter}:{verse} not found in Hebrew OT'}), 404
            
            verse_columns = [desc[0] for desc in cur.description]
            verse_data = dict(zip(verse_columns, verse_row))
            
            # Get the tagged words
            cur.execute(
                """
                SELECT id, word_num, word_text, strongs_id, grammar_code, transliteration, translation
                FROM bible.hebrew_ot_words
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                ORDER BY word_num
                """,
                (book, chapter, verse)
            )
            
            word_columns = [desc[0] for desc in cur.description]
            words = []
            
            for word_row in cur.fetchall():
                word_data = dict(zip(word_columns, word_row))
                
                # If the word has a Strong's ID, get the lexicon entry
                if word_data['strongs_id']:
                    cur.execute(
                        """
                        SELECT id, strongs_id, lemma, transliteration, pronunciation, definition, short_definition
                        FROM bible.hebrew_lexicon
                        WHERE strongs_id = %s
                        """,
                        (word_data['strongs_id'],)
                    )
                    
                    lexicon_row = cur.fetchone()
                    if lexicon_row:
                        lexicon_columns = [desc[0] for desc in cur.description]
                        word_data['lexicon'] = dict(zip(lexicon_columns, lexicon_row))
                
                # If the word has a grammar code, get the morphology
                if word_data['grammar_code']:
                    cur.execute(
                        """
                        SELECT code, code_type, description, explanation
                        FROM bible.hebrew_morphology_codes
                        WHERE code = %s
                        """,
                        (word_data['grammar_code'],)
                    )
                    
                    morph_row = cur.fetchone()
                    if morph_row:
                        morph_columns = [desc[0] for desc in cur.description]
                        word_data['morphology'] = dict(zip(morph_columns, morph_row))
                
                words.append(word_data)
            
            verse_data['words'] = words
            
            return jsonify(verse_data)
    
    except Exception as e:
        logging.error(f"Error getting Hebrew tagged verse: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/names/types', methods=['GET'])
def get_proper_name_types():
    """Get distinct types and genders of proper names for filters."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Get distinct types
            cur.execute("SELECT DISTINCT type FROM bible.proper_names ORDER BY type")
            types = [row[0] for row in cur.fetchall()]
            
            # Get distinct genders
            cur.execute("SELECT DISTINCT gender FROM bible.proper_names WHERE gender IS NOT NULL ORDER BY gender")
            genders = [row[0] for row in cur.fetchall()]
            
            # Get book references count
            cur.execute("""
                SELECT SUBSTRING(reference FROM 1 FOR POSITION('.' IN reference) - 1) as book,
                       COUNT(DISTINCT proper_name_form_id) as name_count
                FROM bible.proper_name_references
                GROUP BY book
                ORDER BY book
            """)
            book_counts = {row[0]: row[1] for row in cur.fetchall()}
            
            return jsonify({
                'types': types,
                'genders': genders,
                'book_counts': book_counts
            })
    
    except Exception as e:
        logging.error(f"Error getting proper name types: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/api/verse/names', methods=['GET'])
def get_verse_names():
    """Get proper names mentioned in a specific Bible verse."""
    try:
        # Get verse reference parameters
        book = request.args.get('book', '')
        chapter = request.args.get('chapter', 0, type=int)
        verse = request.args.get('verse', 0, type=int)
        
        if not book or chapter <= 0 or verse <= 0:
            return jsonify({'error': 'Book, chapter, and verse are required parameters'}), 400
        
        # Format the reference pattern
        reference = f"{book}.{chapter}:{verse}"
        reference_pattern = f"{book}.{chapter}:%"  # Get all names in this chapter
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        names = []
        
        with conn.cursor() as cur:
            # Find names referenced in this verse
            cur.execute("""
                SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description,
                       r.reference, f.language, f.form, f.transliteration
                FROM bible.proper_names n
                JOIN bible.proper_name_forms f ON n.id = f.proper_name_id
                JOIN bible.proper_name_references r ON f.id = r.proper_name_form_id
                WHERE r.reference = %s
                ORDER BY n.name
            """, (reference,))
            
            exact_names = []
            columns = [desc[0] for desc in cur.description]
            
            for row in cur.fetchall():
                name_data = dict(zip(columns, row))
                exact_names.append(name_data)
            
            # If no exact matches, look for names in the same chapter
            if not exact_names:
                cur.execute("""
                    SELECT DISTINCT n.id, n.name, n.type, n.gender, n.short_description,
                           r.reference, f.language, f.form, f.transliteration
                    FROM bible.proper_names n
                    JOIN bible.proper_name_forms f ON n.id = f.proper_name_id
                    JOIN bible.proper_name_references r ON f.id = r.proper_name_form_id
                    WHERE r.reference LIKE %s
                    ORDER BY n.name
                    LIMIT 10
                """, (reference_pattern,))
                
                for row in cur.fetchall():
                    name_data = dict(zip(columns, row))
                    names.append(name_data)
            else:
                # Return exact matches if found
                names = exact_names
            
            return jsonify({
                'reference': reference,
                'names': names,
                'exact_match': len(exact_names) > 0
            })
    
    except Exception as e:
        logging.error(f"Error getting verse names: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()

# Arabic Bible API Endpoints
@app.route('/api/arabic/stats', methods=['GET'])
def get_arabic_bible_stats():
    """Get statistics about the Arabic Bible data."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Get book stats
            cur.execute("""
                SELECT book_name, COUNT(*) as verse_count 
                FROM bible.arabic_verses 
                GROUP BY book_name 
                ORDER BY book_name
            """)
            
            books = []
            for row in cur.fetchall():
                books.append({
                    'book_name': row[0],
                    'verse_count': row[1]
                })
            
            # Get total counts
            cur.execute("SELECT COUNT(*) FROM bible.arabic_verses")
            total_verses = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM bible.arabic_words")
            total_words = cur.fetchone()[0]
            
            return jsonify({
                'total_verses': total_verses,
                'total_words': total_words,
                'books': books
            })
            
    except Exception as e:
        logging.error(f"Error getting Arabic Bible stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arabic/verse', methods=['GET'])
def get_arabic_verse():
    """Get an Arabic verse by reference with its tagged words."""
    try:
        book = request.args.get('book', '')
        chapter = request.args.get('chapter', 0, type=int)
        verse = request.args.get('verse', 0, type=int)
        
        if not book or chapter <= 0 or verse <= 0:
            return jsonify({'error': 'Book, chapter, and verse are required parameters'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Get the verse
            cur.execute("""
                SELECT id, book_name, chapter_num, verse_num, verse_text, translation_source
                FROM bible.arabic_verses
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
            """, (book, chapter, verse))
            
            verse_row = cur.fetchone()
            if not verse_row:
                return jsonify({'error': f'Verse {book} {chapter}:{verse} not found in Arabic Bible'}), 404
            
            verse_columns = [desc[0] for desc in cur.description]
            verse_data = dict(zip(verse_columns, verse_row))
            
            # Get the tagged words
            cur.execute("""
                SELECT id, word_position, arabic_word, strongs_id, latin_word, 
                       greek_word, transliteration, gloss, morphology
                FROM bible.arabic_words
                WHERE verse_id = %s
                ORDER BY word_position
            """, (verse_data['id'],))
            
            word_columns = [desc[0] for desc in cur.description]
            words = []
            
            for word_row in cur.fetchall():
                word_data = dict(zip(word_columns, word_row))
                
                # If the word has a Strong's ID, get the Greek lexicon entry
                if word_data['strongs_id'] and word_data['strongs_id'].startswith('G'):
                    cur.execute("""
                        SELECT id, strongs_id, lemma, transliteration, short_definition, definition
                        FROM bible.greek_entries
                        WHERE strongs_id = %s
                    """, (word_data['strongs_id'],))
                    
                    lexicon_row = cur.fetchone()
                    if lexicon_row:
                        lexicon_columns = [desc[0] for desc in cur.description]
                        word_data['lexicon'] = dict(zip(lexicon_columns, lexicon_row))
                
                # If the word has a morphology code, get the details
                if word_data['morphology']:
                    cur.execute("""
                        SELECT code, code_type, description, explanation
                        FROM bible.greek_morphology_codes
                        WHERE code = %s
                    """, (word_data['morphology'],))
                    
                    morph_row = cur.fetchone()
                    if morph_row:
                        morph_columns = [desc[0] for desc in cur.description]
                        word_data['morphology_details'] = dict(zip(morph_columns, morph_row))
                
                words.append(word_data)
            
            verse_data['words'] = words
            
            return jsonify(verse_data)
    
    except Exception as e:
        logging.error(f"Error getting Arabic verse: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arabic/search', methods=['GET'])
def search_arabic_bible():
    """Search for occurrences of text in the Arabic Bible."""
    try:
        query = request.args.get('q', '')
        book = request.args.get('book', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Build query with optional book filter
            sql_query = """
                SELECT id, book_name, chapter_num, verse_num, verse_text
                FROM bible.arabic_verses
                WHERE verse_text LIKE %s
            """
            params = [f'%{query}%']
            
            if book:
                sql_query += " AND book_name = %s"
                params.append(book)
                
            sql_query += " ORDER BY book_name, chapter_num, verse_num LIMIT %s"
            params.append(limit)
            
            cur.execute(sql_query, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'book_name': row[1],
                    'chapter_num': row[2],
                    'verse_num': row[3],
                    'verse_text': row[4]
                })
            
            return jsonify({
                'query': query,
                'count': len(results),
                'results': results
            })
    
    except Exception as e:
        logging.error(f"Error searching Arabic Bible: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arabic/parallel', methods=['GET'])
def get_parallel_verse():
    """Get a verse in both Arabic and Greek for parallel viewing."""
    try:
        book = request.args.get('book', '')
        chapter = request.args.get('chapter', 0, type=int)
        verse = request.args.get('verse', 0, type=int)
        
        if not book or chapter <= 0 or verse <= 0:
            return jsonify({'error': 'Book, chapter, and verse are required parameters'}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with conn.cursor() as cur:
            # Get the Arabic verse
            cur.execute("""
                SELECT id, book_name, chapter_num, verse_num, verse_text
                FROM bible.arabic_verses
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
            """, (book, chapter, verse))
            
            arabic_row = cur.fetchone()
            if not arabic_row:
                return jsonify({'error': f'Verse {book} {chapter}:{verse} not found in Arabic Bible'}), 404
            
            arabic_verse = {
                'id': arabic_row[0],
                'book_name': arabic_row[1],
                'chapter_num': arabic_row[2],
                'verse_num': arabic_row[3],
                'verse_text': arabic_row[4]
            }
            
            # Get the Greek verse (if it's a NT book)
            greek_verse = None
            if book in [
                'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians',
                'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
                '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter',
                '1 John', '2 John', '3 John', 'Jude', 'Revelation'
            ]:
                cur.execute("""
                    SELECT id, book_name, chapter_num, verse_num, verse_text
                    FROM bible.verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = 'TAGNT'
                """, (book, chapter, verse))
                
                greek_row = cur.fetchone()
                if greek_row:
                    greek_verse = {
                        'id': greek_row[0],
                        'book_name': greek_row[1],
                        'chapter_num': greek_row[2],
                        'verse_num': greek_row[3],
                        'verse_text': greek_row[4]
                    }
            
            # Get the Hebrew verse (if it's an OT book)
            hebrew_verse = None
            if book in [
                'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth',
                '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
                'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
                'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
                'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
            ]:
                cur.execute("""
                    SELECT id, book_name, chapter_num, verse_num, verse_text
                    FROM bible.verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = 'TAHOT'
                """, (book, chapter, verse))
                
                hebrew_row = cur.fetchone()
                if hebrew_row:
                    hebrew_verse = {
                        'id': hebrew_row[0],
                        'book_name': hebrew_row[1],
                        'chapter_num': hebrew_row[2],
                        'verse_num': hebrew_row[3],
                        'verse_text': hebrew_row[4]
                    }
            
            return jsonify({
                'arabic': arabic_verse,
                'greek': greek_verse,
                'hebrew': hebrew_verse
            })
    
    except Exception as e:
        logging.error(f"Error getting parallel verse: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/concordance/<strongs_id>', methods=['GET'])
def generate_concordance(strongs_id):
    """
    Generate a concordance for a specific Strong's number.
    Returns all occurrences of a word with context.
    """
    limit = request.args.get('limit', 50, type=int)
    context_size = request.args.get('context', 3, type=int)  # Words before/after
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            is_hebrew = strongs_id.startswith('H')
            is_greek = strongs_id.startswith('G')
            
            if not (is_hebrew or is_greek):
                return jsonify({'error': 'Invalid Strong\'s number format'}), 400
            
            results = []
            
            if is_hebrew:
                # Get Hebrew word occurrences
                cur.execute("""
                    SELECT w.id, w.word_text, w.strongs_id, w.grammar_code, 
                           v.book_name, v.chapter_num, v.verse_num, v.verse_text
                    FROM bible.hebrew_ot_words w
                    JOIN bible.verses v ON w.book_name = v.book_name AND w.chapter_num = v.chapter_num AND w.verse_num = v.verse_num
                    WHERE w.strongs_id = %s
                    LIMIT %s
                """, (strongs_id, limit))
                
                occurrences = cur.fetchall()
                
                for occ in occurrences:
                    # Get surrounding words for context
                    cur.execute("""
                        SELECT word_text, strongs_id, word_num
                        FROM bible.hebrew_ot_words
                        WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                        ORDER BY word_num
                    """, (occ['book_name'], occ['chapter_num'], occ['verse_num']))
                    
                    all_words = cur.fetchall()
                    target_pos = next((i for i, w in enumerate(all_words) if w['strongs_id'] == strongs_id), 0)
                    
                    # Calculate context window
                    start_pos = max(0, target_pos - context_size)
                    end_pos = min(len(all_words), target_pos + context_size + 1)
                    
                    before_words = [dict(w) for w in all_words[start_pos:target_pos]]
                    after_words = [dict(w) for w in all_words[target_pos+1:end_pos]]
                    
                    results.append({
                        'reference': f"{occ['book_name']} {occ['chapter_num']}:{occ['verse_num']}",
                        'verse_text': occ['verse_text'],
                        'target_word': {
                            'text': occ['word_text'],
                            'strongs_id': occ['strongs_id'],
                            'grammar_code': occ['grammar_code']
                        },
                        'context': {
                            'before': before_words,
                            'after': after_words
                        }
                    })
                    
            elif is_greek:
                # Get Greek word occurrences
                cur.execute("""
                    SELECT w.id, w.word_text, w.strongs_id, w.grammar_code, 
                           v.book_name, v.chapter_num, v.verse_num, v.verse_text
                    FROM bible.greek_nt_words w
                    JOIN bible.verses v ON w.book_name = v.book_name AND w.chapter_num = v.chapter_num AND w.verse_num = v.verse_num
                    WHERE w.strongs_id = %s
                    LIMIT %s
                """, (strongs_id, limit))
                
                occurrences = cur.fetchall()
                
                for occ in occurrences:
                    # Get surrounding words for context
                    cur.execute("""
                        SELECT word_text, strongs_id, word_num
                        FROM bible.greek_nt_words
                        WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                        ORDER BY word_num
                    """, (occ['book_name'], occ['chapter_num'], occ['verse_num']))
                    
                    all_words = cur.fetchall()
                    target_pos = next((i for i, w in enumerate(all_words) if w['strongs_id'] == strongs_id), 0)
                    
                    # Calculate context window
                    start_pos = max(0, target_pos - context_size)
                    end_pos = min(len(all_words), target_pos + context_size + 1)
                    
                    before_words = [dict(w) for w in all_words[start_pos:target_pos]]
                    after_words = [dict(w) for w in all_words[target_pos+1:end_pos]]
                    
                    results.append({
                        'reference': f"{occ['book_name']} {occ['chapter_num']}:{occ['verse_num']}",
                        'verse_text': occ['verse_text'],
                        'target_word': {
                            'text': occ['word_text'],
                            'strongs_id': occ['strongs_id'],
                            'grammar_code': occ['grammar_code']
                        },
                        'context': {
                            'before': before_words,
                            'after': after_words
                        }
                    })
            
            # Get lexicon information about this word
            if is_hebrew:
                cur.execute("""
                    SELECT strongs_id, hebrew_word, transliteration, pos, gloss, definition
                    FROM bible.hebrew_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
            else:  # Greek
                cur.execute("""
                    SELECT strongs_id, greek_word, transliteration, pos, gloss, definition
                    FROM bible.greek_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
                
            lexicon_entry = cur.fetchone()
            
            return jsonify({
                'strongs_id': strongs_id,
                'lexicon_entry': dict(lexicon_entry) if lexicon_entry else None,
                'occurrences': results,
                'total': len(results)
            })
            
    except Exception as e:
        logger.error(f"Error generating concordance for {strongs_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/concordance/arabic/<strongs_id>', methods=['GET'])
def generate_arabic_concordance(strongs_id):
    """
    Generate a concordance for Arabic words that correspond to a specific Strong's number.
    """
    limit = request.args.get('limit', 50, type=int)
    context_size = request.args.get('context', 3, type=int)  # Words before/after
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Check if valid Strong's number
            is_hebrew = strongs_id.startswith('H')
            is_greek = strongs_id.startswith('G')
            
            if not (is_hebrew or is_greek):
                return jsonify({'error': 'Invalid Strong\'s number format'}), 400
            
            results = []
            
            # First, check if there are any matches for this Strong's number
            cur.execute("SELECT COUNT(*) FROM bible.arabic_words WHERE strongs_id = %s", (strongs_id,))
            count = cur.fetchone()[0]
            
            if count == 0:
                # No matches, return empty result
                return jsonify({
                    'strongs_id': strongs_id,
                    'lexicon_entry': None,
                    'occurrences': [],
                    'total': 0,
                    'language': 'arabic'
                })
            
            # Get Arabic word occurrences
            cur.execute("""
                SELECT w.id, w.arabic_word, w.strongs_id, w.word_position, w.morphology,
                       v.id as verse_id, v.book_name, v.chapter_num, v.verse_num, v.verse_text
                FROM bible.arabic_words w
                JOIN bible.arabic_verses v ON w.verse_id = v.id
                WHERE w.strongs_id = %s
                LIMIT %s
            """, (strongs_id, limit))
            
            occurrences = cur.fetchall()
            logger.info(f"Found {len(occurrences)} occurrences for {strongs_id}")
            
            for occ in occurrences:
                # Include verse_id in the logging for debugging
                logger.info(f"Processing occurrence in {occ['book_name']} {occ['chapter_num']}:{occ['verse_num']}, verse_id={occ['verse_id']}")
                
                # Get surrounding words for context
                cur.execute("""
                    SELECT arabic_word, strongs_id, word_position
                    FROM bible.arabic_words
                    WHERE verse_id = %s
                    ORDER BY word_position
                """, (occ['verse_id'],))
                
                all_words = cur.fetchall()
                logger.info(f"Found {len(all_words)} words in verse")
                
                # Find the target position, accounting for multiple occurrences of the same Strong's number
                target_word_pos = occ['word_position']
                target_pos = next((i for i, w in enumerate(all_words) if w['word_position'] == target_word_pos), 0)
                
                logger.info(f"Target word position: {target_word_pos}, index in all_words: {target_pos}")
                
                # Calculate context window
                start_pos = max(0, target_pos - context_size)
                end_pos = min(len(all_words), target_pos + context_size + 1)
                
                before_words = [dict(w) for w in all_words[start_pos:target_pos]]
                after_words = [dict(w) for w in all_words[target_pos+1:end_pos]]
                
                results.append({
                    'reference': f"{occ['book_name']} {occ['chapter_num']}:{occ['verse_num']}",
                    'verse_text': occ['verse_text'],
                    'target_word': {
                        'text': occ['arabic_word'],
                        'strongs_id': occ['strongs_id'],
                        'morphology': occ['morphology'],
                        'position': occ['word_position']
                    },
                    'context': {
                        'before': before_words,
                        'after': after_words
                    }
                })
            
            # Get lexicon information about this word (either Hebrew or Greek)
            if is_hebrew:
                cur.execute("""
                    SELECT strongs_id, hebrew_word, transliteration, pos, gloss, definition
                    FROM bible.hebrew_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
            else:  # Greek
                cur.execute("""
                    SELECT strongs_id, greek_word, transliteration, pos, gloss, definition
                    FROM bible.greek_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
                
            lexicon_entry = cur.fetchone()
            
            return jsonify({
                'strongs_id': strongs_id,
                'lexicon_entry': dict(lexicon_entry) if lexicon_entry else None,
                'occurrences': results,
                'total': len(results),
                'language': 'arabic'
            })
            
    except Exception as e:
        logger.error(f"Error generating Arabic concordance for {strongs_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/cross-references', methods=['GET'])
def get_cross_references():
    """
    Get cross-references for a specific verse.
    Identifies related passages based on thematic connections, 
    parallel passages, and shared content.
    """
    book = request.args.get('book')
    chapter = request.args.get('chapter', type=int)
    verse = request.args.get('verse', type=int)
    
    if not (book and chapter and verse):
        return jsonify({'error': 'Book, chapter, and verse are required'}), 400
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get the current verse text
            cur.execute("""
                SELECT id, verse_text, translation_source
                FROM bible.verses
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                LIMIT 1
            """, (book, chapter, verse))
            
            current_verse = cur.fetchone()
            if not current_verse:
                return jsonify({'error': 'Verse not found'}), 404
            
            verse_id = current_verse['id']
            cross_references = []
            
            # Method 1: Find verses with similar word usage (shared content)
            # Get the Strong's numbers used in this verse
            if book in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
                      'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
                      '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
                      'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms',
                      'Proverbs', 'Ecclesiastes', 'Song of Solomon',
                      'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel',
                      'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah',
                      'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
                      'Haggai', 'Zechariah', 'Malachi']:
                # Old Testament - Hebrew
                cur.execute("""
                    SELECT DISTINCT strongs_id 
                    FROM bible.hebrew_ot_words
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                """, (book, chapter, verse))
            else:
                # New Testament - Greek
                cur.execute("""
                    SELECT DISTINCT strongs_id 
                    FROM bible.greek_nt_words
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                """, (book, chapter, verse))
                
            strongs_ids = [row['strongs_id'] for row in cur.fetchall()]
            
            if strongs_ids:
                # Find other verses that use at least 2 of these Strong's numbers
                if book in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
                          'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
                          '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
                          'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms',
                          'Proverbs', 'Ecclesiastes', 'Song of Solomon',
                          'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel',
                          'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah',
                          'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
                          'Haggai', 'Zechariah', 'Malachi']:
                    # Old Testament - Hebrew
                    placeholders = ','.join(['%s'] * len(strongs_ids))
                    # Exclude the current verse
                    cur.execute(f"""
                        SELECT v.book_name, v.chapter_num, v.verse_num, v.verse_text, 
                               COUNT(DISTINCT w.strongs_id) as shared_words
                        FROM bible.hebrew_ot_words w
                        JOIN bible.verses v 
                            ON w.book_name = v.book_name 
                            AND w.chapter_num = v.chapter_num 
                            AND w.verse_num = v.verse_num
                        WHERE w.strongs_id IN ({placeholders})
                        AND NOT (w.book_name = %s AND w.chapter_num = %s AND w.verse_num = %s)
                        GROUP BY v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text
                        HAVING COUNT(DISTINCT w.strongs_id) >= 2
                        ORDER BY shared_words DESC
                        LIMIT 10
                    """, strongs_ids + [book, chapter, verse])
                else:
                    # New Testament - Greek
                    placeholders = ','.join(['%s'] * len(strongs_ids))
                    cur.execute(f"""
                        SELECT v.book_name, v.chapter_num, v.verse_num, v.verse_text, 
                               COUNT(DISTINCT w.strongs_id) as shared_words
                        FROM bible.greek_nt_words w
                        JOIN bible.verses v 
                            ON w.book_name = v.book_name 
                            AND w.chapter_num = v.chapter_num 
                            AND w.verse_num = v.verse_num
                        WHERE w.strongs_id IN ({placeholders})
                        AND NOT (w.book_name = %s AND w.chapter_num = %s AND w.verse_num = %s)
                        GROUP BY v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text
                        HAVING COUNT(DISTINCT w.strongs_id) >= 2
                        ORDER BY shared_words DESC
                        LIMIT 10
                    """, strongs_ids + [book, chapter, verse])
                
                shared_word_refs = cur.fetchall()
                for ref in shared_word_refs:
                    cross_references.append({
                        'reference': f"{ref['book_name']} {ref['chapter_num']}:{ref['verse_num']}",
                        'text': ref['verse_text'],
                        'shared_words': ref['shared_words'],
                        'type': 'shared_content'
                    })
            
            # Method 2: Known parallel passages (e.g., synoptic gospels)
            # This would normally use a predefined table of parallel passages
            # For this example, we'll use a simplistic approach for the Gospels
            if book in ['Matthew', 'Mark', 'Luke', 'John']:
                parallel_mappings = {
                    # The Sermon on the Mount
                    ('Matthew', 5): [('Luke', 6)],
                    ('Matthew', 6): [('Luke', 11)],
                    ('Matthew', 7): [('Luke', 11), ('Luke', 13)],
                    
                    # The Lord's Prayer
                    ('Matthew', 6, 9): [('Luke', 11, 2)],
                    ('Matthew', 6, 10): [('Luke', 11, 2)],
                    ('Matthew', 6, 11): [('Luke', 11, 3)],
                    ('Matthew', 6, 12): [('Luke', 11, 4)],
                    ('Matthew', 6, 13): [('Luke', 11, 4)],
                    
                    # Feeding the 5000
                    ('Matthew', 14, 13): [('Mark', 6, 30), ('Luke', 9, 10), ('John', 6, 1)],
                    ('Matthew', 14, 14): [('Mark', 6, 34), ('Luke', 9, 11), ('John', 6, 2)],
                    ('Matthew', 14, 15): [('Mark', 6, 35), ('Luke', 9, 12), ('John', 6, 5)],
                    ('Matthew', 14, 16): [('Mark', 6, 37), ('Luke', 9, 13), ('John', 6, 6)],
                    ('Matthew', 14, 17): [('Mark', 6, 38), ('Luke', 9, 13), ('John', 6, 9)],
                    ('Matthew', 14, 18): [('Mark', 6, 39), ('Luke', 9, 14), ('John', 6, 10)],
                    ('Matthew', 14, 19): [('Mark', 6, 41), ('Luke', 9, 16), ('John', 6, 11)],
                    ('Matthew', 14, 20): [('Mark', 6, 42), ('Luke', 9, 17), ('John', 6, 12)],
                    ('Matthew', 14, 21): [('Mark', 6, 44), ('Luke', 9, 14), ('John', 6, 10)],
                    
                    # Jesus walks on water
                    ('Matthew', 14, 22): [('Mark', 6, 45), ('John', 6, 16)],
                    ('Matthew', 14, 23): [('Mark', 6, 46), ('John', 6, 15)],
                    ('Matthew', 14, 24): [('Mark', 6, 47), ('John', 6, 18)],
                    ('Matthew', 14, 25): [('Mark', 6, 48), ('John', 6, 19)],
                    ('Matthew', 14, 26): [('Mark', 6, 49), ('John', 6, 19)],
                    ('Matthew', 14, 27): [('Mark', 6, 50), ('John', 6, 20)],
                    
                    # Passion narrative parallels
                    ('Matthew', 26, 26): [('Mark', 14, 22), ('Luke', 22, 19)],
                    ('Matthew', 26, 27): [('Mark', 14, 23), ('Luke', 22, 20)],
                    ('Matthew', 26, 28): [('Mark', 14, 24), ('Luke', 22, 20)],
                    
                    # Crucifixion parallels
                    ('Matthew', 27, 35): [('Mark', 15, 24), ('Luke', 23, 33), ('John', 19, 18)],
                    ('Matthew', 27, 36): [('Mark', 15, 25), ('Luke', 23, 34), ('John', 19, 19)],
                    ('Matthew', 27, 37): [('Mark', 15, 26), ('Luke', 23, 38), ('John', 19, 19)],
                    
                    # More parallels could be added...
                }
                
                # Check various keys to find parallels at different specificity levels
                for key in [(book, chapter, verse), (book, chapter)]:
                    if key in parallel_mappings:
                        for parallel in parallel_mappings[key]:
                            p_book, p_chapter = parallel[0], parallel[1]
                            p_verse = parallel[2] if len(parallel) > 2 else None
                            
                            if p_verse:
                                cur.execute("""
                                    SELECT book_name, chapter_num, verse_num, verse_text
                                    FROM bible.verses
                                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                                """, (p_book, p_chapter, p_verse))
                            else:
                                # If no specific verse, get the whole chapter
                                cur.execute("""
                                    SELECT book_name, chapter_num, verse_num, verse_text
                                    FROM bible.verses
                                    WHERE book_name = %s AND chapter_num = %s
                                    ORDER BY verse_num
                                    LIMIT 3
                                """, (p_book, p_chapter))
                                
                            for row in cur.fetchall():
                                cross_references.append({
                                    'reference': f"{row['book_name']} {row['chapter_num']}:{row['verse_num']}",
                                    'text': row['verse_text'],
                                    'type': 'parallel_passage'
                                })
            
            # Method 3: Check for verse references in the versification mappings table
            # This would use the TVTMS data if available
            
            return jsonify({
                'verse': {
                    'reference': f"{book} {chapter}:{verse}",
                    'text': current_verse['verse_text']
                },
                'cross_references': cross_references
            })
            
    except Exception as e:
        logger.error(f"Error getting cross-references: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/semantic-search', methods=['GET'])
def semantic_search():
    """
    Perform a semantic search for Bible passages.
    This uses a simplified semantic approach based on word overlap and frequency.
    A more advanced implementation would use embeddings or other NLP techniques.
    """
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Step 1: Tokenize the query into words
            query_words = re.findall(r'\w+', query.lower())
            
            # Filter out common stopwords
            stopwords = {'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'was', 'for',
                        'on', 'with', 'as', 'by', 'at', 'from', 'be', 'this', 'but', 'not',
                        'are', 'have', 'had', 'has', 'they', 'you', 'he', 'she', 'it', 'we'}
            
            query_words = [word for word in query_words if word not in stopwords and len(word) > 2]
            
            if not query_words:
                return jsonify({'error': 'Query too generic. Please use more specific terms.'}), 400
            
            # Step 2: Find verses containing these words
            placeholders = ','.join(['%s'] * len(query_words))
            like_conditions = []
            params = []
            
            for word in query_words:
                like_conditions.append("verse_text ILIKE %s")
                params.append(f'%{word}%')
            
            # Use a weighted approach - more matches = higher rank
            query_sql = f"""
                SELECT book_name, chapter_num, verse_num, verse_text,
                       (
                           {' + '.join([f"(CASE WHEN verse_text ILIKE %s THEN 1 ELSE 0 END)" for _ in query_words])}
                       ) as match_score
                FROM bible.verses
                WHERE {' OR '.join(like_conditions)}
                ORDER BY match_score DESC, book_name, chapter_num, verse_num
                LIMIT %s
            """
            
            # Double the parameters (once for CASE, once for WHERE)
            cur.execute(query_sql, params + params + [limit])
            
            results = [dict(row) for row in cur.fetchall()]
            
            # Step 3: Get context for each result (verses before/after)
            for i, result in enumerate(results):
                book = result['book_name']
                chapter = result['chapter_num']
                verse = result['verse_num']
                
                # Get previous verse
                cur.execute("""
                    SELECT verse_text
                    FROM bible.verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                    LIMIT 1
                """, (book, chapter, verse - 1))
                prev_verse = cur.fetchone()
                
                # Get next verse
                cur.execute("""
                    SELECT verse_text
                    FROM bible.verses
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                    LIMIT 1
                """, (book, chapter, verse + 1))
                next_verse = cur.fetchone()
                
                results[i]['context'] = {
                    'previous': prev_verse['verse_text'] if prev_verse else None,
                    'next': next_verse['verse_text'] if next_verse else None
                }
                
                # Format the reference as a string
                results[i]['reference'] = f"{book} {chapter}:{verse}"
            
            # Step 4: Add result metadata
            total_matches = len(results)
            
            # Get book distribution
            book_counts = {}
            for result in results:
                book = result['book_name']
                book_counts[book] = book_counts.get(book, 0) + 1
            
            return jsonify({
                'query': query,
                'total_matches': total_matches,
                'results': results,
                'metadata': {
                    'book_distribution': book_counts,
                    'matched_terms': query_words
                }
            })
            
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/lexicon/hebrew/validate_critical_terms', methods=['GET'])
def validate_critical_terms():
    critical_terms = {
        "H430": {"name": "Elohim", "hebrew": "אלהים", "expected_min": 2600},
        "H113": {"name": "Adon", "hebrew": "אדון", "expected_min": 335},
        "H2617": {"name": "Chesed", "hebrew": "חסד", "expected_min": 248}
    }
    results = []
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for strongs_id, info in critical_terms.items():
                cur.execute(
                    """
                    SELECT COUNT(*) as count 
                    FROM bible.hebrew_ot_words 
                    WHERE strongs_id = %s AND word_text = %s
                    """, (strongs_id, info["hebrew"])
                )
                count = cur.fetchone()['count']
                results.append({
                    "term": info["name"],
                    "hebrew": info["hebrew"],
                    "strongs_id": strongs_id,
                    "count": count,
                    "valid": count >= info["expected_min"]
                })
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error validating critical terms: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/theological_terms_report', methods=['GET'])
def theological_terms_report():
    # List of key theological terms (Strong's ID, root, language)
    terms = [
        # Hebrew
        {"strongs_id": "H430", "root": "אלהים", "term": "Elohim", "language": "hebrew"},
        {"strongs_id": "H3068", "root": "יהוה", "term": "YHWH", "language": "hebrew"},
        {"strongs_id": "H113", "root": "אדון", "term": "Adon", "language": "hebrew"},
        {"strongs_id": "H4899", "root": "משיח", "term": "Mashiach", "language": "hebrew"},
        {"strongs_id": "H6944", "root": "קדש", "term": "Qodesh", "language": "hebrew"},
        {"strongs_id": "H8451", "root": "תורה", "term": "Torah", "language": "hebrew"},
        {"strongs_id": "H2617", "root": "חסד", "term": "Chesed", "language": "hebrew"},
        {"strongs_id": "H6664", "root": "צדק", "term": "Tsedeq", "language": "hebrew"},
        {"strongs_id": "H5315", "root": "נפש", "term": "Nephesh", "language": "hebrew"},
        {"strongs_id": "H7965", "root": "שלום", "term": "Shalom", "language": "hebrew"},
        # Greek
        {"strongs_id": "G2316", "root": "θεος", "term": "Theos", "language": "greek"},
        {"strongs_id": "G2962", "root": "κυριος", "term": "Kyrios", "language": "greek"},
        {"strongs_id": "G5547", "root": "χριστος", "term": "Christos", "language": "greek"},
        {"strongs_id": "G4151", "root": "πνευμα", "term": "Pneuma", "language": "greek"},
        {"strongs_id": "G40",   "root": "αγιος", "term": "Hagios", "language": "greek"},
        {"strongs_id": "G26",   "root": "αγαπη", "term": "Agape", "language": "greek"},
        {"strongs_id": "G4102", "root": "πιστις", "term": "Pistis", "language": "greek"},
        {"strongs_id": "G1680", "root": "ελπις", "term": "Elpis", "language": "greek"},
        {"strongs_id": "G5485", "root": "χαρις", "term": "Charis", "language": "greek"},
        {"strongs_id": "G1515", "root": "ειρηνη", "term": "Eirene", "language": "greek"},
    ]
    results = []
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for t in terms:
                if t["language"] == "hebrew":
                    cur.execute(
                        """
                        SELECT COUNT(*) as count FROM bible.hebrew_ot_words
                        WHERE strongs_id = %s OR grammar_code LIKE %s
                        """,
                        (t["strongs_id"], f"%{{{t['strongs_id']}}}%")
                    )
                else:
                    cur.execute(
                        """
                        SELECT COUNT(*) as count FROM bible.greek_nt_words
                        WHERE strongs_id = %s
                        """,
                        (t["strongs_id"],)
                    )
                count = cur.fetchone()["count"]
                results.append({
                    "term": t["term"],
                    "strongs_id": t["strongs_id"],
                    "root": t["root"],
                    "language": t["language"],
                    "count": count
                })
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error generating theological terms report: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(debug=True) 