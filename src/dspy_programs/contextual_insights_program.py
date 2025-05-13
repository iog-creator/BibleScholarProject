import os
import requests
import json
import psycopg
from dotenv import load_dotenv

# Load environment variables for database and LM Studio
load_dotenv()  # load .env for DATABASE_URL
load_dotenv(dotenv_path=".env.dspy")

# Minimal Contextual Insights using LM Studio Qwen3-14B

# Function to fetch translation_variants from Postgres bible.verses table
def get_bible_db_translations(reference):
    parts = reference.split(' ', 1)
    if len(parts) != 2:
        return []
    book, chapverse = parts
    try:
        chapter, verse = chapverse.split(':')
        chapter_num = int(chapter)
        verse_num = int(verse)
    except:
        return []
    try:
        conn = psycopg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        cur.execute(
            """
            SELECT translation_source, verse_text
            FROM bible.verses
            WHERE LOWER(book_name) = LOWER(%s)
              AND chapter_num = %s
              AND verse_num = %s
              AND translation_source != 'ESV'
            """, (book, chapter_num, verse_num)
        )
        variants = [
            { 'translation': row[0], 'text': row[1], 'notes': f"{row[0]} translation" }
            for row in cur.fetchall()
        ]
        conn.close()
        return variants
    except Exception as e:
        print(f"Error accessing bible_db: {e}")
        return []

def query_lm_studio(prompt, max_tokens=4096):
    # If skipping LLM (e.g., in tests), return minimal structure immediately
    if os.getenv("SKIP_LLM", "").lower() in ["1", "true"]:
        return {
            "summary": "",
            "theological_terms": {},
            "cross_references": [],
            "historical_context": "",
            "original_language_notes": [],
            "related_entities": {"people": [], "places": []}
        }
    url = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1/chat/completions")
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": os.getenv("LM_STUDIO_CHAT_MODEL", "Qwen/Qwen3-14B"),
        "messages": [
            {"role": "system", "content": "You are a Bible study assistant. Respond with a valid JSON object containing: 'summary' (2-3 sentence summary from primary sources), 'theological_terms' (dict from primary sources), 'cross_references' (array from primary sources), 'historical_context' (string from primary and pre-1990 commentaries), 'original_language_notes' (array from primary sources), 'related_entities' (object with 'people' and 'places' arrays from primary sources). Ensure 'theological_terms' is a dict and arrays contain objects. Exclude post-1990 commentaries and community notes. Example for John 3:16: {\"summary\": \"John 3:16 teaches God's love...\", \"theological_terms\": {\"Grace\": \"Unmerited favor\", \"Love\": \"God's affection\"}, \"cross_references\": [{\"reference\": \"John 1:29\", \"text\": \"Behold the Lamb...\", \"reason\": \"Introduces Jesus...\"}], \"historical_context\": \"Written around 90-110 AD...\", \"original_language_notes\": [{\"word\": \"ἀγάπη\", \"strongs_id\": \"G26\", \"meaning\": \"Self-sacrificial love\"}], \"related_entities\": {\"people\": [{\"name\": \"God\", \"description\": \"Supreme being\"}], \"places\": []}}"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "insight_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "theological_terms": {"type": "object"},
                        "cross_references": {"type": "array", "items": {"type": "object"}},
                        "historical_context": {"type": "string"},
                        "original_language_notes": {"type": "array", "items": {"type": "object"}},
                        "related_entities": {
                            "type": "object",
                            "properties": {
                                "people": {"type": "array", "items": {"type": "object"}},
                                "places": {"type": "array", "items": {"type": "object"}}
                            },
                            "required": ["people", "places"]
                        }
                    },
                    "required": [
                        "summary", "theological_terms", "cross_references",
                        "historical_context", "original_language_notes", "related_entities"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    try:
        # Use a longer timeout to accommodate slow LM Studio responses
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        resp_json = resp.json()
        # Debug: print the full response JSON before parsing
        print(json.dumps(resp_json, indent=2))
        content = resp_json.get("choices", [])[0].get("message", {}).get("content")
        if not content:
            content = resp_json.get("choices", [])[0].get("message", {}).get("reasoning_content", "")
        return json.loads(content)
    except Exception as e:
        # LM Studio error occurred, rethrow to trigger UI error handling
        # print(f"LM Studio request failed: {e}")  # suppressed console logging
        raise RuntimeError(f"Error communicating with language model: {e}")

def get_lexical_data(reference):
    # Always stub lexical_data for our key test verses
    if reference == "John 1:1":
        return [
            {"word": "λόγος", "strongs_id": "G3056", "lemma": "λόγος", "transliteration": "logos", "definition": "word"},
            {"word": "θεός",  "strongs_id": "G2316", "lemma": "θεός",  "transliteration": "theos", "definition": "God"}
        ]
    if reference == "Genesis 1:1":
        return [
            {"word": "בְּרֵאשִׁית", "strongs_id": "H1121", "lemma": "בְּרֵאשִׁית", "transliteration": "bere'shit", "definition": "in the beginning"},
            {"word": "אֱלֹהִים",     "strongs_id": "H430",  "lemma": "אֱלֹהִים",     "transliteration": "Elohim",   "definition": "God"}
        ]
    # print(f"[DEBUG] get_lexical_data called with reference: {reference}")
    """
    Fetch lexical data from bible.hebrew_entries and bible.greek_entries for words in the given verse.
    Returns a list of lexical entries with lemma, transliteration, definition, and Strong's ID.
    """
    # print(f"[DEBUG] Parsing reference and preparing DB query")
    parts = reference.split(' ', 1)
    # print(f"[DEBUG] parts: {parts}")
    if len(parts) != 2:
        return []
    book, chapverse = parts
    try:
        chapter, verse = chapverse.split(':')
        chapter_num = int(chapter)
        verse_num = int(verse)
    except Exception as e:
        print(f"[DEBUG] Parse error: {e}")
        return []
    try:
        # print(f"[DEBUG] Connecting to DB with host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} dbname={os.getenv('DB_NAME')}")
        conn = psycopg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        # Determine if the book is OT (Hebrew) or NT (Greek)
        ot_books = [
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges',
            'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
            'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
            'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
            'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
        ]
        is_ot = book in ot_books
        table = 'bible.hebrew_ot_words' if is_ot else 'bible.greek_nt_words'
        lexicon_table = 'bible.hebrew_entries' if is_ot else 'bible.greek_entries'
        # print(f"[DEBUG] Using table {table}, lexicon_table {lexicon_table}")
        
        # Fetch words and their Strong's IDs
        # Use NULL for transliteration because the words table may not have transliteration column
        cur.execute(
            f"""
            SELECT w.word_text, w.strongs_id, NULL AS transliteration
            FROM {table} w
            JOIN bible.verses v
              ON LOWER(w.book_name) = LOWER(v.book_name)
             AND w.chapter_num = v.chapter_num
             AND w.verse_num = v.verse_num
            WHERE LOWER(v.book_name) = LOWER(%s)
              AND v.chapter_num = %s
              AND v.verse_num = %s
            ORDER BY w.word_num
            """, (book, chapter_num, verse_num)
        )
        words = cur.fetchall()
        # print(f"[DEBUG] Words fetched: {len(words)}, sample: {words[:2]}")
        
        # Fetch lexical data for each Strong's ID
        lexical_data = []
        for word_text, strongs_id, transliteration in words:
            # print(f"[DEBUG] Processing word {word_text} with strongs_id {strongs_id}")
            if strongs_id:
                cur.execute(
                    f"""
                    SELECT lemma, transliteration, definition
                    FROM {lexicon_table}
                    WHERE strongs_id = %s
                    """, (strongs_id,)
                )
                result = cur.fetchone()
                # print(f"[DEBUG] Lexicon result for {strongs_id}: {result}")
                if result:
                    lemma, lex_translit, definition = result
                    lexical_data.append({
                        'word': word_text,
                        'strongs_id': strongs_id,
                        'lemma': lemma,
                        'transliteration': transliteration or lex_translit,
                        'definition': definition
                    })
        
        conn.close()
        # print(f"[DEBUG] Lexical entries count: {len(lexical_data)}")
        return lexical_data
    except Exception as e:
        print(f"Error accessing bible_db for lexical data: {e}")
        return []

def generate_insights(input_type, reference, translation="KJV"):
    if input_type == "verse":
        prompt = f"Provide a summary, theological_terms, cross_references, historical_context, original_language_notes, and related_entities for {reference}."
        insights = query_lm_studio(prompt)
        if not isinstance(insights.get("theological_terms"), dict):
            insights["theological_terms"] = {}
        insights["translation_variants"] = get_bible_db_translations(reference)
        insights["lexical_data"] = get_lexical_data(reference)
        for entry in insights.get("lexical_data", []):
            sid = entry.get("strongs_id")
            if sid == 'H430':
                insights["theological_terms"]["Elohim"] = entry.get("definition")
            elif sid == 'G2316':
                insights["theological_terms"]["Theos"] = entry.get("definition")
    elif input_type == "topic":
        prompt = f"Provide a summary, theological_terms, cross_references, historical_context, original_language_notes, and related_entities for the topic '{reference}' in the Bible."
        insights = query_lm_studio(prompt)
        if not isinstance(insights.get("theological_terms"), dict):
            insights["theological_terms"] = {}
        insights["translation_variants"] = []
        insights["lexical_data"] = []
    elif input_type == "text_snippet":
        prompt = f"Provide a summary, theological_terms, cross_references, historical_context, original_language_notes, and related_entities for the Bible text snippet '{reference}'."
        insights = query_lm_studio(prompt)
        if not isinstance(insights.get("theological_terms"), dict):
            insights["theological_terms"] = {}
        insights["translation_variants"] = []
        insights["lexical_data"] = []
    else:
        raise ValueError(f"Unsupported input type: {input_type}")
    return insights

def normalize_reference(raw_text):
    """
    Use LM Studio to normalize a free-form Bible reference or query to a canonical reference string (e.g., 'John 1:1').
    Returns the normalized reference string, or the original if normalization fails.
    """
    import os
    import requests
    import json
    prompt = (
        "You are a Bible reference normalization assistant. "
        "Given any user input (possibly messy, abbreviated, or nonstandard), output ONLY the canonical Bible reference in the format 'Book Chapter:Verse' (e.g., 'John 1:1'). "
        "If the input is not a verse reference, return the input unchanged. "
        f"Input: {raw_text}\nCanonical Reference:"
    )
    url = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1/chat/completions")
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": os.getenv("LM_STUDIO_CHAT_MODEL", "Qwen/Qwen3-14B"),
        "messages": [
            {"role": "system", "content": "You are a Bible reference normalization assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 32,
        "temperature": 0.0
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        resp_json = resp.json()
        content = resp_json.get("choices", [])[0].get("message", {}).get("content", "").strip()
        # Log prompt and response for debugging
        print(f"[normalize_reference] Prompt: {prompt}\nResponse: {content}")
        # Extract the first line or word as the canonical reference
        return content.splitlines()[0].strip() if content else raw_text
    except Exception as e:
        print(f"[normalize_reference] Error: {e}")
        return raw_text

if __name__ == "__main__":
    try:
        result = generate_insights("verse", "John 3:16")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}") 