#!/usr/bin/env python3
"""
Web application for STEPBible lexicons and tagged Bible texts.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime
import sys

# Import user interaction logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.log_user_interactions import log_web_interaction, log_question_answer, ensure_directories

# Import the external resources blueprint
from api.external_resources_api import external_resources_bp

# Import the cross-language API blueprint
from src.api.cross_language_api import api_blueprint as cross_language_api

# Import the new API
from src.api.vector_search_api import vector_search_api

# Import comprehensive search API
from src.api.comprehensive_search import comprehensive_search_api

# Import DSPy API
from src.api.dspy_api import api_blueprint as dspy_api

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

# Create necessary directories for logging
ensure_directories()

# Register the external resources blueprint
app.register_blueprint(external_resources_bp)

# Register the cross-language API blueprint
app.register_blueprint(cross_language_api, url_prefix='/api/cross_language')

# Register the new API
app.register_blueprint(vector_search_api, url_prefix='/api')

# Register the comprehensive search API
app.register_blueprint(comprehensive_search_api, url_prefix='/api/comprehensive')

# Register the DSPy API
app.register_blueprint(dspy_api, url_prefix='/api/dspy')

# API Base URL - use local host if running on same server
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
logger.info(f"Using API Base URL: {API_BASE_URL}")

# DSPy API Base URL - points to the standalone DSPy server
DSPY_API_URL = os.getenv('DSPY_API_URL', 'http://localhost:5003')
logger.info(f"Using DSPy API URL: {DSPY_API_URL}")

# Check if the API endpoint is accessible
# For Flask 2.x, use before_request with a function that runs once
_api_checked = False

@app.before_request
def check_api_connection():
    """Verify API connection is available before processing any request."""
    if request.endpoint == 'static':
        return  # Skip for static assets
        
    try:
        # Catch the health check endpoint to avoid infinite recursion
        if request.path == '/health':
            return
            
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            return render_template('error.html', message="API server is not available.")
    except requests.RequestException:
        return render_template('error.html', message="Cannot connect to API server.")

# Book name mapping dictionary
BOOK_MAPPING = {
    # Old Testament
    'Genesis': 'Gen',
    'Exodus': 'Exo',
    'Leviticus': 'Lev',
    'Numbers': 'Num',
    'Deuteronomy': 'Deu',
    'Joshua': 'Jos',
    'Judges': 'Jdg',
    'Ruth': 'Rut',
    '1 Samuel': '1Sa',
    '2 Samuel': '2Sa',
    '1 Kings': '1Ki',
    '2 Kings': '2Ki',
    '1 Chronicles': '1Ch',
    '2 Chronicles': '2Ch',
    'Ezra': 'Ezr',
    'Nehemiah': 'Neh',
    'Esther': 'Est',
    'Job': 'Job',
    'Psalms': 'Psa',
    'Psalm': 'Psa',
    'Proverbs': 'Pro',
    'Ecclesiastes': 'Ecc',
    'Song of Solomon': 'Sng',
    'Isaiah': 'Isa',
    'Jeremiah': 'Jer',
    'Lamentations': 'Lam',
    'Ezekiel': 'Ezk',
    'Daniel': 'Dan',
    'Hosea': 'Hos',
    'Joel': 'Jol',
    'Amos': 'Amo',
    'Obadiah': 'Oba',
    'Jonah': 'Jon',
    'Micah': 'Mic',
    'Nahum': 'Nam',
    'Habakkuk': 'Hab',
    'Zephaniah': 'Zep',
    'Haggai': 'Hag',
    'Zechariah': 'Zec',
    'Malachi': 'Mal',
    
    # New Testament
    'Matthew': 'Mat',
    'Mark': 'Mrk',
    'Luke': 'Luk',
    'John': 'Jhn',
    'Acts': 'Act',
    'Romans': 'Rom',
    '1 Corinthians': '1Co',
    '2 Corinthians': '2Co',
    'Galatians': 'Gal',
    'Ephesians': 'Eph',
    'Philippians': 'Php',
    'Colossians': 'Col',
    '1 Thessalonians': '1Th',
    '2 Thessalonians': '2Th',
    '1 Timothy': '1Ti',
    '2 Timothy': '2Ti',
    'Titus': 'Tit',
    'Philemon': 'Phm',
    'Hebrews': 'Heb',
    'James': 'Jas',
    '1 Peter': '1Pe',
    '2 Peter': '2Pe',
    '1 John': '1Jn',
    '2 John': '2Jn',
    '3 John': '3Jn',
    'Jude': 'Jud',
    'Revelation': 'Rev'
}

def get_abbreviated_book_name(book):
    """Convert full book name to abbreviated form if needed."""
    return BOOK_MAPPING.get(book, book)

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
    """Home page with statistics."""
    try:
        # Get statistics from API
        response = requests.get(f"{API_BASE_URL}/api/lexicon/stats")
        
        stats = {
            'hebrew_lexicon_count': 0,
            'greek_lexicon_count': 0,
            'verse_count': 0,
            'proper_names_count': 0,
            'proper_name_refs_count': 0
        }
        
        if response.status_code == 200:
            api_stats = response.json()
            if 'hebrew_lexicon' in api_stats:
                stats['hebrew_lexicon_count'] = api_stats['hebrew_lexicon']['count']
            if 'greek_lexicon' in api_stats:
                stats['greek_lexicon_count'] = api_stats['greek_lexicon']['count']
            if 'verses' in api_stats:
                stats['verse_count'] = api_stats['verses']['count']
            if 'proper_names' in api_stats:
                stats['proper_names_count'] = api_stats['proper_names']['count']
                stats['proper_name_refs_count'] = api_stats['proper_names']['references']
        
        return render_template('index.html', stats=stats)
    
    except Exception as e:
        logging.error(f"Error retrieving home page stats: {e}")
        # If we can't get stats, still show the home page with default values
        return render_template('index.html', stats={
            'hebrew_lexicon_count': 8674,  # Default estimate
            'greek_lexicon_count': 5624,   # Default estimate
            'verse_count': 31102,          # Default estimate of Bible verses
            'proper_names_count': 3500,    # Default estimate
            'proper_name_refs_count': 15000 # Default estimate
        })

@app.route('/search')
def search():
    """Search page for lexicons, verses, and proper names."""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'lexicon')
    
    results = None
    error = None
    
    if query:
        try:
            if search_type == 'lexicon':
                # Search lexicons
                response = requests.get(f"{API_BASE_URL}/api/lexicon/search", 
                                       params={'q': query, 'limit': 50})
                
                if response.status_code == 200:
                    results = response.json()
                else:
                    error = f"Lexicon search error: {response.json().get('error', 'Unknown error')}"
                    
            elif search_type == 'verse':
                # Search verses
                response = requests.get(f"{API_BASE_URL}/api/verses/search", 
                                       params={'q': query, 'limit': 50})
                
                if response.status_code == 200:
                    results = response.json()
                else:
                    error = f"Verse search error: {response.json().get('error', 'Unknown error')}"
                
            elif search_type == 'name':
                # Search proper names
                response = requests.get(f"{API_BASE_URL}/api/names/search", 
                                       params={'q': query, 'type': 'name', 'limit': 50})
                
                if response.status_code == 200:
                    results = response.json()
                else:
                    error = f"Name search error: {response.json().get('error', 'Unknown error')}"
                
            elif search_type == 'morphology':
                # Search morphology codes
                hebrew_response = requests.get(f"{API_BASE_URL}/api/morphology/hebrew", 
                                             params={'code': query, 'limit': 25})
                
                greek_response = requests.get(f"{API_BASE_URL}/api/morphology/greek", 
                                            params={'code': query, 'limit': 25})
                
                results = {
                    'hebrew': hebrew_response.json() if hebrew_response.status_code == 200 else [],
                    'greek': greek_response.json() if greek_response.status_code == 200 else []
                }
                
                if not results['hebrew'] and not results['greek']:
                    error = "No morphology codes found matching the query"
            
            else:
                error = f"Invalid search type: {search_type}"
        
        except Exception as e:
            logging.error(f"Error in search: {e}")
            error = f"An error occurred: {str(e)}"
    
    return render_template('search.html', 
                          query=query,
                          search_type=search_type,
                          results=results,
                          error=error)

@app.route('/lexicon/<lang>/<strongs_id>')
def lexicon_entry(lang, strongs_id):
    """
    Display details for a specific lexicon entry.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return render_template('error.html', error="Database connection error")
            
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if lang == 'hebrew':
                cur.execute("""
                    SELECT * FROM bible.hebrew_entries WHERE strongs_id = %s
                """, (strongs_id,))
                entry = cur.fetchone()
                
                if not entry:
                    return render_template('error.html', error="Entry not found")
                
                # Get related words
                cur.execute("""
                    SELECT wr.target_id, wr.relationship_type, 
                           CASE 
                               WHEN he.hebrew_word IS NOT NULL THEN he.hebrew_word 
                               ELSE ge.greek_word 
                           END as word,
                           CASE 
                               WHEN he.transliteration IS NOT NULL THEN he.transliteration 
                               ELSE ge.transliteration 
                           END as transliteration,
                           CASE 
                               WHEN he.gloss IS NOT NULL THEN he.gloss 
                               ELSE ge.gloss 
                           END as gloss,
                           CASE 
                               WHEN he.strongs_id IS NOT NULL THEN 'hebrew' 
                               ELSE 'greek' 
                           END as language
                    FROM bible.word_relationships wr
                    LEFT JOIN bible.hebrew_entries he ON wr.target_id = he.strongs_id
                    LEFT JOIN bible.greek_entries ge ON wr.target_id = ge.strongs_id
                    WHERE wr.source_id = %s
                """, (strongs_id,))
                related_words = [dict(row) for row in cur.fetchall()]
                
                # Get verse occurrences
                cur.execute("""
                    SELECT DISTINCT v.book_name, v.chapter_num, v.verse_num, v.verse_text
                    FROM bible.hebrew_ot_words w
                    JOIN bible.verses v ON 
                        w.book_name = v.book_name AND 
                        w.chapter_num = v.chapter_num AND 
                        w.verse_num = v.verse_num
                    WHERE w.strongs_id = %s
                    LIMIT 20
                """, (strongs_id,))
                occurrences = [dict(row) for row in cur.fetchall()]
                
                return render_template('lexicon_entry.html', 
                                       entry=dict(entry), 
                                       related_words=related_words,
                                       occurrences=occurrences,
                                       lang=lang)
            
            elif lang == 'greek':
                cur.execute("""
                    SELECT * FROM bible.greek_entries WHERE strongs_id = %s
                """, (strongs_id,))
                entry = cur.fetchone()
                
                if not entry:
                    return render_template('error.html', error="Entry not found")
                
                # Get related words
                cur.execute("""
                    SELECT wr.target_id, wr.relationship_type, 
                           CASE 
                               WHEN he.hebrew_word IS NOT NULL THEN he.hebrew_word 
                               ELSE ge.greek_word 
                           END as word,
                           CASE 
                               WHEN he.transliteration IS NOT NULL THEN he.transliteration 
                               ELSE ge.transliteration 
                           END as transliteration,
                           CASE 
                               WHEN he.gloss IS NOT NULL THEN he.gloss 
                               ELSE ge.gloss 
                           END as gloss,
                           CASE 
                               WHEN he.strongs_id IS NOT NULL THEN 'hebrew' 
                               ELSE 'greek' 
                           END as language
                    FROM bible.word_relationships wr
                    LEFT JOIN bible.hebrew_entries he ON wr.target_id = he.strongs_id
                    LEFT JOIN bible.greek_entries ge ON wr.target_id = ge.strongs_id
                    WHERE wr.source_id = %s
                """, (strongs_id,))
                related_words = [dict(row) for row in cur.fetchall()]
                
                # Get verse occurrences
                cur.execute("""
                    SELECT DISTINCT v.book_name, v.chapter_num, v.verse_num, v.verse_text
                    FROM bible.greek_nt_words w
                    JOIN bible.verses v ON 
                        w.book_name = v.book_name AND 
                        w.chapter_num = v.chapter_num AND 
                        w.verse_num = v.verse_num
                    WHERE w.strongs_id = %s
                    LIMIT 20
                """, (strongs_id,))
                occurrences = [dict(row) for row in cur.fetchall()]
                
                return render_template('lexicon_entry.html', 
                                       entry=dict(entry), 
                                       related_words=related_words,
                                       occurrences=occurrences,
                                       lang=lang)
            
            else:
                return render_template('error.html', error="Invalid language")
    except Exception as e:
        logger.error(f"Error loading lexicon entry {lang}/{strongs_id}: {e}")
        return render_template('error.html', error=str(e))
    finally:
        if conn:
            conn.close()

@app.route('/verse/<book>/<int:chapter>/<int:verse>')
def verse_detail(book, chapter, verse):
    """
    Display details for a specific verse with its tagged words.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return render_template('error.html', error="Database connection error")
        
        # Convert book name to abbreviated form
        api_book = get_abbreviated_book_name(book)
            
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get verse
            cur.execute("""
                SELECT * FROM bible.verses 
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
            """, (api_book, chapter, verse))
            verse_data = cur.fetchone()
            
            if not verse_data:
                return render_template('error.html', error="Verse not found")
            
            # Try to get Greek words for this verse
            cur.execute("""
                SELECT w.*, g.gloss, g.transliteration, g.pos
                FROM bible.greek_nt_words w
                LEFT JOIN bible.greek_entries g ON w.strongs_id = g.strongs_id
                WHERE w.book_name = %s AND w.chapter_num = %s AND w.verse_num = %s
                ORDER BY w.word_num
            """, (api_book, chapter, verse))
            greek_words = [dict(row) for row in cur.fetchall()]
            
            # Try to get Hebrew words for this verse
            cur.execute("""
                SELECT w.*, h.gloss, h.transliteration, h.pos
                FROM bible.hebrew_ot_words w
                LEFT JOIN bible.hebrew_entries h ON w.strongs_id = h.strongs_id
                WHERE w.book_name = %s AND w.chapter_num = %s AND w.verse_num = %s
                ORDER BY w.word_num
            """, (api_book, chapter, verse))
            hebrew_words = [dict(row) for row in cur.fetchall()]
            
            # Get parallel verses if any
            cur.execute("""
                SELECT v.* 
                FROM bible.verse_parallel_mapping vpm
                JOIN bible.verses v ON vpm.target_verse_id = v.id
                WHERE vpm.source_verse_id = %s
            """, (verse_data['id'],))
            parallel_verses = [dict(row) for row in cur.fetchall()]
            
            # Get proper names mentioned in this verse
            proper_names = []
            try:
                names_response = requests.get(
                    f"{API_BASE_URL}/api/verse/names",
                    params={'book': api_book, 'chapter': chapter, 'verse': verse}
                )
                if names_response.status_code == 200:
                    names_data = names_response.json()
                    proper_names = names_data.get('names', [])
            except Exception as e:
                logger.warning(f"Error fetching proper names for verse: {e}")
            
            # Add a link to cross-references
            cross_refs_link = f'/cross-references/{book}/{chapter}/{verse}'
            
            return render_template('verse_detail.html', 
                                  verse=dict(verse_data),
                                  greek_words=greek_words,
                                  hebrew_words=hebrew_words,
                                  parallel_verses=parallel_verses,
                                  proper_names=proper_names,
                                  cross_refs_link=cross_refs_link)
    except Exception as e:
        logger.error(f"Error loading verse {book}/{chapter}/{verse}: {e}")
        return render_template('error.html', error=str(e))
    finally:
        if conn:
            conn.close()

# Add routes for morphology codes
@app.route('/morphology')
def morphology_home():
    """Display morphology codes search and info page."""
    return render_template('morphology.html')

@app.route('/morphology/hebrew/<code>')
def hebrew_morphology_detail(code):
    """Display details for a specific Hebrew morphology code."""
    try:
        # Get the morphology code data from the API
        response = requests.get(f"{API_BASE_URL}/api/morphology/hebrew/{code}")
        
        if response.status_code != 200:
            return render_template('error.html', 
                                   message=f"Error retrieving Hebrew morphology code: {response.json().get('error', 'Unknown error')}")
        
        morphology_data = response.json()
        
        # Get a list of examples where this code is used
        examples_response = requests.get(f"{API_BASE_URL}/api/hebrew/words", 
                                        params={'grammar_code': code, 'limit': 10})
        examples = examples_response.json() if examples_response.status_code == 200 else []
        
        return render_template('morphology_detail.html', 
                              morphology=morphology_data,
                              examples=examples,
                              language='hebrew')
        
    except Exception as e:
        logging.error(f"Error displaying Hebrew morphology code {code}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/morphology/greek/<code>')
def greek_morphology_detail(code):
    """Display details for a specific Greek morphology code."""
    try:
        # Get the morphology code data from the API
        response = requests.get(f"{API_BASE_URL}/api/morphology/greek/{code}")
        
        if response.status_code != 200:
            return render_template('error.html', 
                                   message=f"Error retrieving Greek morphology code: {response.json().get('error', 'Unknown error')}")
        
        morphology_data = response.json()
        
        # Get a list of examples where this code is used
        examples_response = requests.get(f"{API_BASE_URL}/api/greek/words", 
                                        params={'grammar_code': code, 'limit': 10})
        examples = examples_response.json() if examples_response.status_code == 200 else []
        
        return render_template('morphology_detail.html', 
                              morphology=morphology_data,
                              examples=examples,
                              language='greek')
        
    except Exception as e:
        logging.error(f"Error displaying Greek morphology code {code}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

# Add routes for proper names
@app.route('/names')
def names_home():
    """Display proper names search and info page."""
    try:
        # Get filter data from API
        filter_response = requests.get(f"{API_BASE_URL}/api/names/types")
        filter_data = filter_response.json() if filter_response.status_code == 200 else {
            'types': ['Person', 'Location', 'Title', 'Other'],
            'genders': ['Male', 'Female'],
            'book_counts': {}
        }
        
        # Get most viewed/popular names (limited to 5)
        popular_response = requests.get(f"{API_BASE_URL}/api/names", params={'limit': 5})
        popular_names = []
        
        if popular_response.status_code == 200:
            popular_names = popular_response.json()
            
        return render_template('names.html', 
                              filter_data=filter_data,
                              popular_names=popular_names)
    except Exception as e:
        logging.error(f"Error displaying names home: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/names/<int:name_id>')
def name_detail(name_id):
    """Display details for a specific proper name."""
    try:
        # Get the proper name data from the API
        response = requests.get(f"{API_BASE_URL}/api/names/{name_id}")
        
        if response.status_code != 200:
            return render_template('error.html', 
                                   message=f"Error retrieving proper name: {response.json().get('error', 'Unknown error')}")
        
        name_data = response.json()
        
        return render_template('name_detail.html', name=name_data)
        
    except Exception as e:
        logging.error(f"Error displaying proper name {name_id}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/names/search')
def name_search():
    """Search for proper names."""
    try:
        # Get search parameters
        search_term = request.args.get('q', '')
        search_type = request.args.get('type', 'name')
        name_type = request.args.get('name_type', '')
        gender = request.args.get('gender', '')
        book = request.args.get('book', '')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Get filter data for form fields
        filter_response = requests.get(f"{API_BASE_URL}/api/names/types")
        filter_data = filter_response.json() if filter_response.status_code == 200 else {
            'types': ['Person', 'Location', 'Title', 'Other'],
            'genders': ['Male', 'Female'],
            'book_counts': {}
        }
        
        # If no search parameters provided, just show the form
        if not search_term and not name_type and not gender and not book:
            return render_template('names.html', 
                                  filter_data=filter_data,
                                  search_term=search_term,
                                  search_type=search_type)
        
        # Call the API with all parameters
        params = {
            'q': search_term,
            'type': search_type,
            'name_type': name_type,
            'gender': gender,
            'book': book,
            'offset': offset,
            'limit': limit
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        response = requests.get(f"{API_BASE_URL}/api/names/search", params=params)
        
        if response.status_code != 200:
            return render_template('names.html', 
                                  error=f"Search error: {response.json().get('error', 'Unknown error')}",
                                  search_term=search_term,
                                  search_type=search_type,
                                  filter_data=filter_data,
                                  filters={
                                    'name_type': name_type,
                                    'gender': gender,
                                    'book': book
                                  })
        
        data = response.json()
        results = data.get('results', [])
        metadata = data.get('metadata', {})
        
        return render_template('names.html', 
                              results=results, 
                              metadata=metadata,
                              search_term=search_term,
                              search_type=search_type,
                              filter_data=filter_data,
                              filters={
                                'name_type': name_type,
                                'gender': gender,
                                'book': book
                              })
        
    except Exception as e:
        logging.error(f"Error searching proper names: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

# Update the existing Bible route to handle both Hebrew OT and Greek NT
@app.route('/bible/<book>/<int:chapter>/<int:verse>')
def bible_verse(book, chapter, verse):
    """
    Display Bible verse with options to view in different formats.
    """
    try:
        # Convert book name to abbreviated form
        api_book = get_abbreviated_book_name(book)
        
        # Determine if this is Hebrew or Greek based on the book
        is_hebrew = True  # Default to Hebrew
        
        # Basic list of NT books (abbreviated)
        nt_books = ['Mat', 'Mrk', 'Luk', 'Jhn', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Php', 'Col', 
                   '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe', '2Pe', '1Jn', '2Jn', '3Jn', 'Jud', 'Rev']
        
        if api_book in nt_books:
            is_hebrew = False
        
        # Redirect to the appropriate verse view
        if is_hebrew:
            return redirect(url_for('verse_detail', book=api_book, chapter=chapter, verse=verse))
        else:
            return redirect(url_for('verse_detail', book=api_book, chapter=chapter, verse=verse))
            
    except Exception as e:
        logger.error(f"Error redirecting to verse {book}/{chapter}/{verse}: {e}")
        return render_template('error.html', error=str(e))

# Arabic Bible routes
@app.route('/arabic')
def arabic_bible_home():
    """Display the Arabic Bible explorer page."""
    try:
        # Call the API to get Arabic Bible stats
        response = requests.get(f"{API_BASE_URL}/api/arabic/stats")
        
        if response.status_code != 200:
            return render_template('error.html', 
                                  message=f"Error retrieving Arabic Bible stats: {response.json().get('error', 'Unknown error')}")
        
        stats = response.json()
        
        return render_template('arabic_bible.html', 
                              stats=stats)
        
    except Exception as e:
        logging.error(f"Error displaying Arabic Bible home: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/arabic/verse/<book>/<int:chapter>/<int:verse>')
def arabic_verse(book, chapter, verse):
    """Display a verse from the Arabic Bible."""
    try:
        # Convert book name to abbreviated form
        api_book = get_abbreviated_book_name(book)
        
        # Call the API to get verse data
        response = requests.get(f"{API_BASE_URL}/api/arabic/verse", 
                               params={'book': api_book, 'chapter': chapter, 'verse': verse})
        
        if response.status_code != 200:
            return render_template('error.html', 
                                  message=f"Error retrieving Arabic verse: {response.json().get('error', 'Unknown error')}")
        
        verse_data = response.json()
        
        # Get surrounding verses for context
        context_response = requests.get(f"{API_BASE_URL}/api/arabic/context", 
                                      params={'book': api_book, 'chapter': chapter, 'verse': verse, 'context': 3})
        
        context_verses = []
        if context_response.status_code == 200:
            context_verses = context_response.json().get('verses', [])
            
        return render_template('arabic_verse.html', 
                              verse=verse_data.get('verse', {}),
                              words=verse_data.get('words', []),
                              context_verses=context_verses,
                              book=book,
                              chapter=chapter,
                              verse_num=verse)
        
    except Exception as e:
        logging.error(f"Error displaying Arabic verse {book} {chapter}:{verse}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/arabic/search')
def arabic_search():
    """Search the Arabic Bible."""
    query = request.args.get('q', '')
    book = request.args.get('book', '')
    
    if not query:
        # If no query, just show the search form
        return render_template('arabic_search.html', results=None)
    
    try:
        # Call the API to search
        response = requests.get(f"{API_BASE_URL}/api/arabic/search", 
                               params={'q': query, 'book': book, 'limit': 50})
        
        if response.status_code != 200:
            return render_template('error.html', 
                                  message=f"Error searching Arabic Bible: {response.json().get('error', 'Unknown error')}")
        
        search_results = response.json()
        
        return render_template('arabic_search.html', 
                              results=search_results,
                              query=query,
                              book=book)
        
    except Exception as e:
        logging.error(f"Error searching Arabic Bible: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/arabic/parallel/<book>/<int:chapter>/<int:verse>')
def arabic_parallel(book, chapter, verse):
    """Display a verse in Arabic alongside Greek or Hebrew."""
    try:
        # Convert book name to abbreviated form
        api_book = get_abbreviated_book_name(book)
        
        # Call the API to get parallel verses
        response = requests.get(f"{API_BASE_URL}/api/arabic/parallel", 
                               params={'book': api_book, 'chapter': chapter, 'verse': verse})
        
        if response.status_code != 200:
            return render_template('error.html', 
                                  message=f"Error retrieving parallel verses: {response.json().get('error', 'Unknown error')}")
        
        parallel_data = response.json()
        
        return render_template('arabic_parallel.html', 
                              parallel=parallel_data,
                              book=book,
                              chapter=chapter,
                              verse=verse)
        
    except Exception as e:
        logging.error(f"Error displaying parallel verses for {book} {chapter}:{verse}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/concordance/<strongs_id>')
def concordance(strongs_id):
    """
    Display concordance for a specific Strong's number.
    """
    try:
        # Determine if this is Arabic or standard concordance
        show_arabic = request.args.get('arabic', '').lower() == 'true'
        
        if show_arabic:
            response = requests.get(f"{API_BASE_URL}/api/concordance/arabic/{strongs_id}")
        else:
            response = requests.get(f"{API_BASE_URL}/api/concordance/{strongs_id}")
        
        if response.status_code == 200:
            concordance_data = response.json()
            
            # Get language info
            is_hebrew = strongs_id.startswith('H')
            language = "Hebrew" if is_hebrew else "Greek"
            
            return render_template('concordance.html', 
                                  data=concordance_data, 
                                  strongs_id=strongs_id,
                                  language=language,
                                  show_arabic=show_arabic)
        else:
            error = response.json().get('error', 'Unknown error')
            return render_template('error.html', message=f"Error: {error}")
            
    except Exception as e:
        logger.error(f"Error displaying concordance for {strongs_id}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/export/concordance/<strongs_id>')
def export_concordance(strongs_id):
    """
    Export concordance data to CSV format.
    """
    try:
        # Determine if this is Arabic or standard concordance
        show_arabic = request.args.get('arabic', '').lower() == 'true'
        
        if show_arabic:
            response = requests.get(f"{API_BASE_URL}/api/concordance/arabic/{strongs_id}")
        else:
            response = requests.get(f"{API_BASE_URL}/api/concordance/{strongs_id}")
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to retrieve concordance data'}), 500
            
        concordance_data = response.json()
        
        # Generate CSV data
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Reference', 'Verse Text', 'Target Word', 'Strong\'s ID'])
        
        # Write data rows
        for occurrence in concordance_data['occurrences']:
            writer.writerow([
                occurrence['reference'],
                occurrence['verse_text'],
                occurrence['target_word']['text'],
                occurrence['target_word']['strongs_id']
            ])
        
        # Prepare response
        response = app.response_class(
            response=output.getvalue(),
            mimetype='text/csv',
            headers={
                "Content-Disposition": f"attachment;filename=concordance_{strongs_id}.csv"
            }
        )
        return response
            
    except Exception as e:
        logger.error(f"Error exporting concordance for {strongs_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cross-references/<book>/<int:chapter>/<int:verse>')
def cross_references(book, chapter, verse):
    """
    Display cross-references for a specific verse.
    """
    try:
        # Convert full book name to abbreviated form if needed
        api_book = get_abbreviated_book_name(book)
        
        response = requests.get(f"{API_BASE_URL}/api/cross-references",
                               params={'book': api_book, 'chapter': chapter, 'verse': verse})
        
        if response.status_code == 200:
            data = response.json()
            return render_template('cross_references.html', 
                                  verse_reference=f"{book} {chapter}:{verse}",
                                  verse_text=data['verse']['text'],
                                  cross_references=data['cross_references'])
        else:
            error = response.json().get('error', 'Unknown error')
            return render_template('error.html', message=f"Error: {error}")
            
    except Exception as e:
        logger.error(f"Error displaying cross-references for {book} {chapter}:{verse}: {e}")
        return render_template('error.html', message=f"An error occurred: {str(e)}")

@app.route('/semantic-search')
def semantic_search():
    """
    Display semantic search form and results.
    """
    query = request.args.get('q', '')
    
    results = None
    error = None
    
    if query:
        try:
            response = requests.get(f"{API_BASE_URL}/api/semantic-search",
                                  params={'q': query, 'limit': 20})
            
            if response.status_code == 200:
                results = response.json()
            else:
                error = response.json().get('error', 'Unknown error')
                
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            error = f"An error occurred: {str(e)}"
    
    return render_template('semantic_search.html',
                          query=query,
                          results=results,
                          error=error)

# Add the new route for viewing verses with external resources
@app.route('/verse-resources/<book>/<int:chapter>/<int:verse>')
def verse_with_resources(book, chapter, verse):
    """
    Display a Bible verse with additional resources from external APIs.
    
    Args:
        book (str): Bible book name
        chapter (int): Chapter number
        verse (int): Verse number
    """
    try:
        # Get the verse details from our internal API
        abbr_book = get_abbreviated_book_name(book)
        response = requests.get(f"{API_BASE_URL}/api/tagged/verse?book={abbr_book}&chapter={chapter}&verse={verse}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get verse data: {response.status_code}")
            return render_template('error.html', message=f"Failed to retrieve verse data for {book} {chapter}:{verse}")
        
        verse_data = response.json()
        
        # Get commentaries from external API
        commentaries_response = requests.get(f"/api/external/commentaries/{abbr_book}/{chapter}/{verse}")
        commentaries = commentaries_response.json() if commentaries_response.status_code == 200 else {"commentaries": []}
        
        # Get archaeological data if relevant
        location = None
        archaeological_data = None
        
        # This is a simplistic approach - in reality, you'd need more sophisticated
        # location detection based on the verse content
        if 'Jerusalem' in verse_data.get('text', ''):
            location = 'Jerusalem'
        elif 'Bethlehem' in verse_data.get('text', ''):
            location = 'Bethlehem'
        
        if location:
            arch_response = requests.get(f"/api/external/archaeological/{location}")
            archaeological_data = arch_response.json() if arch_response.status_code == 200 else None
        
        # Get manuscript data for NT verses
        manuscript_data = None
        if abbr_book in ['Mat', 'Mrk', 'Luk', 'Jhn', 'Act', 'Rom', 'Gal', 'Eph']:
            manu_response = requests.get(f"/api/external/manuscripts/{abbr_book} {chapter}:{verse}")
            manuscript_data = manu_response.json() if manu_response.status_code == 200 else None
        
        # Get multiple translations
        translations_response = requests.get(f"/api/external/translations/{abbr_book} {chapter}:{verse}")
        translations = translations_response.json() if translations_response.status_code == 200 else {"translations": {}}
        
        # Return template with all data
        return render_template(
            'verse_with_resources.html',
            verse=verse_data,
            book=book,
            chapter=chapter,
            verse_num=verse,
            commentaries=commentaries,
            archaeological_data=archaeological_data,
            manuscript_data=manuscript_data,
            translations=translations,
            citation_url=f"/api/external/citations/{abbr_book} {chapter}:{verse}"
        )
    
    except Exception as e:
        logger.error(f"Error retrieving verse with resources: {e}")
        return render_template('error.html', message=f"Error: {e}")

@app.route('/hebrew_terms_validation')
def hebrew_terms_validation():
    try:
        response = requests.get(f"{API_BASE_URL}/api/lexicon/hebrew/validate_critical_terms")
        if response.status_code != 200:
            logger.error(f"Failed to fetch critical terms: {response.status_code}")
            return render_template('error.html', message="Failed to retrieve term validation data")
        results = response.json()
        return render_template('hebrew_terms_validation.html', results=results)
    except Exception as e:
        logger.error(f"Error rendering term validation: {e}")
        return render_template('error.html', message=str(e))

@app.route('/cross_language')
def cross_language():
    try:
        response = requests.get(f"{API_BASE_URL}/api/cross_language/terms")
        if response.status_code != 200:
            logger.error(f"Failed to fetch cross-language terms: {response.status_code}")
            return render_template('error.html', message="Failed to retrieve cross-language terms")
        results = response.json()
        return render_template('cross_language.html', results=results)
    except Exception as e:
        logger.error(f"Error rendering cross-language page: {e}")
        return render_template('error.html', message=str(e))

@app.route('/theological_terms_report')
def theological_terms_report():
    try:
        response = requests.get(f"{API_BASE_URL}/api/theological_terms_report")
        if response.status_code != 200:
            logger.error(f"Failed to fetch theological terms report: {response.status_code}")
            return render_template('error.html', message="Failed to retrieve theological terms report")
        results = response.json()
        return render_template('theological_terms_report.html', results=results)
    except Exception as e:
        logger.error(f"Error rendering theological terms report: {e}")
        return render_template('error.html', message=str(e))

@app.route('/health')
def health_check():
    """Health check endpoint for API connection verification."""
    return jsonify({"status": "OK"}), 200

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

# Web interaction logging decorator
def log_web_request(f):
    """Decorator to log web page interactions for DSPy training data."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get route info
            route = request.path
            query_params = dict(request.args)
            
            # Only log non-static requests with meaningful paths
            if (not route.startswith('/static') and 
                not route == '/health' and 
                not route == '/favicon.ico'):
                
                # Process the request
                response = f(*args, **kwargs)
                
                # Determine response type
                if hasattr(response, 'template_name'):
                    response_type = f"template:{response.template_name}"
                elif isinstance(response, str):
                    response_type = "html"
                else:
                    response_type = "json" if hasattr(response, 'get_json') else "other"
                
                # Log the web interaction
                log_web_interaction(
                    route=route,
                    query_params=query_params,
                    response_type=response_type
                )
                
                return response
            else:
                return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error logging web interaction: {e}")
            return f(*args, **kwargs)
    
    return decorated_function

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
                
                # Log successful semantic search for analytics
                log_web_interaction(
                    route='/vector-search',
                    query_params={'q': query, 'translation': translation},
                    response_type='success',
                    response_data=f"Found {results.get('total_matches', 0)} results"
                )
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
                
                # Log successful similar verses search
                log_web_interaction(
                    route='/similar-verses',
                    query_params={'book': book, 'chapter': chapter, 'verse': verse, 'translation': translation},
                    response_type='success',
                    response_data=f"Found {results.get('total_matches', 0)} similar verses"
                )
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

@app.route('/dspy-ask', methods=['GET', 'POST'])
def dspy_ask():
    """
    Route for the DSPy model training and testing interface.
    """
    # Default values for the form
    context = request.form.get('context', '')
    question = request.form.get('question', '')
    result = None

    if request.method == 'POST':
        # If we're testing a model
        if 'context' in request.form and 'question' in request.form:
            # Prepare data for API call
            data = {
                'context': request.form['context'],
                'question': request.form['question']
            }
            
            try:
                # Make API call to test the model - use DSPY_API_URL
                response = requests.post(
                    f"{DSPY_API_URL}/api/dspy/example",
                    json=data,
                    timeout=30  # Longer timeout for model inference
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log the successful interaction
                    log_web_interaction(
                        route='/dspy-ask',
                        parameters=str(data),
                        response_status=response.status_code,
                        response_data=str(result)
                    )
                else:
                    logger.error(f"DSPy API error: {response.status_code} - {response.text}")
                    flash(f"Error: {response.json().get('error', 'Unknown error')}", "danger")
            except Exception as e:
                logger.error(f"DSPy request error: {str(e)}")
                flash(f"Error: {str(e)}", "danger")
    
    return render_template('dspy_ask.html', context=context, question=question, result=result)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 