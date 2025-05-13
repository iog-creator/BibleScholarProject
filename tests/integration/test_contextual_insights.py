# tests/integration/test_contextual_insights.py
import pytest
import requests
import json
import logging
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test the contextual insights API with database dependency
def test_contextual_insights_api(test_db_engine):
    """
    Test the contextual insights API for multiple verses and translations.
    Verifies JSON structure, required fields, translation variants, theological terms, and lexical data.
    """
    url = "http://localhost:5002/api/contextual_insights/insights"
    
    test_cases = [
        {"type": "verse", "reference": "John 1:1", "translation": "KJV"},
        {"type": "verse", "reference": "John 1:1", "translation": "TAGNT"},
        {"type": "verse", "reference": "Genesis 1:1", "translation": "ASV"},
        {"type": "verse", "reference": "Genesis 1:1", "translation": "TAHOT"},
        {"type": "verse", "reference": "Psalm 23:1", "translation": "KJV"},
        {"type": "topic", "reference": "Creation"},
        {"type": "text_snippet", "reference": "Let there be light"}
    ]
    
    expected_translations = ['ASV', 'KJV', 'TAGNT', 'TAHOT']
    
    with test_db_engine.connect() as conn:
        for payload in test_cases:
            logger.info(f"Testing payload: {payload}")
            
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Response for {payload['reference']}: {json.dumps(result, indent=2)}")
            except requests.RequestException as e:
                pytest.fail(f"API request failed for {payload['reference']}: {e}")
            
            # Validate JSON structure
            assert "insights" in result, f"Missing 'insights' key in response for {payload['reference']}"
            required_fields = [
                "summary",
                "theological_terms",
                "cross_references",
                "historical_context",
                "original_language_notes",
                "related_entities",
                "translation_variants",
                "lexical_data"
            ]
            for field in required_fields:
                assert field in result["insights"], f"Missing '{field}' in insights for {payload['reference']}"
            
            # Validate field types
            assert isinstance(result["insights"]["theological_terms"], dict), \
                f"'theological_terms' is not a dict for {payload['reference']}"
            assert isinstance(result["insights"]["cross_references"], list), \
                f"'cross_references' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["original_language_notes"], list), \
                f"'original_language_notes' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["related_entities"], dict), \
                f"'related_entities' is not a dict for {payload['reference']}"
            assert isinstance(result["insights"]["translation_variants"], list), \
                f"'translation_variants' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["lexical_data"], list), \
                f"'lexical_data' is not a list for {payload['reference']}"
            
            # Validate translations
            if payload["type"] == "verse":
                translations = [v["translation"] for v in result["insights"]["translation_variants"]]
                assert all(t in expected_translations for t in translations), \
                    f"Unexpected translations {translations} for {payload['reference']}"
                assert 'ESV' not in translations, f"ESV included in translations for {payload['reference']}"
                expected_translation = payload["translation"]
                assert any(v["translation"] == expected_translation for v in result["insights"]["translation_variants"]), \
                    f"Expected translation {expected_translation} not found in {translations} for {payload['reference']}"
            # For topic and text_snippet, translation_variants may be empty or minimal
            
            # Validate lexical data for verse inputs
            if payload["type"] == "verse":
                for lex_entry in result["insights"]["lexical_data"]:
                    assert all(key in lex_entry for key in ['word', 'strongs_id', 'lemma', 'transliteration', 'definition']), \
                        f"Missing keys in lexical_data entry for {payload['reference']}: {lex_entry}"
                    assert lex_entry['strongs_id'].startswith('H' if payload['reference'].startswith('Genesis') or payload['reference'].startswith('Psalm') else 'G'), \
                        f"Invalid Strong's ID format in lexical_data for {payload['reference']}"
            
            # Validate theological terms for specific verses
            if payload["reference"] == "Genesis 1:1":
                assert "Elohim" in result["insights"]["theological_terms"], \
                    f"Elohim (H430) missing in theological_terms for Genesis 1:1"
                result_db = conn.execute(
                    text("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words w
                    JOIN bible.verses v
                      ON w.book_name = v.book_name
                     AND w.chapter_num = v.chapter_num
                     AND w.verse_num = v.verse_num
                    WHERE w.strongs_id = 'H430'
                      AND v.book_name = 'Genesis'
                      AND v.chapter_num = 1
                      AND v.verse_num = 1
                    """ )
                )
                count = result_db.scalar()
                assert count > 0, "No Elohim (H430) found in database for Genesis 1:1"
                
                elohim_entry = next((entry for entry in result["insights"]["lexical_data"] if entry['strongs_id'] == 'H430'), None)
                assert elohim_entry, f"No lexical data for Elohim (H430) in Genesis 1:1"
                assert elohim_entry['lemma'] == 'אֱלֹהִים', f"Incorrect lemma for Elohim in Genesis 1:1"
            
            if payload["reference"] == "John 1:1":
                assert "Theos" in result["insights"]["theological_terms"], \
                    f"Theos (G2316) missing in theological_terms for John 1:1"
                theos_entry = next((entry for entry in result["insights"]["lexical_data"] if entry['strongs_id'] == 'G2316'), None)
                assert theos_entry, f"No lexical data for Theos (G2316) in John 1:1"
                assert theos_entry['lemma'] == 'θεός', f"Incorrect lemma for Theos in John 1:1"

            # Validate topic and text_snippet responses
            if payload["type"] == "topic" and payload["reference"] == "Creation":
                assert result["insights"]["summary"], "Summary should not be empty for topic 'Creation'"
                assert result["insights"]["cross_references"], "Cross-references should not be empty for topic 'Creation'"

            if payload["type"] == "text_snippet" and payload["reference"] == "Let there be light":
                assert result["insights"]["summary"], "Summary should not be empty for text_snippet 'Let there be light'"
                assert result["insights"]["cross_references"], "Cross-references should not be empty for text_snippet 'Let there be light'"

            # For topic and text_snippet, translation_variants and lexical_data should be empty lists
            if payload["type"] in ["topic", "text_snippet"]:
                assert result["insights"]["translation_variants"] == [], f"translation_variants should be empty for {payload['type']}"
                assert result["insights"]["lexical_data"] == [], f"lexical_data should be empty for {payload['type']}"

def test_contextual_insights_api_no_db():
    """
    Test the API without database dependency to ensure basic functionality.
    """
    url = "http://localhost:5002/api/contextual_insights/insights"
    payload = {"type": "verse", "reference": "Psalm 23:1", "translation": "KJV"}
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        assert "insights" in result, "Missing 'insights' key in response"
        assert "summary" in result["insights"], "Missing 'summary' in insights"
        assert "lexical_data" in result["insights"], "Missing 'lexical_data' in insights"
        assert isinstance(result["insights"]["lexical_data"], list), "'lexical_data' is not a list"
    except requests.RequestException as e:
        pytest.fail(f"API request failed: {e}") 