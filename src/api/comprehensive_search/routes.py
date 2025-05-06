"""
Routes for comprehensive search API.

This module provides endpoints for searching across all Bible database resources.
"""

import os
import logging
import json
from flask import request, jsonify
import psycopg
from psycopg.rows import dict_row
import requests
from dotenv import load_dotenv

from . import comprehensive_search_api
from src.utils.vector_search_utils import get_embedding, format_vector_for_postgres

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/comprehensive_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234")
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0:2"

def get_db_connection():
    """Get a database connection with the appropriate configuration."""
    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "bible_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        row_factory=dict_row
    )
    return conn

@comprehensive_search_api.route('/vector-search')
def vector_search():
    """
    Comprehensive vector search across all sources.
    
    Query parameters:
        q: Search query
        translation: Primary translation to search (default: KJV)
        include_lexicon: Include lexical data (default: true)
        include_related: Include related terms (default: true)
        include_names: Include proper name data (default: true)
        cross_language: Search across languages (default: false)
        limit: Number of results (default: 10)
    """
    # Get query parameters
    query = request.args.get('q', '')
    translation = request.args.get('translation', 'KJV')
    include_lexicon = request.args.get('include_lexicon', 'true').lower() == 'true'
    include_related = request.args.get('include_related', 'true').lower() == 'true'
    include_names = request.args.get('include_names', 'true').lower() == 'true'
    cross_language = request.args.get('cross_language', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 10)), 50)
    
    # Validate input
    if not query:
        return jsonify({
            'error': 'No search query provided',
            'results': []
        }), 400
    
    try:
        # Get query embedding
        query_embedding = get_embedding(query)
        if not query_embedding:
            return jsonify({
                'error': 'Failed to generate embedding for query',
                'results': []
            }), 500
        
        # Format the embedding array for PostgreSQL
        embedding_array = format_vector_for_postgres(query_embedding)
        
        # Determine which lexicon tables to use based on translation
        is_hebrew = translation in ['TAHOT']
        is_greek = translation in ['TAGNT']
        
        # Build base query for the specified translation
        conn = get_db_connection()
        results = []
        
        with conn.cursor() as cur:
            # Base semantic search query
            base_query = """
            SELECT 
                v.id, 
                v.book_name, 
                v.chapter_num, 
                v.verse_num, 
                v.verse_text,
                v.translation_source,
                1 - (e.embedding <=> %s::vector) AS similarity
            FROM 
                bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
            WHERE 
                v.translation_source = %s
            ORDER BY 
                e.embedding <=> %s::vector
            LIMIT %s
            """
            
            # Execute base query
            cur.execute(base_query, (embedding_array, translation, embedding_array, limit))
            base_results = cur.fetchall()
            
            # Process base results
            for result in base_results:
                verse_data = {
                    'reference': f"{result['book_name']} {result['chapter_num']}:{result['verse_num']}",
                    'text': result['verse_text'],
                    'translation': result['translation_source'],
                    'similarity': round(float(result['similarity']) * 100, 2),
                }
                
                # Add lexical information if requested
                if include_lexicon:
                    if is_hebrew:
                        # Get Hebrew lexical data
                        lexical_query = """
                        SELECT 
                            w.word_text, 
                            w.word_position,
                            w.strongs_id, 
                            w.grammar_code,
                            h.lemma, 
                            h.definition
                        FROM 
                            bible.hebrew_ot_words w
                            JOIN bible.hebrew_entries h ON w.strongs_id = h.strongs_id
                        WHERE 
                            w.verse_id = %s
                        ORDER BY 
                            w.word_position
                        """
                        cur.execute(lexical_query, (result['id'],))
                        
                    elif is_greek:
                        # Get Greek lexical data
                        lexical_query = """
                        SELECT 
                            w.word_text, 
                            w.word_position,
                            w.strongs_id, 
                            w.grammar_code,
                            g.lemma, 
                            g.definition
                        FROM 
                            bible.greek_nt_words w
                            JOIN bible.greek_entries g ON w.strongs_id = g.strongs_id
                        WHERE 
                            w.verse_id = %s
                        ORDER BY 
                            w.word_position
                        """
                        cur.execute(lexical_query, (result['id'],))
                    
                    # For other translations, skip lexical data for now
                    else:
                        lexical_data = []
                        verse_data['lexical_data'] = lexical_data
                        results.append(verse_data)
                        continue
                    
                    lexical_data = cur.fetchall()
                    verse_data['lexical_data'] = [
                        {
                            'word': lex['word_text'],
                            'position': lex['word_position'],
                            'strongs_id': lex['strongs_id'],
                            'grammar': lex['grammar_code'],
                            'lemma': lex['lemma'],
                            'definition': lex['definition']
                        } for lex in lexical_data
                    ]
                
                # Add proper name information if requested
                if include_names and (is_hebrew or is_greek):
                    name_query = """
                    SELECT 
                        pn.name_id,
                        pn.name,
                        pn.transliteration,
                        pn.description
                    FROM 
                        bible.proper_names pn
                        JOIN bible.proper_name_forms pnf ON pn.name_id = pnf.name_id
                        JOIN bible.hebrew_ot_words w ON w.word_text = pnf.form
                    WHERE 
                        w.verse_id = %s
                    GROUP BY
                        pn.name_id, pn.name, pn.transliteration, pn.description
                    """
                    
                    try:
                        cur.execute(name_query, (result['id'],))
                        name_data = cur.fetchall()
                        if name_data:
                            verse_data['proper_names'] = [
                                {
                                    'name': name['name'],
                                    'transliteration': name['transliteration'],
                                    'description': name['description']
                                } for name in name_data
                            ]
                    except Exception as e:
                        logger.error(f"Error fetching proper name data: {e}")
                
                # Add the processed verse to results
                results.append(verse_data)
            
            # If cross-language search is requested, search other translations
            if cross_language:
                logger.info(f"Performing cross-language search for query: {query}")
                # Define which translations to search
                cross_translations = []
                
                # Always include Hebrew and Greek in cross-language search
                if translation != 'TAHOT':
                    cross_translations.append('TAHOT')
                if translation != 'TAGNT':
                    cross_translations.append('TAGNT')
                    
                # Include KJV or ASV if not already the primary translation
                if translation not in ['KJV', 'ASV']:
                    cross_translations.append('KJV')
                
                # Search each translation
                for cross_translation in cross_translations:
                    logger.info(f"Searching translation: {cross_translation}")
                    cross_limit = max(3, limit // len(cross_translations))  # Distribute the limit
                    
                    # Execute the same search in this translation
                    cur.execute(base_query, (embedding_array, cross_translation, embedding_array, cross_limit))
                    cross_results = cur.fetchall()
                    
                    # Process results
                    for result in cross_results:
                        cross_verse = {
                            'reference': f"{result['book_name']} {result['chapter_num']}:{result['verse_num']}",
                            'text': result['verse_text'],
                            'translation': result['translation_source'],
                            'similarity': round(float(result['similarity']) * 100, 2),
                            'cross_language': True
                        }
                        
                        # Add lexical information if it's Hebrew or Greek
                        if include_lexicon:
                            is_cross_hebrew = cross_translation == 'TAHOT'
                            is_cross_greek = cross_translation == 'TAGNT'
                            
                            if is_cross_hebrew or is_cross_greek:
                                # Same lexical query logic as above
                                lexicon_table = 'hebrew_entries' if is_cross_hebrew else 'greek_entries'
                                word_table = 'hebrew_ot_words' if is_cross_hebrew else 'greek_nt_words'
                                
                                lexical_query = f"""
                                SELECT 
                                    w.word_text, 
                                    w.word_position,
                                    w.strongs_id, 
                                    w.grammar_code,
                                    l.lemma, 
                                    l.definition
                                FROM 
                                    bible.{word_table} w
                                    JOIN bible.{lexicon_table} l ON w.strongs_id = l.strongs_id
                                WHERE 
                                    w.verse_id = %s
                                ORDER BY 
                                    w.word_position
                                """
                                
                                cur.execute(lexical_query, (result['id'],))
                                lexical_data = cur.fetchall()
                                
                                cross_verse['lexical_data'] = [
                                    {
                                        'word': lex['word_text'],
                                        'position': lex['word_position'],
                                        'strongs_id': lex['strongs_id'],
                                        'grammar': lex['grammar_code'],
                                        'lemma': lex['lemma'],
                                        'definition': lex['definition']
                                    } for lex in lexical_data
                                ]
                        
                        results.append(cross_verse)
                
                # Check for Arabic verses if any Hebrew verses were found
                try:
                    hebrew_verses = [r for r in results if r.get('translation') == 'TAHOT']
                    if hebrew_verses and include_lexicon:
                        logger.info(f"Found {len(hebrew_verses)} Hebrew verses, checking for Arabic equivalents")
                        
                        # Extract reference information
                        verse_refs = []
                        for hv in hebrew_verses:
                            ref = hv['reference'].split()
                            book = ref[0]
                            chapter, verse = map(int, ref[1].split(':'))
                            verse_refs.append((book, chapter, verse))
                        
                        # Query for Arabic verses with matching references
                        for book, chapter, verse in verse_refs:
                            arabic_query = """
                            SELECT 
                                book, chapter, verse, text
                            FROM 
                                bible.arabic_verses
                            WHERE 
                                book = %s AND chapter = %s AND verse = %s
                            """
                            
                            cur.execute(arabic_query, (book, chapter, verse))
                            arabic_results = cur.fetchall()
                            
                            for ar in arabic_results:
                                results.append({
                                    'reference': f"{ar['book']} {ar['chapter']}:{ar['verse']}",
                                    'text': ar['text'],
                                    'translation': 'ARABIC',
                                    'similarity': 0,  # No direct similarity score
                                    'cross_language': True,
                                    'from_hebrew_ref': f"{book} {chapter}:{verse}"
                                })
                                logger.info(f"Added Arabic verse: {ar['book']} {ar['chapter']}:{ar['verse']}")
                except Exception as e:
                    logger.error(f"Error finding Arabic equivalents: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # Sort results by similarity
                results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
                
                # Limit results to requested count
                if len(results) > limit:
                    results = results[:limit]
        
        # Return the search results
        return jsonify({
            'query': query,
            'translation': translation,
            'cross_language': cross_language,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in comprehensive search: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Error processing search: {str(e)}',
            'results': []
        }), 500

@comprehensive_search_api.route('/theological-term-search')
def theological_term_search():
    """
    Search for theological terms across translations.
    
    Query parameters:
        term: Theological term to search
        language: Term language (hebrew, greek, english, arabic)
        include_equivalent: Include equivalent terms in other languages
    """
    # Get query parameters
    term = request.args.get('term', '')
    language = request.args.get('language', 'english').lower()
    include_equivalent = request.args.get('include_equivalent', 'true').lower() == 'true'
    limit = min(int(request.args.get('limit', 10)), 50)
    
    # Validate input
    if not term:
        return jsonify({
            'error': 'No term provided',
            'results': []
        }), 400
    
    try:
        # Map language to appropriate column for searching
        lang_column_map = {
            'hebrew': 'hebrew_term',
            'greek': 'greek_term',
            'english': 'english_term',
            'arabic': 'arabic_term'
        }
        
        search_column = lang_column_map.get(language, 'english_term')
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            # If the cross_language_terms table exists, search it first
            try:
                # Find matching theological terms
                term_query = f"""
                SELECT 
                    term_id,
                    hebrew_term,
                    greek_term,
                    english_term,
                    arabic_term,
                    theological_category
                FROM 
                    bible.cross_language_terms
                WHERE 
                    {search_column} ILIKE %s
                LIMIT 20
                """
                
                cur.execute(term_query, (f"%{term}%",))
                term_results = cur.fetchall()
                
                # If no direct match and include_equivalent is true, try Strong's ID search
                if not term_results and include_equivalent:
                    # Try to match by Strong's ID if term looks like one
                    if term.upper().startswith('H') or term.upper().startswith('G'):
                        strongs_id = term.upper()
                        
                        # Get lexicon entry for this Strong's ID
                        if strongs_id.startswith('H'):
                            lexicon_query = """
                            SELECT 
                                strongs_id, 
                                lemma, 
                                transliteration, 
                                definition
                            FROM 
                                bible.hebrew_entries
                            WHERE 
                                strongs_id = %s
                            """
                        else:
                            lexicon_query = """
                            SELECT 
                                strongs_id, 
                                lemma, 
                                transliteration, 
                                definition
                            FROM 
                                bible.greek_entries
                            WHERE 
                                strongs_id = %s
                            """
                            
                        cur.execute(lexicon_query, (strongs_id,))
                        lexicon_result = cur.fetchone()
                        
                        if lexicon_result:
                            # Create an artificial cross-language term result
                            term_results = [{
                                'term_id': None,
                                'hebrew_term': lexicon_result['lemma'] if strongs_id.startswith('H') else None,
                                'greek_term': lexicon_result['lemma'] if strongs_id.startswith('G') else None,
                                'english_term': lexicon_result['definition'].split(',')[0] if lexicon_result['definition'] else None,
                                'arabic_term': None,
                                'theological_category': 'lexicon-derived',
                                'strongs_id': strongs_id,
                                'transliteration': lexicon_result['transliteration'],
                                'definition': lexicon_result['definition']
                            }]
            except Exception as e:
                logger.error(f"Error searching cross_language_terms: {e}")
                term_results = []
            
            # Find verses containing the term
            verses_with_term = []
            
            if language == 'hebrew':
                # Search Hebrew verses
                verse_query = """
                SELECT 
                    v.id, 
                    v.book_name, 
                    v.chapter_num, 
                    v.verse_num, 
                    v.verse_text,
                    v.translation_source,
                    w.word_text,
                    w.strongs_id,
                    h.lemma,
                    h.definition
                FROM 
                    bible.verses v
                    JOIN bible.hebrew_ot_words w ON v.id = w.verse_id
                    JOIN bible.hebrew_entries h ON w.strongs_id = h.strongs_id
                WHERE 
                    (w.word_text ILIKE %s OR 
                    h.lemma ILIKE %s OR 
                    w.strongs_id = %s)
                    AND v.translation_source = 'TAHOT'
                ORDER BY 
                    v.book_name, v.chapter_num, v.verse_num
                LIMIT %s
                """
                
                strongs_id = term.upper() if term.upper().startswith('H') else ''
                cur.execute(verse_query, (f"%{term}%", f"%{term}%", strongs_id, limit))
                
            elif language == 'greek':
                # Search Greek verses
                verse_query = """
                SELECT 
                    v.id, 
                    v.book_name, 
                    v.chapter_num, 
                    v.verse_num, 
                    v.verse_text,
                    v.translation_source,
                    w.word_text,
                    w.strongs_id,
                    g.lemma,
                    g.definition
                FROM 
                    bible.verses v
                    JOIN bible.greek_nt_words w ON v.id = w.verse_id
                    JOIN bible.greek_entries g ON w.strongs_id = g.strongs_id
                WHERE 
                    (w.word_text ILIKE %s OR 
                    g.lemma ILIKE %s OR 
                    w.strongs_id = %s)
                    AND v.translation_source = 'TAGNT'
                ORDER BY 
                    v.book_name, v.chapter_num, v.verse_num
                LIMIT %s
                """
                
                strongs_id = term.upper() if term.upper().startswith('G') else ''
                cur.execute(verse_query, (f"%{term}%", f"%{term}%", strongs_id, limit))
                
            else:
                # Search English verses (KJV)
                verse_query = """
                SELECT 
                    v.id, 
                    v.book_name, 
                    v.chapter_num, 
                    v.verse_num, 
                    v.verse_text,
                    v.translation_source
                FROM 
                    bible.verses v
                WHERE 
                    v.verse_text ILIKE %s
                    AND v.translation_source = 'KJV'
                ORDER BY 
                    v.book_name, v.chapter_num, v.verse_num
                LIMIT %s
                """
                
                cur.execute(verse_query, (f"%{term}%", limit))
            
            verses_with_term = cur.fetchall()
            
            # Process the verses
            verses = []
            for verse in verses_with_term:
                verse_data = {
                    'reference': f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}",
                    'text': verse['verse_text'],
                    'translation': verse['translation_source']
                }
                
                # Add lexical information if available
                if language in ['hebrew', 'greek'] and 'strongs_id' in verse:
                    verse_data['term_info'] = {
                        'word': verse['word_text'],
                        'strongs_id': verse['strongs_id'],
                        'lemma': verse['lemma'],
                        'definition': verse['definition']
                    }
                
                verses.append(verse_data)
            
            # Get embeddings for verses to find semantically similar ones
            if verses and include_equivalent:
                # Get query text from the first verse
                query_text = verses[0]['text']
                
                # Get embedding for this verse
                query_embedding = get_embedding(query_text)
                if query_embedding:
                    embedding_array = format_vector_for_postgres(query_embedding)
                    
                    # Find semantically similar verses in other translations
                    similar_query = """
                    SELECT 
                        v.id, 
                        v.book_name, 
                        v.chapter_num, 
                        v.verse_num, 
                        v.verse_text,
                        v.translation_source,
                        1 - (e.embedding <=> %s::vector) AS similarity
                    FROM 
                        bible.verse_embeddings e
                        JOIN bible.verses v ON e.verse_id = v.id
                    WHERE 
                        v.translation_source != %s
                    ORDER BY 
                        e.embedding <=> %s::vector
                    LIMIT %s
                    """
                    
                    source_translation = verses[0]['translation']
                    cur.execute(similar_query, (embedding_array, source_translation, embedding_array, 5))
                    similar_verses = cur.fetchall()
                    
                    # Add as semantically related
                    for verse in similar_verses:
                        verses.append({
                            'reference': f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}",
                            'text': verse['verse_text'],
                            'translation': verse['translation_source'],
                            'similarity': round(float(verse['similarity']) * 100, 2),
                            'semantically_related': True
                        })
        
        # Return the results
        return jsonify({
            'term': term,
            'language': language,
            'term_info': term_results,
            'verses': verses,
            'count': len(verses)
        })
        
    except Exception as e:
        logger.error(f"Error in theological term search: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f"Error processing term search: {str(e)}",
            'results': []
        }), 500

@comprehensive_search_api.route('/name-search')
def name_search():
    """
    Search for biblical proper names and their relationships.
    
    Query parameters:
        name: Proper name to search
        include_relationships: Include related names
        relationship_type: Filter by relationship type
    """
    # Get query parameters
    name = request.args.get('name', '')
    include_relationships = request.args.get('include_relationships', 'true').lower() == 'true'
    relationship_type = request.args.get('relationship_type', '')
    limit = min(int(request.args.get('limit', 20)), 50)
    
    # Validate input
    if not name:
        return jsonify({
            'error': 'No name provided',
            'results': []
        }), 400
    
    try:
        conn = get_db_connection()
        results = {}
        
        with conn.cursor() as cur:
            # Search for names
            name_query = """
            SELECT 
                name_id,
                name,
                transliteration,
                description
            FROM 
                bible.proper_names
            WHERE 
                name ILIKE %s OR transliteration ILIKE %s
            ORDER BY name
            LIMIT %s
            """
            
            cur.execute(name_query, (f"%{name}%", f"%{name}%", limit))
            name_results = cur.fetchall()
            results['names'] = name_results
            
            # Get all forms of these names
            if name_results:
                name_ids = [n['name_id'] for n in name_results]
                name_ids_str = ",".join([f"'{nid}'" for nid in name_ids])
                
                forms_query = f"""
                SELECT 
                    name_id,
                    form,
                    transliteration,
                    language
                FROM 
                    bible.proper_name_forms
                WHERE 
                    name_id IN ({name_ids_str})
                ORDER BY name_id, form
                """
                
                cur.execute(forms_query)
                form_results = cur.fetchall()
                
                # Group forms by name_id
                name_forms = {}
                for form in form_results:
                    name_id = form['name_id']
                    if name_id not in name_forms:
                        name_forms[name_id] = []
                    name_forms[name_id].append({
                        'form': form['form'],
                        'transliteration': form['transliteration'],
                        'language': form['language']
                    })
                
                # Add forms to each name
                for name in results['names']:
                    name_id = name['name_id']
                    name['forms'] = name_forms.get(name_id, [])
                
                # Find relationships if requested
                if include_relationships:
                    relationships = []
                    
                    rel_query = f"""
                    SELECT 
                        pnr.name_id1, 
                        pnr.name_id2, 
                        pnr.relationship_type,
                        pn1.name AS name1,
                        pn2.name AS name2,
                        pn1.transliteration AS transliteration1,
                        pn2.transliteration AS transliteration2
                    FROM 
                        bible.proper_name_relationships pnr
                        JOIN bible.proper_names pn1 ON pnr.name_id1 = pn1.name_id
                        JOIN bible.proper_names pn2 ON pnr.name_id2 = pn2.name_id
                    WHERE 
                        pnr.name_id1 IN ({name_ids_str}) OR pnr.name_id2 IN ({name_ids_str})
                    """
                    
                    # Add relationship type filter if provided
                    if relationship_type:
                        rel_query += f" AND pnr.relationship_type = '{relationship_type}'"
                    
                    rel_query += " ORDER BY pnr.relationship_type, pn1.name, pn2.name"
                    
                    cur.execute(rel_query)
                    rel_results = cur.fetchall()
                    
                    for rel in rel_results:
                        relationships.append({
                            'name1': rel['name1'],
                            'name2': rel['name2'],
                            'transliteration1': rel['transliteration1'],
                            'transliteration2': rel['transliteration2'],
                            'relationship_type': rel['relationship_type']
                        })
                    
                    results['relationships'] = relationships
                
                # Find verses containing these names
                verses = []
                
                # Get all forms to search for in text
                all_forms = []
                for name_forms_list in name_forms.values():
                    all_forms.extend([f['form'] for f in name_forms_list])
                
                if all_forms:
                    # Create a query to find verses with these name forms
                    # This is an approximation - more sophisticated matching may be needed
                    verses_query = """
                    SELECT DISTINCT
                        v.id,
                        v.book_name,
                        v.chapter_num,
                        v.verse_num,
                        v.verse_text,
                        v.translation_source,
                        pn.name_id,
                        pn.name,
                        pn.transliteration
                    FROM
                        bible.verses v
                        JOIN bible.hebrew_ot_words w ON v.id = w.verse_id
                        JOIN bible.proper_name_forms pnf ON w.word_text = pnf.form
                        JOIN bible.proper_names pn ON pnf.name_id = pn.name_id
                    WHERE
                        pn.name_id IN ({})
                    ORDER BY
                        v.book_name, v.chapter_num, v.verse_num
                    LIMIT 50
                    """.format(name_ids_str)
                    
                    try:
                        cur.execute(verses_query)
                        verse_results = cur.fetchall()
                        
                        for verse in verse_results:
                            verses.append({
                                'reference': f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}",
                                'text': verse['verse_text'],
                                'translation': verse['translation_source'],
                                'name': verse['name'],
                                'transliteration': verse['transliteration']
                            })
                    except Exception as e:
                        logger.error(f"Error finding verses with proper names: {e}")
                
                results['verses'] = verses
        
        # Return results
        return jsonify({
            'query': name,
            'count': len(results.get('names', [])),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in name search: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f"Error processing name search: {str(e)}",
            'results': []
        }), 500

@comprehensive_search_api.route('/health')
def health_check():
    """API health check endpoint."""
    try:
        # Check database connection
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        
        # Check LM Studio API
        response = requests.get(f"{LM_STUDIO_API_URL}/v1/models", timeout=5)
        if response.status_code != 200:
            return jsonify({
                'status': 'degraded',
                'database': 'ok',
                'embedding_api': 'error',
                'message': f'LM Studio API error: {response.status_code}'
            }), 500
        
        return jsonify({
            'status': 'ok',
            'database': 'ok',
            'embedding_api': 'ok'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 