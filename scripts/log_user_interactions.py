#!/usr/bin/env python3
"""
User Interaction Logger for DSPy Training

This script logs user questions and AI solutions as DSPy training data.
It captures API requests, web interactions, and direct user questions
to build a comprehensive dataset for training language models to assist
with Bible research, theological analysis, and API/web interface usage.

Usage:
  python scripts/log_user_interactions.py [--reset]
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import psycopg
from psycopg.rows import dict_row
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/user_interactions.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data/processed/dspy_training_data')
INTERACTIONS_FILE = DATA_DIR / 'user_interactions_dataset.jsonl'
PROBLEMS_SOLUTIONS_FILE = DATA_DIR / 'problem_solution_dataset.jsonl'
LOG_DIR = Path('logs')

def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    return DATA_DIR

def get_db_connection():
    """Get a database connection using environment variables."""
    from dotenv import load_dotenv
    load_dotenv()
    
    conn = psycopg.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        dbname=os.environ.get('DB_NAME', 'bible_db'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', '')
    )
    return conn

def load_existing_data(file_path):
    """Load existing data from a JSONL file."""
    data = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                data.append(json.loads(line))
        logger.info(f"Loaded {len(data)} existing entries from {file_path}")
    return data

def save_jsonl(data, file_path):
    """Save data to a JSONL file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        # Write header with metadata as comment
        f.write(f"// DSPy training data from user interactions\n")
        f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Write each data item as a JSON line
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(data)} examples to {file_path}")
    return file_path

def log_api_interaction(endpoint, method, params, response, success):
    """Log an API interaction for training data."""
    interactions = load_existing_data(INTERACTIONS_FILE)
    
    # Create new interaction entry
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "type": "api_interaction",
        "endpoint": endpoint,
        "method": method,
        "parameters": params,
        "response": response,
        "success": success,
        "formatted_query": f"Make an API call to {endpoint} with {method}",
        "formatted_solution": f"API response: {json.dumps(response) if success else 'Error'}"
    }
    
    interactions.append(interaction)
    save_jsonl(interactions, INTERACTIONS_FILE)
    logger.info(f"Logged API interaction for endpoint: {endpoint}")
    
    return interaction

def log_web_interaction(route, query_params, response_type):
    """Log a web interface interaction for training data."""
    interactions = load_existing_data(INTERACTIONS_FILE)
    
    # Create new interaction entry
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "type": "web_interaction",
        "route": route,
        "query_params": query_params,
        "response_type": response_type,
        "formatted_query": f"How do I access {route} with parameters {json.dumps(query_params)}?",
        "formatted_solution": f"Visit {route} and provide these parameters: {json.dumps(query_params)}"
    }
    
    interactions.append(interaction)
    save_jsonl(interactions, INTERACTIONS_FILE)
    logger.info(f"Logged web interaction for route: {route}")
    
    return interaction

def log_question_answer(question, answer, context=None, category=None):
    """Log a user question and AI answer for training data."""
    interactions = load_existing_data(INTERACTIONS_FILE)
    
    # Create new QA entry
    qa_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "question_answer",
        "question": question,
        "answer": answer,
        "context": context,
        "category": category or "general",
        "formatted_query": question,
        "formatted_solution": answer
    }
    
    interactions.append(qa_entry)
    save_jsonl(interactions, INTERACTIONS_FILE)
    logger.info(f"Logged QA pair: {question[:50]}...")
    
    return qa_entry

def log_problem_solution(problem, solution, code_example=None, diagnostic_steps=None):
    """Log a problem and its solution for training data."""
    problems = load_existing_data(PROBLEMS_SOLUTIONS_FILE)
    
    # Create new problem-solution entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "problem": problem,
        "solution": solution,
        "code_example": code_example,
        "diagnostic_steps": diagnostic_steps or [],
        "metadata": {
            "issue_type": "user_reported",
            "has_code_solution": code_example is not None
        }
    }
    
    problems.append(entry)
    save_jsonl(problems, PROBLEMS_SOLUTIONS_FILE)
    logger.info(f"Logged problem-solution: {problem[:50]}...")
    
    return entry

def reset_data():
    """Reset all interaction logs (for testing)."""
    if INTERACTIONS_FILE.exists():
        os.remove(INTERACTIONS_FILE)
    if PROBLEMS_SOLUTIONS_FILE.exists():
        os.remove(PROBLEMS_SOLUTIONS_FILE)
    logger.info("Reset all interaction logs")

def main():
    """Main function for the script."""
    parser = argparse.ArgumentParser(description="Log user interactions for DSPy training")
    parser.add_argument("--reset", action="store_true", help="Reset all interaction logs")
    args = parser.parse_args()
    
    try:
        # Create necessary directories
        ensure_directories()
        
        if args.reset:
            reset_data()
            return
        
        # Example of logging interactions
        log_api_interaction(
            endpoint="/api/lexicon/hebrew/H7225",
            method="GET",
            params={},
            response={"strongs_id": "H7225", "lemma": "רֵאשִׁית", "transliteration": "rēʾšîṯ", "gloss": "beginning, chief"},
            success=True
        )
        
        log_web_interaction(
            route="/bible/John/3/16",
            query_params={"show_translation": "KJV"},
            response_type="verse_display"
        )
        
        log_question_answer(
            question="What is the meaning of Elohim in Hebrew?",
            answer="Elohim (אֱלֹהִים) is the Hebrew word for 'God' or 'gods'. It's the plural form of Eloah, but is often used with singular verbs when referring to the one true God of Israel.",
            category="theological_term"
        )
        
        log_problem_solution(
            problem="API returns 404 for /api/lexicon/greek/G25",
            solution="The Greek lexicon endpoint needs to be properly implemented. The Hebrew endpoint works but Greek is missing.",
            code_example="""
# Implementation for Greek lexicon API
@app.route('/api/lexicon/greek/<strongs_id>', methods=['GET'])
def get_greek_lexicon_entry(strongs_id):
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM bible.greek_entries WHERE strongs_id = %s",
                (strongs_id,)
            )
            entry = cur.fetchone()
            
        if entry:
            return jsonify(entry)
        else:
            return jsonify({"error": f"No entry found for Strong's ID {strongs_id}"}), 404
    finally:
        conn.close()
""",
            diagnostic_steps=[
                "Checked API server logs - no Greek lexicon endpoint implemented",
                "Verified the database has Greek entries table",
                "Confirmed Hebrew endpoint works correctly"
            ]
        )
        
        logger.info("Successfully logged example interactions")
        
    except Exception as e:
        logger.error(f"Error in user interaction logging: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 