#!/usr/bin/env python3
"""
DSPy Training Data Generator

This script generates high-quality DSPy training data for various tasks:
1. Question-Answering (QA) about Bible verses
2. Summarization of Bible passages
3. Translation pairs between languages
4. Theological term analysis
5. Named entity recognition
6. Tool usage and web interaction tasks

The generated data follows DSPy format conventions and captures context/labels
for training language models to perform Bible-related tasks.
"""

import os
import sys
import json
import logging
import pandas as pd
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
        logging.FileHandler('logs/dspy_data_generator.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path('data/processed/dspy_training_data')
DB_SCHEMA = 'bible'

# Critical theological terms to ensure are included
CRITICAL_TERMS = {
    "H430": {"name": "Elohim", "min_count": 2600},
    "H3068": {"name": "YHWH", "min_count": 6000},
    "H113": {"name": "Adon", "min_count": 335},
    "H2617": {"name": "Chesed", "min_count": 248},
    "H539": {"name": "Aman", "min_count": 100}
}

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

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR

def save_jsonl(data, filename):
    """Save data as JSONL file."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header with metadata as comment
        f.write(f"// DSPy training data for {filename.split('.')[0]}\n")
        f.write(f"// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Write each data item as a JSON line
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(data)} examples to {filepath}")
    return filepath

def generate_qa_dataset(conn, limit=1000):
    """Generate Question-Answer pairs for Bible verses."""
    qa_pairs = []
    
    # Example 1: Get some key Genesis verses for QA pairs
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # Genesis creation account
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'Genesis' 
                AND chapter_num = 1 
                AND verse_num BETWEEN 1 AND 10
                ORDER BY chapter_num, verse_num
            """)
            genesis_verses = cur.fetchall()
            
            # Create QA pairs for Genesis 1:1
            if genesis_verses and len(genesis_verses) > 0:
                gen1_1 = next((v for v in genesis_verses if v['verse_num'] == 1), None)
                if gen1_1:
                    qa_pairs.append({
                        "context": gen1_1['verse_text'],
                        "question": "Who created the heavens and the earth?",
                        "answer": "God",
                        "metadata": {
                            "book": gen1_1['book_name'],
                            "chapter": gen1_1['chapter_num'],
                            "verse": gen1_1['verse_num'],
                            "type": "factual"
                        }
                    })
                    
                    qa_pairs.append({
                        "context": gen1_1['verse_text'],
                        "question": "What did God create in the beginning?",
                        "answer": "The heavens and the earth",
                        "metadata": {
                            "book": gen1_1['book_name'],
                            "chapter": gen1_1['chapter_num'],
                            "verse": gen1_1['verse_num'],
                            "type": "factual"
                        }
                    })
            
            # Get John 3:16
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'John' 
                AND chapter_num = 3 
                AND verse_num = 16
            """)
            john3_16 = cur.fetchone()
            
            if john3_16:
                qa_pairs.append({
                    "context": john3_16['verse_text'],
                    "question": "What did God give because of his love for the world?",
                    "answer": "His one and only Son",
                    "metadata": {
                        "book": john3_16['book_name'],
                        "chapter": john3_16['chapter_num'],
                        "verse": john3_16['verse_num'],
                        "type": "theological"
                    }
                })
                
                qa_pairs.append({
                    "context": john3_16['verse_text'],
                    "question": "Why did God give his one and only Son?",
                    "answer": "Because he loved the world",
                    "metadata": {
                        "book": john3_16['book_name'],
                        "chapter": john3_16['chapter_num'],
                        "verse": john3_16['verse_num'],
                        "type": "theological"
                    }
                })
            
            # Get some Psalm verses
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'Psalms' 
                AND chapter_num = 23
                ORDER BY verse_num
                LIMIT 6
            """)
            psalm23_verses = cur.fetchall()
            
            if psalm23_verses:
                psalm23_1 = next((v for v in psalm23_verses if v['verse_num'] == 1), None)
                if psalm23_1:
                    qa_pairs.append({
                        "context": psalm23_1['verse_text'],
                        "question": "Who is the psalmist's shepherd?",
                        "answer": "The LORD",
                        "metadata": {
                            "book": psalm23_1['book_name'],
                            "chapter": psalm23_1['chapter_num'],
                            "verse": psalm23_1['verse_num'],
                            "type": "theological"
                        }
                    })
            
            # Add questions about theological terms
            cur.execute("""
                SELECT h.book_name, h.chapter_num, h.verse_num, h.word_text, h.strongs_id, e.gloss
                FROM bible.hebrew_ot_words h
                JOIN bible.hebrew_entries e ON h.strongs_id = e.strongs_id
                WHERE h.strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
                LIMIT 100
            """)
            theological_terms = cur.fetchall()
            
            for term in theological_terms:
                if term['strongs_id'] == 'H430':  # Elohim
                    qa_pairs.append({
                        "context": f"Hebrew word '{term['word_text']}' (Strong's ID: {term['strongs_id']}) in {term['book_name']} {term['chapter_num']}:{term['verse_num']}",
                        "question": "What is the meaning of the Hebrew word 'Elohim'?",
                        "answer": term['gloss'] or "God, gods, judges, angels",
                        "metadata": {
                            "book": term['book_name'],
                            "chapter": term['chapter_num'],
                            "verse": term['verse_num'],
                            "strongs_id": term['strongs_id'],
                            "type": "lexical"
                        }
                    })
                elif term['strongs_id'] == 'H3068':  # YHWH
                    qa_pairs.append({
                        "context": f"Hebrew word '{term['word_text']}' (Strong's ID: {term['strongs_id']}) in {term['book_name']} {term['chapter_num']}:{term['verse_num']}",
                        "question": "What is the meaning of the Hebrew name 'YHWH'?",
                        "answer": term['gloss'] or "LORD, Yahweh, the proper name of the God of Israel",
                        "metadata": {
                            "book": term['book_name'],
                            "chapter": term['chapter_num'],
                            "verse": term['verse_num'],
                            "strongs_id": term['strongs_id'],
                            "type": "lexical"
                        }
                    })
    
    except Exception as e:
        logger.error(f"Error generating QA dataset: {e}", exc_info=True)
        # Roll back any open transaction
        conn.rollback()
    
    return qa_pairs

def generate_summarization_dataset(conn, limit=500):
    """Generate passage-summary pairs."""
    summaries = []
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # Genesis 1:1-2
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'Genesis' 
                AND chapter_num = 1 
                AND verse_num IN (1, 2)
                ORDER BY verse_num
            """)
            gen1_verses = cur.fetchall()
            
            if gen1_verses and len(gen1_verses) >= 2:
                passage = " ".join(v['verse_text'] for v in gen1_verses)
                summaries.append({
                    "passage": passage,
                    "summary": "God created the heavens and the earth, and the Spirit of God was over the waters.",
                    "metadata": {
                        "book": "Genesis",
                        "chapter": 1,
                        "verses": [1, 2],
                        "type": "creation_narrative"
                    }
                })
            
            # Psalm 23
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'Psalms' 
                AND chapter_num = 23
                ORDER BY verse_num
            """)
            psalm23_verses = cur.fetchall()
            
            if psalm23_verses:
                passage = " ".join(v['verse_text'] for v in psalm23_verses)
                summaries.append({
                    "passage": passage,
                    "summary": "The LORD is the psalmist's shepherd who provides, guides, and protects through all of life's journey.",
                    "metadata": {
                        "book": "Psalms",
                        "chapter": 23,
                        "verses": [v['verse_num'] for v in psalm23_verses],
                        "type": "psalm"
                    }
                })
            
            # John 3:16-17
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, verse_text 
                FROM bible.verses 
                WHERE book_name = 'John' 
                AND chapter_num = 3 
                AND verse_num IN (16, 17)
                ORDER BY verse_num
            """)
            john3_verses = cur.fetchall()
            
            if john3_verses and len(john3_verses) >= 2:
                passage = " ".join(v['verse_text'] for v in john3_verses)
                summaries.append({
                    "passage": passage,
                    "summary": "God loved the world so much that he gave his Son to save, not condemn, the world.",
                    "metadata": {
                        "book": "John",
                        "chapter": 3,
                        "verses": [16, 17],
                        "type": "gospel"
                    }
                })
    
    except Exception as e:
        logger.error(f"Error generating summarization dataset: {e}", exc_info=True)
        # Roll back any open transaction
        conn.rollback()
    
    return summaries

def generate_translation_dataset(conn, limit=100):
    """Generate parallel translation examples."""
    translations = []
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # Get Hebrew-English pairs
            cur.execute("""
                SELECT h.book_name, h.chapter_num, h.verse_num, 
                       string_agg(h.word_text, ' ') as hebrew_text,
                       e.verse_text as english_text
                FROM bible.hebrew_ot_words h
                JOIN bible.verses e ON 
                    h.book_name = e.book_name AND 
                    h.chapter_num = e.chapter_num AND 
                    h.verse_num = e.verse_num
                WHERE h.book_name IN ('Genesis', 'Psalms')
                GROUP BY h.book_name, h.chapter_num, h.verse_num, e.verse_text
                LIMIT 50
            """)
            hebrew_english = cur.fetchall()
            
            for pair in hebrew_english:
                translations.append({
                    "source": pair['hebrew_text'],
                    "target": pair['english_text'],
                    "metadata": {
                        "book": pair['book_name'],
                        "chapter": pair['chapter_num'],
                        "verse": pair['verse_num'],
                        "source_language": "Hebrew",
                        "target_language": "English"
                    }
                })
            
            # Get Greek-English pairs
            cur.execute("""
                SELECT g.book_name, g.chapter_num, g.verse_num, 
                       string_agg(g.word_text, ' ') as greek_text,
                       e.verse_text as english_text
                FROM bible.greek_nt_words g
                JOIN bible.verses e ON 
                    g.book_name = e.book_name AND 
                    g.chapter_num = e.chapter_num AND 
                    g.verse_num = e.verse_num
                WHERE g.book_name IN ('John', 'Romans')
                GROUP BY g.book_name, g.chapter_num, g.verse_num, e.verse_text
                LIMIT 50
            """)
            greek_english = cur.fetchall()
            
            for pair in greek_english:
                translations.append({
                    "source": pair['greek_text'],
                    "target": pair['english_text'],
                    "metadata": {
                        "book": pair['book_name'],
                        "chapter": pair['chapter_num'],
                        "verse": pair['verse_num'],
                        "source_language": "Greek",
                        "target_language": "English"
                    }
                })
    
    except Exception as e:
        logger.error(f"Error generating translation dataset: {e}", exc_info=True)
        # Roll back any open transaction
        conn.rollback()
    
    return translations

def generate_theological_terms_dataset(conn, limit=500):
    """Generate theological term analysis examples."""
    term_examples = []
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # Get examples for critical theological terms
            for strongs_id, info in CRITICAL_TERMS.items():
                cur.execute("""
                    SELECT h.book_name, h.chapter_num, h.verse_num, h.word_text as word, 
                           h.strongs_id, e.hebrew_word as lemma, e.gloss, h.grammar_code,
                           v.verse_text as verse_text
                    FROM bible.hebrew_ot_words h
                    JOIN bible.hebrew_entries e ON h.strongs_id = e.strongs_id
                    JOIN bible.verses v ON 
                        h.book_name = v.book_name AND 
                        h.chapter_num = v.chapter_num AND 
                        h.verse_num = v.verse_num
                    WHERE h.strongs_id = %s
                    ORDER BY random()
                    LIMIT 20
                """, (strongs_id,))
                examples = cur.fetchall()
                
                for ex in examples:
                    term_examples.append({
                        "term": {
                            "word": ex['word'],
                            "strongs_id": ex['strongs_id'],
                            "lemma": ex['lemma'],
                            "gloss": ex['gloss']
                        },
                        "context": {
                            "verse_text": ex['verse_text'],
                            "book": ex['book_name'],
                            "chapter": ex['chapter_num'],
                            "verse": ex['verse_num']
                        },
                        "analysis": {
                            "theological_meaning": info['name'],
                            "importance": f"Core theological term with expected {info['min_count']}+ occurrences",
                            "hebrew_morphology": ex['grammar_code']
                        }
                    })
    
    except Exception as e:
        logger.error(f"Error generating theological terms dataset: {e}", exc_info=True)
        # Roll back any open transaction
        conn.rollback()
    
    return term_examples

def generate_ner_dataset(conn, limit=500):
    """Generate named entity recognition examples."""
    ner_examples = []
    
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            # Get person names from the Bible
            cur.execute("""
                SELECT book_name, chapter_num, verse_num, word_text, 
                       CASE
                           WHEN strongs_id IN ('H430', 'H3068', 'H113') THEN 'DEITY'
                           WHEN grammar_code LIKE '%Prop%' THEN 'PERSON'
                           ELSE 'O'
                       END as entity_type
                FROM bible.hebrew_ot_words
                WHERE strongs_id IN ('H430', 'H3068', 'H113') 
                   OR grammar_code LIKE '%Prop%'
                LIMIT 100
            """)
            entities = cur.fetchall()
            
            # Group by verse
            verse_entities = {}
            for entity in entities:
                key = f"{entity['book_name']}_{entity['chapter_num']}_{entity['verse_num']}"
                if key not in verse_entities:
                    verse_entities[key] = {
                        'book': entity['book_name'],
                        'chapter': entity['chapter_num'],
                        'verse': entity['verse_num'],
                        'tokens': [],
                        'tags': []
                    }
                
                verse_entities[key]['tokens'].append(entity['word_text'])
                verse_entities[key]['tags'].append(entity['entity_type'])
            
            # Convert to NER examples
            for key, data in verse_entities.items():
                ner_examples.append({
                    "tokens": data['tokens'],
                    "tags": data['tags'],
                    "metadata": {
                        "book": data['book'],
                        "chapter": data['chapter'],
                        "verse": data['verse'],
                        "task": "named_entity_recognition"
                    }
                })
    
    except Exception as e:
        logger.error(f"Error generating NER dataset: {e}", exc_info=True)
        # Roll back any open transaction
        conn.rollback()
    
    return ner_examples

def generate_web_interaction_dataset(conn, limit=100):
    """Generate examples of tool usage and web interactions."""
    web_examples = []
    
    # Example 1: Search for verses containing theological terms
    web_examples.append({
        "query": "Find verses containing the name YHWH in Genesis",
        "action": "search_database",
        "parameters": {
            "book": "Genesis",
            "term": "YHWH",
            "strongs_id": "H3068"
        },
        "expected_response_format": {
            "results": [{"reference": "Gen 2:4", "text": "..."}]
        },
        "metadata": {
            "interaction_type": "database_query",
            "theological_term": "YHWH"
        }
    })
    
    # Example 2: Retrieve Strong's definition
    web_examples.append({
        "query": "What is the definition of Elohim in Hebrew?",
        "action": "lookup_strongs",
        "parameters": {
            "strongs_id": "H430",
            "term": "Elohim"
        },
        "expected_response_format": {
            "strongs_id": "H430",
            "term": "אלהים",
            "transliteration": "Elohim",
            "definition": "God, gods, judges, angels"
        },
        "metadata": {
            "interaction_type": "lexicon_lookup",
            "theological_term": "Elohim"
        }
    })
    
    # Example 3: Compare translations
    web_examples.append({
        "query": "Compare John 3:16 in different translations",
        "action": "compare_translations",
        "parameters": {
            "reference": "John 3:16",
            "translations": ["KJV", "NIV", "ESV"]
        },
        "expected_response_format": {
            "reference": "John 3:16",
            "translations": {
                "KJV": "For God so loved the world...",
                "NIV": "For God so loved the world...",
                "ESV": "For God so loved the world..."
            }
        },
        "metadata": {
            "interaction_type": "translation_comparison",
            "passage_type": "gospel"
        }
    })
    
    # Add more web interface interaction examples
    for i in range(10):
        web_examples.append({
            "query": f"Generate theological analysis of passage {i}",
            "action": "analyze_theology",
            "parameters": {
                "passage": f"Sample passage {i}",
                "theological_terms": ["Elohim", "YHWH", "Adon"]
            },
            "expected_response_format": {
                "analysis": "Theological analysis result",
                "key_terms": ["term1", "term2"],
                "themes": ["theme1", "theme2"]
            },
            "metadata": {
                "interaction_type": "theological_analysis",
                "complexity": "medium"
            }
        })
    
    return web_examples

def generate_dspy_evaluation_metrics():
    """Generate DSPy evaluation metrics examples."""
    eval_examples = []
    
    # Example 1: QA evaluation metrics
    eval_examples.append({
        "task": "bible_qa",
        "metric_name": "theological_accuracy",
        "metric_implementation": """
def theological_accuracy(prediction, reference):
    # Check if the prediction aligns with theological truth
    critical_terms = ["Elohim", "YHWH", "Adon", "Chesed", "Aman"]
    for term in critical_terms:
        if term in reference and term not in prediction:
            return 0.0
    # More complex theological verification...
    return 1.0
""",
        "metadata": {
            "metric_type": "accuracy",
            "theological_focus": True
        }
    })
    
    # Example 2: Translation evaluation
    eval_examples.append({
        "task": "bible_translation",
        "metric_name": "theological_term_preservation",
        "metric_implementation": """
def theological_term_preservation(prediction, reference):
    # Check if theological terms are preserved in translation
    source_terms = extract_theological_terms(reference["source"])
    target_terms = extract_theological_terms(prediction)
    
    if not source_terms:
        return 1.0
    
    preserved = sum(1 for term in source_terms if term in target_terms)
    return preserved / len(source_terms)
""",
        "metadata": {
            "metric_type": "preservation",
            "theological_focus": True
        }
    })
    
    return eval_examples

def main():
    """Main function to orchestrate DSPy training data generation."""
    logger.info("Starting DSPy training data generation")
    
    try:
        # Create output directory
        ensure_output_dir()
        
        # Get database connection
        conn = get_db_connection()
        conn.autocommit = True  # Use autocommit mode to avoid transaction issues
        
        # Generate datasets
        qa_data = generate_qa_dataset(conn)
        save_jsonl(qa_data, "qa_dataset.jsonl")
        
        summarization_data = generate_summarization_dataset(conn)
        save_jsonl(summarization_data, "summarization_dataset.jsonl")
        
        translation_data = generate_translation_dataset(conn)
        save_jsonl(translation_data, "translation_dataset.jsonl")
        
        theological_terms_data = generate_theological_terms_dataset(conn)
        save_jsonl(theological_terms_data, "theological_terms_dataset.jsonl")
        
        ner_data = generate_ner_dataset(conn)
        save_jsonl(ner_data, "ner_dataset.jsonl")
        
        # Generate new web interaction data
        web_interaction_data = generate_web_interaction_dataset(conn)
        save_jsonl(web_interaction_data, "web_interaction_dataset.jsonl")
        
        # Generate DSPy evaluation metrics
        eval_metrics = generate_dspy_evaluation_metrics()
        save_jsonl(eval_metrics, "evaluation_metrics.jsonl")
        
        # Generate consolidated README
        datasets = {
            "qa_dataset.jsonl": len(qa_data),
            "summarization_dataset.jsonl": len(summarization_data),
            "translation_dataset.jsonl": len(translation_data),
            "theological_terms_dataset.jsonl": len(theological_terms_data),
            "ner_dataset.jsonl": len(ner_data),
            "web_interaction_dataset.jsonl": len(web_interaction_data),
            "evaluation_metrics.jsonl": len(eval_metrics),
            "tvtms_parsing_examples.jsonl": "(TVTMS versification mapping examples)",
            "versification_parser_schema_issues.jsonl": "(Versification parser issues)"
        }
        
        # Update README
        with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
            f.write("# DSPy Training Data for BibleScholarProject\n\n")
            f.write("This directory contains training data files for DSPy-based AI model development in the BibleScholarProject.\n\n")
            
            f.write("## File Listing and Contents\n\n")
            for filename, count in datasets.items():
                f.write(f"- `{filename}`: {count if not isinstance(count, str) else count} examples\n")
            
            f.write("\n## Schema\n\n")
            f.write("Each file is a JSONL file (one JSON object per line) with task-specific fields:\n\n")
            
            f.write("### Question-Answering (QA)\n")
            f.write("```json\n{\n  \"context\": \"Bible verse text\",\n  \"question\": \"Question about the verse\",\n  \"answer\": \"Answer to the question\",\n  \"metadata\": {\"book\": \"Genesis\", \"chapter\": 1, \"verse\": 1}\n}\n```\n\n")
            
            f.write("### Summarization\n")
            f.write("```json\n{\n  \"passage\": \"Bible passage text\",\n  \"summary\": \"Summary of the passage\",\n  \"metadata\": {\"book\": \"Genesis\", \"chapter\": 1, \"verses\": [1, 2]}\n}\n```\n\n")
            
            f.write("### Translation\n")
            f.write("```json\n{\n  \"source\": \"Original language text\",\n  \"target\": \"Translated text\",\n  \"metadata\": {\"book\": \"Genesis\", \"chapter\": 1, \"verse\": 1, \"source_language\": \"Hebrew\", \"target_language\": \"English\"}\n}\n```\n\n")
            
            f.write("### Theological Terms\n")
            f.write("```json\n{\n  \"term\": {\"word\": \"אלהים\", \"strongs_id\": \"H430\", \"lemma\": \"אלהים\", \"gloss\": \"God\"},\n  \"context\": {\"verse_text\": \"In the beginning God created...\", \"book\": \"Genesis\", \"chapter\": 1, \"verse\": 1},\n  \"analysis\": {\"theological_meaning\": \"Elohim\", \"importance\": \"Core theological term\"}\n}\n```\n\n")
            
            f.write("### Named Entity Recognition\n")
            f.write("```json\n{\n  \"tokens\": [\"In\", \"the\", \"beginning\", \"God\", \"created\"],\n  \"tags\": [\"O\", \"O\", \"O\", \"DEITY\", \"O\"],\n  \"metadata\": {\"book\": \"Genesis\", \"chapter\": 1, \"verse\": 1}\n}\n```\n\n")
            
            f.write("### Web Interaction\n")
            f.write("```json\n{\n  \"query\": \"Find verses containing YHWH\",\n  \"action\": \"search_database\",\n  \"parameters\": {\"book\": \"Genesis\", \"term\": \"YHWH\", \"strongs_id\": \"H3068\"},\n  \"expected_response_format\": {\"results\": [{\"reference\": \"Gen 2:4\", \"text\": \"...\"}]},\n  \"metadata\": {\"interaction_type\": \"database_query\"}\n}\n```\n\n")
            
            f.write("### Evaluation Metrics\n")
            f.write("```json\n{\n  \"task\": \"bible_qa\",\n  \"metric_name\": \"theological_accuracy\",\n  \"metric_implementation\": \"def theological_accuracy(prediction, reference): ...\",\n  \"metadata\": {\"metric_type\": \"accuracy\", \"theological_focus\": true}\n}\n```\n\n")
            
            f.write("## Using with DSPy\n\n")
            f.write("```python\nimport dspy\nimport json\n\n# Basic loading of examples\nwith open('data/processed/dspy_training_data/qa_dataset.jsonl') as f:\n    trainset = [dspy.Example(**json.loads(line)) for line in f if not line.startswith('//') and line.strip()]\n\n# Using DSPy for model optimization\nfrom dspy.teleprompt import SIMBA\noptimizer = SIMBA(metric=\"theological_accuracy\")\noptimized_model = optimizer.optimize(model, trainset=trainset)\n```\n\n")
            
            f.write("## Optimization and Autonomous Interface Interaction\n\n")
            f.write("The `web_interaction_dataset.jsonl` contains examples specifically designed for training models to interact with web interfaces. Combined with DSPy's optimization capabilities, this allows for training autonomous agents that can:\n\n")
            f.write("1. Parse user queries related to biblical content\n")
            f.write("2. Determine the appropriate API action to take\n") 
            f.write("3. Extract the correct parameters from the query\n")
            f.write("4. Format and validate the response\n\n")
            
            f.write("### Example DSPy Agent Setup\n\n")
            f.write("```python\nclass BibleSearchAgent(dspy.Module):\n    def __init__(self):\n        super().__init__()\n        self.query_parser = dspy.ChainOfThought(\"context, query -> action, parameters\")\n        \n    def forward(self, query):\n        # Parse the query to determine action and parameters\n        parsed = self.query_parser(context=\"Biblical research assistant\", query=query)\n        \n        # Execute the appropriate action\n        if parsed.action == \"search_database\":\n            results = search_bible_database(**parsed.parameters)\n            return {\"results\": results}\n        elif parsed.action == \"lookup_strongs\":\n            definition = lookup_strongs_entry(**parsed.parameters)\n            return {\"definition\": definition}\n        # ... other actions\n```\n\n")
            
            f.write("## Generation\n\n")
            f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("To regenerate this data, run `python scripts/generate_dspy_training_data.py`\n")
        
        logger.info("DSPy training data generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in DSPy training data generation: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    main() 