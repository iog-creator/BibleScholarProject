"""
Utility functions for TVTMS processing.
"""

import logging
import os
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)

def setup_logging(log_file: str = 'etl_versification.log') -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode='w')
        ]
    )

# Book name mappings (abbreviated to full)
BOOK_NAME_MAPPINGS = {
    # Old Testament
    'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deu': 'Deuteronomy',
    'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
    '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
    'Ezr': 'Ezra', 'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
    'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Sng': 'Song of Solomon', 'Isa': 'Isaiah',
    'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Ezk': 'Ezekiel', 'Dan': 'Daniel',
    'Hos': 'Hosea', 'Joe': 'Joel', 'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah',
    'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah',
    'Hag': 'Haggai', 'Zec': 'Zechariah', 'Mal': 'Malachi',
    # New Testament
    'Mat': 'Matthew', 'Mar': 'Mark', 'Luk': 'Luke', 'Jhn': 'John',
    'Act': 'Acts', 'Rom': 'Romans', '1Co': '1 Corinthians', '2Co': '2 Corinthians',
    'Gal': 'Galatians', 'Eph': 'Ephesians', 'Php': 'Philippians', 'Col': 'Colossians',
    '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', '1Ti': '1 Timothy',
    '2Ti': '2 Timothy', 'Tit': 'Titus', 'Phm': 'Philemon', 'Heb': 'Hebrews',
    'Jas': 'James', '1Pe': '1 Peter', '2Pe': '2 Peter', '1Jn': '1 John',
    '2Jn': '2 John', '3Jn': '3 John', 'Jud': 'Jude', 'Rev': 'Revelation',
    # Additions to Esther
    'EstA': 'Additions to Esther', 'EstB': 'Additions to Esther',
    'EstC': 'Additions to Esther', 'EstD': 'Additions to Esther',
    'EstE': 'Additions to Esther', 'EstF': 'Additions to Esther',
    'Ade': 'Additions to Esther', 'Esg': 'Additions to Esther'
}

# Book name variations
BOOK_VARIATIONS = {
    'Psalm': 'Psalms', 'Ps': 'Psalms', 'Canticles': 'Song of Solomon',
    'Song': 'Song of Solomon', 'Eccles': 'Ecclesiastes', 'Lament': 'Lamentations',
    'Apocalypse': 'Revelation', 'Epistle of Jeremiah': 'Jeremiah',
    'Genesis': 'Genesis', 'Exodus': 'Exodus', 'Leviticus': 'Leviticus',
    'Numbers': 'Numbers', 'Deuteronomy': 'Deuteronomy', 'Joshua': 'Joshua',
    'Judges': 'Judges', 'Ruth': 'Ruth', '1 Samuel': '1 Samuel', '2 Samuel': '2 Samuel',
    '1 Kings': '1 Kings', '2 Kings': '2 Kings', '1 Chronicles': '1 Chronicles',
    '2 Chronicles': '2 Chronicles', 'Ezra': 'Ezra', 'Nehemiah': 'Nehemiah',
    'Esther': 'Esther', 'Job': 'Job', 'Psalms': 'Psalms', 'Proverbs': 'Proverbs',
    'Ecclesiastes': 'Ecclesiastes', 'Song of Solomon': 'Song of Solomon',
    'Isaiah': 'Isaiah', 'Jeremiah': 'Jeremiah', 'Lamentations': 'Lamentations',
    'Ezekiel': 'Ezekiel', 'Daniel': 'Daniel', 'Hosea': 'Hosea', 'Joel': 'Joel',
    'Amos': 'Amos', 'Obadiah': 'Obadiah', 'Jonah': 'Jonah', 'Micah': 'Micah',
    'Nahum': 'Nahum', 'Habakkuk': 'Habakkuk', 'Zephaniah': 'Zephaniah',
    'Haggai': 'Haggai', 'Zechariah': 'Zechariah', 'Malachi': 'Malachi',
    'Matthew': 'Matthew', 'Mark': 'Mark', 'Luke': 'Luke', 'John': 'John',
    'Acts': 'Acts', 'Romans': 'Romans', '1 Corinthians': '1 Corinthians',
    '2 Corinthians': '2 Corinthians', 'Galatians': 'Galatians',
    'Ephesians': 'Ephesians', 'Philippians': 'Philippians',
    'Colossians': 'Colossians', '1 Thessalonians': '1 Thessalonians',
    '2 Thessalonians': '2 Thessalonians', '1 Timothy': '1 Timothy',
    '2 Timothy': '2 Timothy', 'Titus': 'Titus', 'Philemon': 'Philemon',
    'Hebrews': 'Hebrews', 'James': 'James', '1 Peter': '1 Peter',
    '2 Peter': '2 Peter', '1 John': '1 John', '2 John': '2 John',
    '3 John': '3 John', 'Jude': 'Jude', 'Revelation': 'Revelation',
    'Additions to Esther': 'Additions to Esther'
}

def normalize_book_name(book: str) -> Optional[str]:
    """Normalize book name to full name."""
    if not book:
        return None
    
    # Try direct mapping from abbreviation to full name
    if book in BOOK_NAME_MAPPINGS:
        return BOOK_NAME_MAPPINGS[book]
    
    # Try variations
    book = book.strip()
    if book in BOOK_VARIATIONS:
        return BOOK_VARIATIONS[book]
    
    # Handle letter chapter books (e.g., EstA -> Additions to Esther)
    base_book = re.match(r'^([A-Z][a-z]+)([A-F])$', book)
    if base_book:
        book_name = base_book.group(1)
        if book_name in ['Est']:
            return 'Additions to Esther'
    
    # If the book name is already a full name, return it
    if book in set(BOOK_NAME_MAPPINGS.values()) or book in set(BOOK_VARIATIONS.values()):
        return book
    
    logger.warning(f"Unknown book name: {book}")
    return None 