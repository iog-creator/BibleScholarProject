#!/usr/bin/env python3
"""
DSPy Training Data Enhancement Script

This script enhances the existing DSPy training data by:
1. Adding more web API examples based on actual API endpoints
2. Improving the quality of theological term examples
3. Adding UI interaction examples with the web interface
4. Fixing formatting issues in existing examples
5. Adding more examples with problems/solutions format

Usage:
  python scripts/enhance_dspy_training.py

This complements the automatic collection system by adding specialized examples
that wouldn't be automatically generated from the database.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/dspy_enhancement.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data/processed/dspy_training_data')

def ensure_directory():
    """Ensure output directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR

def load_jsonl_file(filename):
    """Load data from a JSONL file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        logger.warning(f"File {filepath} does not exist.")
        return []
        
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            data.append(json.loads(line))
    
    logger.info(f"Loaded {len(data)} examples from {filepath}")
    return data

def save_jsonl_file(data, filename):
    """Save data to a JSONL file."""
    filepath = DATA_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header with metadata as comment
        f.write(f"// DSPy training data for {filename.split('.')[0]}\n")
        f.write(f"// Enhanced on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Write each data item as a JSON line
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(data)} examples to {filepath}")
    return filepath

def enhance_api_examples():
    """Enhance API examples based on actual API endpoints."""
    # Load existing examples
    web_examples = load_jsonl_file('web_interaction_dataset.jsonl')
    
    # New examples based on actual API endpoints
    new_examples = [
        {
            "query": "Get the Hebrew lexicon entry for bereshit (H7225)",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/lexicon/hebrew/H7225",
                "method": "GET"
            },
            "expected_response_format": {
                "strongs_id": "H7225",
                "lemma": "רֵאשִׁית",
                "transliteration": "rēʾšîṯ",
                "gloss": "beginning, chief"
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "lexicon",
                "difficulty": "basic"
            }
        },
        {
            "query": "Search for Hebrew words related to love",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/lexicon/search",
                "method": "GET",
                "query_params": {"q": "love"}
            },
            "expected_response_format": {
                "results": [
                    {"strongs_id": "H157", "lemma": "אָהַב", "gloss": "to love"},
                    {"strongs_id": "H160", "lemma": "אַהֲבָה", "gloss": "love"}
                ]
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "lexicon",
                "difficulty": "basic"
            }
        },
        {
            "query": "Get Hebrew morphology code information for Ncmsc",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/morphology/hebrew/Ncmsc",
                "method": "GET"
            },
            "expected_response_format": {
                "code": "Ncmsc",
                "description": "Noun common masculine singular construct",
                "parts": {
                    "N": "Noun",
                    "c": "common",
                    "m": "masculine",
                    "s": "singular",
                    "c": "construct"
                }
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "morphology",
                "difficulty": "intermediate"
            }
        },
        {
            "query": "Search for biblical names starting with 'David'",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/names/search",
                "method": "GET",
                "query_params": {"q": "David", "type": "name"}
            },
            "expected_response_format": {
                "results": [
                    {
                        "name": "David",
                        "hebrew": "דָּוִד",
                        "meaning": "beloved",
                        "occurrences": 1075
                    }
                ]
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "names",
                "difficulty": "basic"
            }
        },
        {
            "query": "Get theological terms report",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/theological_terms_report",
                "method": "GET"
            },
            "expected_response_format": {
                "terms": [
                    {
                        "term": "Elohim",
                        "strongs_id": "H430",
                        "count": 2602
                    },
                    {
                        "term": "YHWH",
                        "strongs_id": "H3068",
                        "count": 6828
                    }
                ]
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "theological",
                "difficulty": "intermediate"
            }
        },
        {
            "query": "Get cross-language theological terms",
            "action": "api_call",
            "parameters": {
                "endpoint": "/api/cross_language/terms",
                "method": "GET"
            },
            "expected_response_format": {
                "terms": [
                    {
                        "hebrew": {"term": "אֱלֹהִים", "strongs_id": "H430"},
                        "greek": {"term": "θεός", "strongs_id": "G2316"},
                        "concept": "God"
                    }
                ]
            },
            "metadata": {
                "interaction_type": "api_call",
                "api_category": "cross_language",
                "difficulty": "advanced"
            }
        }
    ]
    
    # Combine and save
    all_examples = web_examples + new_examples
    save_jsonl_file(all_examples, 'web_interaction_dataset.jsonl')
    
    return len(new_examples)

def enhance_web_ui_examples():
    """Add examples of web UI interactions."""
    ui_examples = [
        {
            "query": "How to search for verses containing 'love'",
            "action": "ui_interaction",
            "steps": [
                {"step": 1, "action": "Navigate to /search"},
                {"step": 2, "action": "Enter 'love' in the search box"},
                {"step": 3, "action": "Select 'Verse' as search type"},
                {"step": 4, "action": "Click Search button"}
            ],
            "expected_result": "List of Bible verses containing the word 'love'",
            "problem_solving": "If no results appear, try different spellings or check if filters are applied",
            "metadata": {
                "interaction_type": "web_ui",
                "feature": "verse_search",
                "difficulty": "basic"
            }
        },
        {
            "query": "How to look up a Strong's number for a Hebrew word",
            "action": "ui_interaction",
            "steps": [
                {"step": 1, "action": "Navigate to /lexicon/hebrew"},
                {"step": 2, "action": "Enter a Strong's ID (e.g., 'H430') in the search box"},
                {"step": 3, "action": "Click 'Search' or press Enter"}
            ],
            "expected_result": "Lexicon entry for the specified Strong's number",
            "problem_solving": "If entry doesn't appear, check if the Strong's ID format is correct (H followed by number)",
            "metadata": {
                "interaction_type": "web_ui",
                "feature": "lexicon_lookup",
                "difficulty": "basic"
            }
        },
        {
            "query": "How to compare translations of John 3:16",
            "action": "ui_interaction",
            "steps": [
                {"step": 1, "action": "Navigate to /bible/John/3/16"},
                {"step": 2, "action": "Click on 'Show Other Translations' button"},
                {"step": 3, "action": "Select translations to compare from the dropdown menu"}
            ],
            "expected_result": "Side-by-side view of John 3:16 in different translations",
            "problem_solving": "If a translation is not available, it may not be in the database or may have licensing restrictions",
            "metadata": {
                "interaction_type": "web_ui",
                "feature": "translation_comparison",
                "difficulty": "basic"
            }
        },
        {
            "query": "How to analyze Hebrew morphology of Genesis 1:1",
            "action": "ui_interaction",
            "steps": [
                {"step": 1, "action": "Navigate to /bible/Genesis/1/1"},
                {"step": 2, "action": "Click on 'Show Original Text' button"},
                {"step": 3, "action": "Hover over or click on a Hebrew word to see morphology details"}
            ],
            "expected_result": "Original Hebrew text with morphological analysis",
            "problem_solving": "If morphology details don't appear, check if tagged text is available for this verse",
            "metadata": {
                "interaction_type": "web_ui",
                "feature": "morphology_analysis",
                "difficulty": "advanced"
            }
        }
    ]
    
    # Save to a new file
    save_jsonl_file(ui_examples, 'web_ui_interaction_dataset.jsonl')
    
    return len(ui_examples)

def fix_theological_term_examples():
    """Fix formatting issues in theological term examples."""
    # Load existing examples
    theological_examples = load_jsonl_file('theological_terms_dataset.jsonl')
    qa_examples = load_jsonl_file('qa_dataset.jsonl')
    
    # Fix common YHWH issue - answers have HTML artifacts
    for example in qa_examples:
        if "What is the meaning of the Hebrew name 'YHWH'" in example.get('question', ''):
            # Fix the answer by replacing the HTML with proper content
            example['answer'] = "LORD, Yahweh, the proper name of the God of Israel"
    
    # Add improved theological term examples
    new_theological_examples = [
        {
            "term": {"word": "יְהוָה", "strongs_id": "H3068", "lemma": "יְהוָה", "gloss": "LORD, Yahweh"},
            "context": {"verse_text": "These are the generations of the heavens and the earth when they were created, in the day that the LORD God made the earth and the heavens.", "book": "Genesis", "chapter": 2, "verse": 4},
            "analysis": {
                "theological_meaning": "The personal, covenant name of God in the Hebrew Bible",
                "importance": "Core theological term representing God's self-revelation and covenant relationship",
                "pronunciation": "Traditionally not pronounced; substituted with 'Adonai' (Lord)",
                "key_concepts": ["divine name", "covenant", "self-existence", "I AM"]
            }
        },
        {
            "term": {"word": "חֶסֶד", "strongs_id": "H2617", "lemma": "חֶסֶד", "gloss": "lovingkindness, steadfast love"},
            "context": {"verse_text": "But I have trusted in your steadfast love; my heart shall rejoice in your salvation.", "book": "Psalms", "chapter": 13, "verse": 5},
            "analysis": {
                "theological_meaning": "God's covenant loyalty, steadfast love, and faithfulness",
                "importance": "Central attribute of God in the Hebrew Bible that combines love, mercy, and faithfulness",
                "related_concepts": ["covenant", "mercy", "faithfulness", "love"],
                "new_testament_parallel": "Grace (χάρις, G5485)"
            }
        },
        {
            "term": {"word": "אָמֵן", "strongs_id": "H539", "lemma": "אָמַן", "gloss": "to confirm, support, believe"},
            "context": {"verse_text": "And he believed the LORD, and he counted it to him as righteousness.", "book": "Genesis", "chapter": 15, "verse": 6},
            "analysis": {
                "theological_meaning": "Faith, trust, belief in God and his promises",
                "importance": "Foundational concept of faith and trust in God's promises",
                "root_meaning": "Firmness, faithfulness, reliability",
                "derivation": "The word 'Amen' comes from this root, meaning 'truly, certainly'"
            }
        }
    ]
    
    # Combine and save
    all_theological_examples = theological_examples + new_theological_examples
    save_jsonl_file(all_theological_examples, 'theological_terms_dataset.jsonl')
    save_jsonl_file(qa_examples, 'qa_dataset.jsonl')
    
    return len(new_theological_examples)

def add_problem_solution_examples():
    """Add examples in problem/solution format."""
    problem_solutions = [
        {
            "problem": "API returns 404 for /api/verses endpoint",
            "context": "Attempting to fetch Bible verses using the API",
            "diagnostic_steps": [
                "Check if the API server is running with correct Flask application",
                "Verify the endpoint path is correct in the documentation",
                "Check if the endpoint is implemented in the code",
                "Look for any routing issues in the API implementation"
            ],
            "solution": "Endpoints for verses should be accessed via /api/verses with required query parameters: translation, book, chapter, verse",
            "code_example": """
# Python example for correct API call
import requests

response = requests.get(
    "http://localhost:5000/api/verses",
    params={
        "translation": "KJV",
        "book": "John",
        "chapter": 3,
        "verse": 16
    }
)

if response.status_code == 200:
    verse = response.json()
    print(verse["text"])
else:
    print(f"Error: {response.status_code}")
""",
            "metadata": {
                "issue_type": "api_error",
                "difficulty": "intermediate"
            }
        },
        {
            "problem": "DSPy collection not triggering after database changes",
            "context": "Making database changes but DSPy training data not updating",
            "diagnostic_steps": [
                "Check if database connection is established correctly",
                "Verify that the state file (.state.json) exists and is readable",
                "Look for any errors in the logs (dspy_collector.log)",
                "Check if the database changes affect tables monitored by the collector"
            ],
            "solution": "Ensure that the database changes are commited and affect tables that are monitored in the get_db_state_hash function. You can also manually trigger collection using the refresh_dspy_data.py script.",
            "code_example": """
# Manual refresh of DSPy data
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import dspy_collector
from src.database.connection import get_connection

conn = get_connection()
result = dspy_collector.force_regeneration(conn)
print(f"DSPy regeneration result: {result}")
""",
            "metadata": {
                "issue_type": "data_collection",
                "difficulty": "advanced"
            }
        },
        {
            "problem": "Wrong theological term data for YHWH entries",
            "context": "YHWH entries showing HTML formatting issues in the answers",
            "diagnostic_steps": [
                "Check the source of the theological data in the database",
                "Verify the HTML parsing in the data generation script",
                "Look for any encoding issues in the data",
                "Check if the data is properly escaped when generating JSONL"
            ],
            "solution": "Update the generate_theological_terms_dataset function to properly clean HTML tags and fix formatting issues in YHWH entries.",
            "code_example": """
# Function to clean HTML tags from text
def clean_html(html_text):
    import re
    # Remove HTML tags
    clean_text = re.sub(r'<.*?>', '', html_text)
    # Fix common entity issues
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    return clean_text

# Apply to gloss data
entry['gloss'] = clean_html(entry['gloss']) if entry['gloss'] else "N/A"
""",
            "metadata": {
                "issue_type": "data_quality",
                "difficulty": "intermediate"
            }
        },
        {
            "problem": "API server not starting correctly",
            "context": "Error: Failed to find Flask application or factory in module 'src.api'",
            "diagnostic_steps": [
                "Check if the correct Flask application module is specified",
                "Verify that the module exists and has a Flask application",
                "Check environment variables for FLASK_APP",
                "Check import structure in the API code"
            ],
            "solution": "Update start_servers.py to use the correct Flask application module path: 'src.api.lexicon_api' instead of 'src.api'",
            "code_example": """
# In start_servers.py
def start_api_server(port):
    \"\"\"Start the API server.\"\"\"
    print_info(f"Starting API server on port {port}...")
    try:
        env = os.environ.copy()
        env["FLASK_APP"] = "src.api.lexicon_api"  # Correct path
        api_process = subprocess.Popen(
            ["python", "-m", "flask", "run", "--port", str(port)],
            env=env
        )
        time.sleep(2)  # Give the server a moment to start
        print_success(f"API server started on http://localhost:{port}")
        return api_process
    except Exception as e:
        print_failure(f"Failed to start API server: {e}")
        return None
""",
            "metadata": {
                "issue_type": "server_configuration",
                "difficulty": "basic"
            }
        }
    ]
    
    # Save to a new file
    save_jsonl_file(problem_solutions, 'problem_solution_dataset.jsonl')
    
    return len(problem_solutions)

def create_dspy_metric_examples():
    """Create examples of DSPy evaluation metrics."""
    metric_examples = load_jsonl_file('evaluation_metrics.jsonl')
    
    new_metrics = [
        {
            "task": "theological_term_analysis",
            "metric_name": "theological_accuracy",
            "metric_implementation": """
def theological_accuracy(prediction, reference):
    \"\"\"
    Measures accuracy of theological term analysis by comparing key concepts.
    
    Args:
        prediction: The model's theological analysis
        reference: The reference theological analysis
        
    Returns:
        float: Score between 0.0 and 1.0
    \"\"\"
    # Extract key concepts from prediction and reference
    pred_concepts = set(prediction.get('key_concepts', []))
    ref_concepts = set(reference.get('key_concepts', []))
    
    # Calculate overlap
    if not ref_concepts:
        return 0.0
    
    overlap = len(pred_concepts.intersection(ref_concepts))
    return overlap / len(ref_concepts)
""",
            "usage_example": """
# Example usage in DSPy
import dspy

class TheologicalAccuracy(dspy.Metric):
    def __call__(self, example, prediction):
        return theological_accuracy(prediction.analysis, example.reference_analysis)
        
metric = TheologicalAccuracy()
optimizer = dspy.teleprompt.SIMBA(metric=metric)
optimized_module = optimizer.optimize(theological_module, trainset=trainset)
""",
            "metadata": {
                "metric_type": "accuracy",
                "theological_focus": True,
                "complexity": "intermediate"
            }
        },
        {
            "task": "cross_lingual_verse_comparison",
            "metric_name": "cross_lingual_consistency",
            "metric_implementation": """
def cross_lingual_consistency(prediction, reference):
    \"\"\"
    Measures consistency between translations of the same verse across languages.
    
    Args:
        prediction: The model's analysis of cross-language consistency
        reference: The reference analysis with key theological terms
        
    Returns:
        float: Score between 0.0 and 1.0
    \"\"\"
    # Extract key terms from prediction and reference
    pred_terms = set(term.lower() for term in prediction.get('consistent_terms', []))
    ref_terms = set(term.lower() for term in reference.get('consistent_terms', []))
    
    # Calculate F1 score for term overlap
    if not pred_terms or not ref_terms:
        return 0.0
    
    precision = len(pred_terms.intersection(ref_terms)) / len(pred_terms) if pred_terms else 0
    recall = len(pred_terms.intersection(ref_terms)) / len(ref_terms) if ref_terms else 0
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * precision * recall / (precision + recall)
    return f1
""",
            "usage_example": """
# Example usage in DSPy
import dspy

# Define the metric
class CrossLingualConsistency(dspy.Metric):
    def __call__(self, example, prediction):
        return cross_lingual_consistency(prediction.analysis, example.reference_analysis)
        
# Use the metric in optimization
metric = CrossLingualConsistency()
optimizer = dspy.teleprompt.SIMBA(metric=metric)
optimized_module = optimizer.optimize(cross_lingual_module, trainset=trainset)
""",
            "metadata": {
                "metric_type": "consistency",
                "theological_focus": False,
                "complexity": "advanced"
            }
        }
    ]
    
    # Combine and save
    all_metrics = metric_examples + new_metrics
    save_jsonl_file(all_metrics, 'evaluation_metrics.jsonl')
    
    return len(new_metrics)

def main():
    """Main function to run the enhancement process."""
    try:
        # Ensure directory exists
        ensure_directory()
        
        # Enhance each dataset
        api_examples = enhance_api_examples()
        ui_examples = enhance_web_ui_examples()
        theological_fixed = fix_theological_term_examples()
        problem_solutions = add_problem_solution_examples()
        metrics = create_dspy_metric_examples()
        
        # Log summary
        logger.info("\n=== DSPy Training Data Enhancement Summary ===")
        logger.info(f"Added {api_examples} new API examples")
        logger.info(f"Added {ui_examples} new UI interaction examples")
        logger.info(f"Added {theological_fixed} new theological examples and fixed existing ones")
        logger.info(f"Added {problem_solutions} new problem-solution examples")
        logger.info(f"Added {metrics} new DSPy metric examples")
        logger.info("Enhancement completed successfully!")
        
        # Print summary to console
        print("\n=== DSPy Training Data Enhancement Summary ===")
        print(f"Added {api_examples} new API examples")
        print(f"Added {ui_examples} new UI interaction examples")
        print(f"Added {theological_fixed} new theological examples and fixed existing ones")
        print(f"Added {problem_solutions} new problem-solution examples")
        print(f"Added {metrics} new DSPy metric examples")
        print("\nEnhancement completed successfully!")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in enhancement process: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 