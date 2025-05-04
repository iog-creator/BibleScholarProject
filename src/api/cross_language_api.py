from flask import Blueprint, jsonify
import logging
from src.utils.db_utils import get_db_connection

api_blueprint = Blueprint('cross_language', __name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('cross_language_api.log'), logging.StreamHandler()]
)
logger = logging.getLogger('cross_language_api')

MAPPINGS = [
    {"hebrew": "יהוה", "greek": "θεός", "arabic": "الله", "strongs": "H3068"},
    {"hebrew": "אלהים", "greek": "θεός", "arabic": "الله", "strongs": "H430"}
]

@api_blueprint.route('/terms', methods=['GET'])
def get_cross_language_terms():
    results = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for mapping in MAPPINGS:
                # Hebrew count
                cur.execute(
                    "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s AND word_text = %s",
                    (mapping['strongs'], mapping['hebrew'])
                )
                hebrew_count = cur.fetchone()[0]
                # Greek count
                cur.execute(
                    "SELECT COUNT(*) FROM bible.greek_nt_words WHERE strongs_id = %s AND word_text = %s",
                    (mapping['strongs'], mapping['greek'])
                )
                greek_count = cur.fetchone()[0]
                # Arabic count
                cur.execute(
                    "SELECT COUNT(*) FROM bible.arabic_words WHERE arabic_word = %s",
                    (mapping['arabic'],)
                )
                arabic_count = cur.fetchone()[0]
                results.append({
                    "hebrew": mapping['hebrew'],
                    "greek": mapping['greek'],
                    "arabic": mapping['arabic'],
                    "strongs": mapping['strongs'],
                    "counts": {"hebrew": hebrew_count, "greek": greek_count, "arabic": arabic_count}
                })
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching cross-language terms: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close() 