#!/usr/bin/env python3
"""
Vector Search Demo Application

This is a simple web application that demonstrates the vector search capabilities
of the BibleScholarProject. It allows users to search for Bible verses semantically
using pgvector in PostgreSQL.

The demo includes:
- Basic vector search with relevance scoring
- Cross-translation comparison
- Search for verses similar to a reference verse
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
import numpy as np
import requests
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/vector_search_demo.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")

# Database connection settings
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

# Create Flask app
app = Flask(__name__)

# Add templates directory
app.template_folder = "templates"

def get_db_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            row_factory=dict_row
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

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
            f"{LM_STUDIO_API_URL}/embeddings",
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

def validate_translation(translation):
    """Validate and normalize translation code."""
    # Get list of valid translations
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT translation_source FROM bible.verse_embeddings")
        valid_translations = [row['translation_source'] for row in cursor.fetchall()]
        conn.close()
        
        # Check if the provided translation is valid
        if translation in valid_translations:
            return translation
        
        # If not valid, normalize and check again
        normalized = translation.upper()
        if normalized in valid_translations:
            return normalized
        
        # Return default translation if not found
        logger.warning(f"Invalid translation: {translation}, using KJV")
        return "KJV"
    except Exception as e:
        logger.error(f"Error validating translation: {e}")
        return "KJV"

def search_similar_verses(verse_reference, translation="KJV", limit=10):
    """
    Search for verses similar to the specified verse reference.
    
    Args:
        verse_reference: Reference in format "Book Chapter:Verse" (e.g., "John 3:16")
        translation: Bible translation
        limit: Maximum number of results
        
    Returns:
        List of similar verses
    """
    try:
        # Parse the verse reference
        parts = verse_reference.strip().split()
        if len(parts) < 2:
            logger.error(f"Invalid verse reference format: {verse_reference}")
            return []
        
        book_name = " ".join(parts[:-1])
        chapter_verse = parts[-1].split(":")
        
        if len(chapter_verse) != 2:
            logger.error(f"Invalid verse reference format: {verse_reference}")
            return []
        
        chapter_num = int(chapter_verse[0])
        verse_num = int(chapter_verse[1])
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the embedding for the reference verse
        query = """
        SELECT ve.embedding
        FROM bible.verses v
        JOIN bible.books b ON v.book_id = b.book_id
        JOIN bible.verse_embeddings ve ON v.verse_id = ve.verse_id
        WHERE b.book_name = %s
        AND v.chapter_num = %s
        AND v.verse_num = %s
        AND ve.translation_source = %s
        LIMIT 1
        """
        
        cursor.execute(query, (book_name, chapter_num, verse_num, translation))
        result = cursor.fetchone()
        
        if not result:
            logger.error(f"Verse not found: {verse_reference}")
            conn.close()
            return []
        
        # Get the embedding vector
        embedding = result['embedding']
        
        # Search for similar verses
        search_query = """
        SELECT v.verse_id, b.book_name, v.chapter_num, v.verse_num, 
               v.verse_text, ve.translation_source,
               1 - (ve.embedding <=> %s) as similarity
        FROM bible.verses v
        JOIN bible.books b ON v.book_id = b.book_id
        JOIN bible.verse_embeddings ve ON v.verse_id = ve.verse_id
        WHERE ve.translation_source = %s
        AND NOT (b.book_name = %s AND v.chapter_num = %s AND v.verse_num = %s)
        ORDER BY ve.embedding <=> %s
        LIMIT %s
        """
        
        cursor.execute(search_query, (embedding, translation, book_name, chapter_num, verse_num, embedding, limit))
        results = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error searching for similar verses: {e}")
        return []

def compare_translations(verse_reference, translations=None, limit=5):
    """
    Compare translations of a specific verse using vector similarity.
    
    Args:
        verse_reference: Reference in format "Book Chapter:Verse" (e.g., "John 3:16")
        translations: List of translation codes (e.g., ["KJV", "ASV"])
        limit: Maximum number of translations to compare
        
    Returns:
        Dictionary with verse information and comparisons
    """
    try:
        # Set default translations if not provided
        if not translations:
            translations = ["KJV", "ASV", "WEB"]
        
        # Parse the verse reference
        parts = verse_reference.strip().split()
        if len(parts) < 2:
            logger.error(f"Invalid verse reference format: {verse_reference}")
            return {}
        
        book_name = " ".join(parts[:-1])
        chapter_verse = parts[-1].split(":")
        
        if len(chapter_verse) != 2:
            logger.error(f"Invalid verse reference format: {verse_reference}")
            return {}
        
        chapter_num = int(chapter_verse[0])
        verse_num = int(chapter_verse[1])
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all available translations for this verse
        query = """
        SELECT v.verse_id, b.book_name, v.chapter_num, v.verse_num, 
               v.verse_text, ve.translation_source, ve.embedding
        FROM bible.verses v
        JOIN bible.books b ON v.book_id = b.book_id
        JOIN bible.verse_embeddings ve ON v.verse_id = ve.verse_id
        WHERE b.book_name = %s
        AND v.chapter_num = %s
        AND v.verse_num = %s
        ORDER BY ve.translation_source
        """
        
        cursor.execute(query, (book_name, chapter_num, verse_num))
        results = cursor.fetchall()
        
        if not results:
            logger.error(f"Verse not found: {verse_reference}")
            conn.close()
            return {}
        
        # Convert to list of dictionaries
        verses = [dict(row) for row in results]
        
        # Filter to requested translations if specified
        if translations:
            verses = [v for v in verses if v['translation_source'] in translations]
        
        # Limit the number of translations
        if len(verses) > limit:
            verses = verses[:limit]
        
        # Calculate similarity between translations
        similarities = []
        for i, verse1 in enumerate(verses):
            for j, verse2 in enumerate(verses):
                if i >= j:
                    continue
                
                # Calculate cosine similarity manually
                embedding1 = verse1['embedding']
                embedding2 = verse2['embedding']
                
                # Calculate similarity
                similarity = 1 - np.arccos(
                    np.dot(embedding1, embedding2) / 
                    (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
                ) / np.pi
                
                similarities.append({
                    'translation1': verse1['translation_source'],
                    'translation2': verse2['translation_source'],
                    'similarity': float(similarity)
                })
        
        # Close the connection
        conn.close()
        
        # Prepare the result
        result = {
            'reference': verse_reference,
            'verses': [
                {
                    'translation': v['translation_source'],
                    'text': v['verse_text']
                }
                for v in verses
            ],
            'similarities': similarities
        }
        
        return result
    except Exception as e:
        logger.error(f"Error comparing translations: {e}")
        return {}

def vector_search(query, translation="KJV", limit=10):
    """
    Perform vector search for Bible verses.
    
    Args:
        query: Search query
        translation: Bible translation to search
        limit: Maximum number of results
        
    Returns:
        List of verse dictionaries
    """
    try:
        # Get embedding for the query
        embedding = get_embedding(query)
        if not embedding:
            return []
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the search query
        search_query = """
        SELECT v.verse_id, b.book_name, v.chapter_num, v.verse_num, 
               v.verse_text, ve.translation_source,
               1 - (ve.embedding <=> %s::vector) as similarity
        FROM bible.verses v
        JOIN bible.books b ON v.book_id = b.book_id
        JOIN bible.verse_embeddings ve ON v.verse_id = ve.verse_id
        WHERE ve.translation_source = %s
        ORDER BY ve.embedding <=> %s::vector
        LIMIT %s
        """
        
        cursor.execute(search_query, (embedding_str, translation, embedding_str, limit))
        results = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return []

# Flask routes
@app.route("/")
def index():
    """Render the main demo page."""
    return render_template("vector_search_demo.html")

@app.route("/search/vector")
def search_api():
    """API endpoint for vector search."""
    try:
        query = request.args.get("q", "")
        translation = request.args.get("translation", "KJV")
        limit = int(request.args.get("limit", 10))
        
        # Validate translation
        translation = validate_translation(translation)
        
        # Perform the search
        results = vector_search(query, translation, limit)
        
        # Return JSON response
        return jsonify({
            "query": query,
            "translation": translation,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/search/similar")
def similar_verses_api():
    """API endpoint for finding similar verses."""
    try:
        reference = request.args.get("reference", "")
        translation = request.args.get("translation", "KJV")
        limit = int(request.args.get("limit", 10))
        
        # Validate inputs
        if not reference:
            return jsonify({"error": "No verse reference provided"}), 400
        
        translation = validate_translation(translation)
        
        # Perform the search
        results = search_similar_verses(reference, translation, limit)
        
        # Return JSON response
        return jsonify({
            "reference": reference,
            "translation": translation,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error in similar verses API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/compare/translations")
def compare_translations_api():
    """API endpoint for comparing translations."""
    try:
        reference = request.args.get("reference", "")
        translations_param = request.args.get("translations", "KJV,ASV,WEB")
        
        # Validate inputs
        if not reference:
            return jsonify({"error": "No verse reference provided"}), 400
        
        # Parse translations
        translations = [t.strip() for t in translations_param.split(",")]
        
        # Perform the comparison
        result = compare_translations(reference, translations)
        
        # Return JSON response
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in compare translations API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/translations")
def list_translations():
    """API endpoint for listing available translations."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT translation_source FROM bible.verse_embeddings ORDER BY translation_source")
        translations = [row['translation_source'] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "translations": translations
        })
    except Exception as e:
        logger.error(f"Error listing translations: {e}")
        return jsonify({"error": str(e)}), 500

# For direct execution
if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Ensure the templates directory exists
    os.makedirs("templates", exist_ok=True)
    
    # Create a simple HTML template if it doesn't exist
    template_path = os.path.join(app.template_folder, "vector_search_demo.html")
    if not os.path.exists(template_path):
        with open(template_path, "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Bible Vector Search Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .search-box {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .results {
            margin-top: 20px;
        }
        .verse {
            padding: 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .verse-ref {
            font-weight: bold;
            color: #555;
        }
        .verse-text {
            margin-top: 5px;
        }
        .score {
            color: #888;
            font-size: 0.9em;
        }
        input[type="text"] {
            width: 70%;
            padding: 8px;
        }
        select {
            padding: 8px;
        }
        button {
            padding: 8px 15px;
            background-color: #4285f4;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        button:hover {
            background-color: #3367d6;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid #ddd;
            background-color: #f8f8f8;
            margin-right: 5px;
        }
        .tab.active {
            background-color: #fff;
            border-bottom: 1px solid #fff;
        }
        .tab-content {
            display: none;
            padding: 20px;
            border: 1px solid #ddd;
            margin-top: -1px;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <h1>Bible Vector Search Demo</h1>
    <p>This demo uses pgvector in PostgreSQL to perform semantic search on Bible verses.</p>
    
    <div class="tabs">
        <div class="tab active" onclick="openTab(event, 'search-tab')">Vector Search</div>
        <div class="tab" onclick="openTab(event, 'similar-tab')">Similar Verses</div>
        <div class="tab" onclick="openTab(event, 'compare-tab')">Compare Translations</div>
    </div>
    
    <div id="search-tab" class="tab-content active">
        <div class="search-box">
            <h2>Search for verses semantically</h2>
            <input type="text" id="search-query" placeholder="Enter your search query">
            <select id="search-translation">
                <option value="KJV">KJV</option>
                <option value="ASV">ASV</option>
                <option value="WEB">WEB</option>
            </select>
            <button onclick="performSearch()">Search</button>
        </div>
        
        <div id="search-results" class="results"></div>
    </div>
    
    <div id="similar-tab" class="tab-content">
        <div class="search-box">
            <h2>Find similar verses</h2>
            <input type="text" id="verse-reference" placeholder="Enter verse reference (e.g., John 3:16)">
            <select id="similar-translation">
                <option value="KJV">KJV</option>
                <option value="ASV">ASV</option>
                <option value="WEB">WEB</option>
            </select>
            <button onclick="findSimilarVerses()">Find Similar</button>
        </div>
        
        <div id="similar-results" class="results"></div>
    </div>
    
    <div id="compare-tab" class="tab-content">
        <div class="search-box">
            <h2>Compare translations</h2>
            <input type="text" id="compare-reference" placeholder="Enter verse reference (e.g., John 3:16)">
            <button onclick="compareTranslations()">Compare</button>
        </div>
        
        <div id="compare-results" class="results"></div>
    </div>
    
    <script>
        // Load available translations
        fetch('/translations')
            .then(response => response.json())
            .then(data => {
                const translations = data.translations;
                const searchSelect = document.getElementById('search-translation');
                const similarSelect = document.getElementById('similar-translation');
                
                // Clear existing options
                searchSelect.innerHTML = '';
                similarSelect.innerHTML = '';
                
                // Add translations to selects
                translations.forEach(translation => {
                    searchSelect.add(new Option(translation, translation));
                    similarSelect.add(new Option(translation, translation));
                });
            })
            .catch(error => console.error('Error loading translations:', error));
        
        function openTab(evt, tabName) {
            // Hide all tab contents
            const tabContents = document.getElementsByClassName('tab-content');
            for (let i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // Remove active class from tabs
            const tabs = document.getElementsByClassName('tab');
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Show the selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to the clicked tab
            evt.currentTarget.classList.add('active');
        }
        
        function performSearch() {
            const query = document.getElementById('search-query').value;
            const translation = document.getElementById('search-translation').value;
            
            if (!query) {
                alert('Please enter a search query');
                return;
            }
            
            // Display loading message
            document.getElementById('search-results').innerHTML = '<p>Searching...</p>';
            
            // Perform the search
            fetch(`/search/vector?q=${encodeURIComponent(query)}&translation=${translation}&limit=10`)
                .then(response => response.json())
                .then(data => {
                    // Display results
                    const resultsDiv = document.getElementById('search-results');
                    
                    if (data.results && data.results.length > 0) {
                        let html = `<h3>Search results for: "${data.query}"</h3>`;
                        
                        data.results.forEach(verse => {
                            const reference = `${verse.book_name} ${verse.chapter_num}:${verse.verse_num}`;
                            const similarity = (verse.similarity * 100).toFixed(2);
                            
                            html += `
                                <div class="verse">
                                    <div class="verse-ref">${reference}</div>
                                    <div class="verse-text">${verse.verse_text}</div>
                                    <div class="score">Similarity: ${similarity}%</div>
                                </div>
                            `;
                        });
                        
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = '<p>No results found.</p>';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    document.getElementById('search-results').innerHTML = '<p>Error performing search.</p>';
                });
        }
        
        function findSimilarVerses() {
            const reference = document.getElementById('verse-reference').value;
            const translation = document.getElementById('similar-translation').value;
            
            if (!reference) {
                alert('Please enter a verse reference');
                return;
            }
            
            // Display loading message
            document.getElementById('similar-results').innerHTML = '<p>Searching...</p>';
            
            // Perform the search
            fetch(`/search/similar?reference=${encodeURIComponent(reference)}&translation=${translation}&limit=10`)
                .then(response => response.json())
                .then(data => {
                    // Display results
                    const resultsDiv = document.getElementById('similar-results');
                    
                    if (data.results && data.results.length > 0) {
                        let html = `<h3>Verses similar to: "${data.reference}"</h3>`;
                        
                        data.results.forEach(verse => {
                            const reference = `${verse.book_name} ${verse.chapter_num}:${verse.verse_num}`;
                            const similarity = (verse.similarity * 100).toFixed(2);
                            
                            html += `
                                <div class="verse">
                                    <div class="verse-ref">${reference}</div>
                                    <div class="verse-text">${verse.verse_text}</div>
                                    <div class="score">Similarity: ${similarity}%</div>
                                </div>
                            `;
                        });
                        
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = '<p>No similar verses found.</p>';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    document.getElementById('similar-results').innerHTML = '<p>Error finding similar verses.</p>';
                });
        }
        
        function compareTranslations() {
            const reference = document.getElementById('compare-reference').value;
            
            if (!reference) {
                alert('Please enter a verse reference');
                return;
            }
            
            // Display loading message
            document.getElementById('compare-results').innerHTML = '<p>Comparing...</p>';
            
            // Perform the comparison
            fetch(`/compare/translations?reference=${encodeURIComponent(reference)}`)
                .then(response => response.json())
                .then(data => {
                    // Display results
                    const resultsDiv = document.getElementById('compare-results');
                    
                    if (data.verses && data.verses.length > 0) {
                        let html = `<h3>Translations of: "${data.reference}"</h3>`;
                        
                        // Display verses
                        html += '<div class="verses">';
                        data.verses.forEach(verse => {
                            html += `
                                <div class="verse">
                                    <div class="verse-ref">${verse.translation}</div>
                                    <div class="verse-text">${verse.text}</div>
                                </div>
                            `;
                        });
                        html += '</div>';
                        
                        // Display similarities
                        if (data.similarities && data.similarities.length > 0) {
                            html += '<h3>Translation Similarities</h3>';
                            html += '<div class="similarities">';
                            
                            data.similarities.forEach(similarity => {
                                const similarityPercent = (similarity.similarity * 100).toFixed(2);
                                html += `
                                    <div class="similarity">
                                        <span>${similarity.translation1} ↔ ${similarity.translation2}: ${similarityPercent}%</span>
                                    </div>
                                `;
                            });
                            
                            html += '</div>';
                        }
                        
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = '<p>No translations found for this verse.</p>';
                    }
                })
                .catch(error => {
                    console.error('Comparison error:', error);
                    document.getElementById('compare-results').innerHTML = '<p>Error comparing translations.</p>';
                });
        }
        
        // Add event listeners for enter key
        document.getElementById('search-query').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                performSearch();
            }
        });
        
        document.getElementById('verse-reference').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                findSimilarVerses();
            }
        });
        
        document.getElementById('compare-reference').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                compareTranslations();
            }
        });
    </script>
</body>
</html>
            """)
        logger.info(f"Created default template at {template_path}")
    
    # Run the application
    app.run(debug=True, port=5050) 