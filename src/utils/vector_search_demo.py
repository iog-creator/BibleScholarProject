#!/usr/bin/env python3
"""
Simple demo Flask app for pgvector search.

This minimal app:
1. Provides a web interface for searching Bible verses with pgvector
2. Shows the power of semantic search over traditional keyword search
3. Demonstrates the integration of LM Studio embeddings with PostgreSQL

Usage:
    python -m src.utils.vector_search_demo

Then open http://127.0.0.1:5050 in your browser.
"""

import os
import logging
import requests
from flask import Flask, render_template, request, jsonify
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234")
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0:2"

# Initialize Flask app
app = Flask(__name__, template_folder="../../templates")

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

def get_embedding(text):
    """
    Get embedding vector for text using LM Studio API.
    
    Args:
        text: Text to encode
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        response = requests.post(
            f"{LM_STUDIO_API_URL}/v1/embeddings",
            headers={"Content-Type": "application/json"},
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Error from LM Studio API: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
            # Ensure all values in the embedding are floats
            embedding = [float(val) for val in data["data"][0]["embedding"]]
            return embedding
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting embedding from LM Studio: {e}")
        return None

def search_verses(query, translation="KJV", limit=10):
    """
    Search for verses similar to the query using vector similarity.
    
    Args:
        query: Text query
        translation: Bible translation to search
        limit: Number of results to return
        
    Returns:
        List of similar verses
    """
    # Get query embedding
    logger.info(f"Getting embedding for query: '{query}' for translation: '{translation}'")
    query_embedding = get_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for query")
        return []
    
    # Format the embedding array in PostgreSQL syntax
    embedding_array = "["
    for i, value in enumerate(query_embedding):
        if i > 0:
            embedding_array += ","
        embedding_array += str(value)
    embedding_array += "]"
    
    # Output statistics for debugging
    logger.info(f"Searching for verses similar to: '{query}' in translation: '{translation}'")
    
    # Search for similar verses
    conn = get_db_connection()
    try:
        # Get count first to verify query works
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT COUNT(*) 
                    FROM bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                    WHERE v.translation_source = %s
                    """,
                    (translation,)
                )
                count_result = cur.fetchone()
                verse_count = count_result["count"] if count_result else 0
                logger.info(f"Found {verse_count} verses in {translation} translation")
                
                if verse_count == 0:
                    logger.warning(f"No verses found for translation: {translation}")
                    return []
                
                # Use a simpler direct query structure for better compatibility
                embedding_query = """
                SELECT 
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
                
                cur.execute(embedding_query, (embedding_array, translation, embedding_array, limit))
                results = cur.fetchall()
                
                logger.info(f"Found {len(results)} similar verses in {translation}")
                
                # Format results for display
                formatted_results = []
                for r in results:
                    formatted_results.append({
                        'reference': f"{r['book_name']} {r['chapter_num']}:{r['verse_num']}",
                        'text': r['verse_text'],
                        'translation': r['translation_source'],
                        'similarity': round(float(r['similarity']) * 100, 2)
                    })
                    
                return formatted_results
            except Exception as e:
                logger.error(f"Error in vector search query: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
    finally:
        conn.close()

def search_verses_keyword(query, translation="KJV", limit=10):
    """
    Search for verses using traditional keyword search.
    
    Args:
        query: Text query
        translation: Bible translation to search
        limit: Number of results to return
        
    Returns:
        List of matching verses
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    book_name, 
                    chapter_num, 
                    verse_num, 
                    verse_text,
                    translation_source
                FROM 
                    bible.verses
                WHERE 
                    translation_source = %s
                    AND verse_text ILIKE %s
                LIMIT %s
                """,
                (translation, f'%{query}%', limit)
            )
            results = cur.fetchall()
            
            # Format results for display
            formatted_results = []
            for r in results:
                formatted_results.append({
                    'reference': f"{r['book_name']} {r['chapter_num']}:{r['verse_num']}",
                    'text': r['verse_text'],
                    'translation': r['translation_source']
                })
                
            return formatted_results
    except Exception as e:
        logger.error(f"Error searching verses by keyword: {e}")
        return []
    finally:
        conn.close()

@app.route('/')
def index():
    """Home page with search form."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bible Vector Search Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; max-width: 1200px; margin: 0 auto; }
            .container { display: flex; flex-direction: column; gap: 20px; }
            .search-form { background: #f5f5f5; padding: 20px; border-radius: 5px; }
            .results { display: flex; gap: 20px; }
            .vector-results, .keyword-results { flex: 1; background: #f9f9f9; padding: 20px; border-radius: 5px; }
            .verse { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .reference { font-weight: bold; }
            .similarity { color: #0066cc; font-size: 0.9em; }
            h1, h2 { color: #333; }
            input[type="text"] { width: 60%; padding: 8px; }
            button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            select { padding: 8px; }
            .translation-note { font-size: 0.9em; color: #666; margin-top: 5px; display: none; }
            .note-tahot, .note-tagnt { color: #d9534f; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Bible Vector Search Demo</h1>
            <p>Compare semantic search (using pgvector) with traditional keyword search</p>
            
            <div class="search-form">
                <form id="searchForm">
                    <input type="text" id="query" name="q" placeholder="Enter a concept, idea, or theme..." required>
                    <select id="translation" name="translation">
                        <option value="KJV">King James Version</option>
                        <option value="ASV">American Standard Version</option>
                        <option value="TAHOT">Tagged Hebrew Old Testament</option>
                        <option value="TAGNT">Tagged Greek New Testament</option>
                        <option value="ESV">English Standard Version</option>
                    </select>
                    <button type="submit">Search</button>
                    <div id="translationNote" class="translation-note">
                        <div class="note-general">Note: For best results, use the natural language of the translation.</div>
                        <div class="note-tahot">TAHOT: For Hebrew text, try queries using Hebrew characters (e.g., "בְּרֵאשִׁ֖ית")</div>
                        <div class="note-tagnt">TAGNT: For Greek text, try queries using Greek characters</div>
                    </div>
                </form>
            </div>
            
            <div class="results">
                <div class="vector-results">
                    <h2>Semantic Search Results</h2>
                    <div id="vectorResults"></div>
                </div>
                
                <div class="keyword-results">
                    <h2>Keyword Search Results</h2>
                    <div id="keywordResults"></div>
                </div>
            </div>
        </div>
        
        <script>
            // Show translation note based on selection
            document.getElementById('translation').addEventListener('change', function() {
                const translationNote = document.getElementById('translationNote');
                const selectedValue = this.value;
                
                // Show/hide notes
                translationNote.style.display = 'block';
                
                // Hide all specific notes first
                document.querySelector('.note-tahot').style.display = 'none';
                document.querySelector('.note-tagnt').style.display = 'none';
                
                // Show specific notes based on selection
                if (selectedValue === 'TAHOT') {
                    document.querySelector('.note-tahot').style.display = 'block';
                }
                else if (selectedValue === 'TAGNT') {
                    document.querySelector('.note-tagnt').style.display = 'block';
                }
                else if (selectedValue === 'KJV' || selectedValue === 'ASV' || selectedValue === 'ESV') {
                    translationNote.style.display = 'none';
                }
            });

            document.getElementById('searchForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const query = document.getElementById('query').value;
                const translation = document.getElementById('translation').value;
                
                document.getElementById('vectorResults').innerHTML = 'Searching...';
                document.getElementById('keywordResults').innerHTML = 'Searching...';
                
                // Vector search
                fetch(`/search/vector?q=${encodeURIComponent(query)}&translation=${translation}`)
                    .then(response => response.json())
                    .then(data => {
                        const resultsDiv = document.getElementById('vectorResults');
                        if (data.results.length === 0) {
                            resultsDiv.innerHTML = '<p>No results found</p>';
                            if (translation === 'TAHOT') {
                                resultsDiv.innerHTML += '<p class="note-tahot">Try searching with Hebrew text for TAHOT translation.</p>';
                            }
                            else if (translation === 'TAGNT') {
                                resultsDiv.innerHTML += '<p class="note-tagnt">Try searching with Greek text for TAGNT translation.</p>';
                            }
                        } else {
                            resultsDiv.innerHTML = data.results.map(verse => `
                                <div class="verse">
                                    <div class="reference">${verse.reference}</div>
                                    <div class="text">${verse.text}</div>
                                    <div class="similarity">Similarity: ${verse.similarity}%</div>
                                </div>
                            `).join('');
                        }
                    });
                
                // Keyword search
                fetch(`/search/keyword?q=${encodeURIComponent(query)}&translation=${translation}`)
                    .then(response => response.json())
                    .then(data => {
                        const resultsDiv = document.getElementById('keywordResults');
                        if (data.results.length === 0) {
                            resultsDiv.innerHTML = '<p>No results found</p>';
                        } else {
                            resultsDiv.innerHTML = data.results.map(verse => `
                                <div class="verse">
                                    <div class="reference">${verse.reference}</div>
                                    <div class="text">${verse.text}</div>
                                </div>
                            `).join('');
                        }
                    });
            });
        </script>
    </body>
    </html>
    """

@app.route('/search/vector')
def vector_search():
    """API endpoint for vector search."""
    query = request.args.get('q', '')
    translation = request.args.get('translation', 'KJV')
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query:
        return jsonify({
            'error': 'No search query provided',
            'results': []
        })
    
    results = search_verses(query, translation, limit)
    
    return jsonify({
        'query': query,
        'translation': translation,
        'results': results
    })

@app.route('/search/keyword')
def keyword_search():
    """API endpoint for keyword search."""
    query = request.args.get('q', '')
    translation = request.args.get('translation', 'KJV')
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query:
        return jsonify({
            'error': 'No search query provided',
            'results': []
        })
    
    results = search_verses_keyword(query, translation, limit)
    
    return jsonify({
        'query': query,
        'translation': translation,
        'results': results
    })

if __name__ == "__main__":
    app.run(debug=True, port=5050) 