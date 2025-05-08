"""
Bible Reference Parser

This module provides functions for parsing Bible references in various formats.
"""

import re
import logging
from typing import Tuple, Optional, List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Standard book name mapping (aliases to canonical names)
BOOK_ALIASES = {
    # Old Testament
    'gen': 'Genesis',
    'ge': 'Genesis',
    'gn': 'Genesis',
    'exo': 'Exodus',
    'ex': 'Exodus',
    'lev': 'Leviticus',
    'lv': 'Leviticus',
    'num': 'Numbers',
    'nm': 'Numbers',
    'nu': 'Numbers',
    'deut': 'Deuteronomy',
    'dt': 'Deuteronomy',
    'de': 'Deuteronomy',
    'josh': 'Joshua',
    'jos': 'Joshua',
    'jsh': 'Joshua',
    'judg': 'Judges',
    'jdg': 'Judges',
    'jg': 'Judges',
    'ruth': 'Ruth',
    'ru': 'Ruth',
    'rth': 'Ruth',
    '1 sam': '1 Samuel',
    '1sam': '1 Samuel',
    '1 sa': '1 Samuel',
    '1sa': '1 Samuel',
    'i sam': '1 Samuel',
    'i sa': '1 Samuel',
    '2 sam': '2 Samuel',
    '2sam': '2 Samuel',
    '2 sa': '2 Samuel',
    '2sa': '2 Samuel',
    'ii sam': '2 Samuel',
    'ii sa': '2 Samuel',
    '1 kings': '1 Kings',
    '1kings': '1 Kings',
    '1 ki': '1 Kings',
    '1ki': '1 Kings',
    'i kings': '1 Kings',
    'i ki': '1 Kings',
    '2 kings': '2 Kings',
    '2kings': '2 Kings',
    '2 ki': '2 Kings',
    '2ki': '2 Kings',
    'ii kings': '2 Kings',
    'ii ki': '2 Kings',
    '1 chron': '1 Chronicles',
    '1chron': '1 Chronicles',
    '1 ch': '1 Chronicles',
    '1ch': '1 Chronicles',
    'i chron': '1 Chronicles',
    'i ch': '1 Chronicles',
    '2 chron': '2 Chronicles',
    '2chron': '2 Chronicles',
    '2 ch': '2 Chronicles',
    '2ch': '2 Chronicles',
    'ii chron': '2 Chronicles',
    'ii ch': '2 Chronicles',
    'ezra': 'Ezra',
    'ez': 'Ezra',
    'neh': 'Nehemiah',
    'ne': 'Nehemiah',
    'esth': 'Esther',
    'est': 'Esther',
    'es': 'Esther',
    'job': 'Job',
    'jb': 'Job',
    'ps': 'Psalms',
    'psa': 'Psalms',
    'psalm': 'Psalms',
    'prov': 'Proverbs',
    'pr': 'Proverbs',
    'prv': 'Proverbs',
    'eccl': 'Ecclesiastes',
    'ecc': 'Ecclesiastes',
    'ec': 'Ecclesiastes',
    'song': 'Song of Solomon',
    'sos': 'Song of Solomon',
    'ss': 'Song of Solomon',
    'song of sol': 'Song of Solomon',
    'isa': 'Isaiah',
    'is': 'Isaiah',
    'jer': 'Jeremiah',
    'je': 'Jeremiah',
    'jr': 'Jeremiah',
    'lam': 'Lamentations',
    'la': 'Lamentations',
    'ezek': 'Ezekiel',
    'eze': 'Ezekiel',
    'ezk': 'Ezekiel',
    'dan': 'Daniel',
    'da': 'Daniel',
    'dn': 'Daniel',
    'hos': 'Hosea',
    'ho': 'Hosea',
    'joel': 'Joel',
    'jl': 'Joel',
    'amos': 'Amos',
    'am': 'Amos',
    'obad': 'Obadiah',
    'ob': 'Obadiah',
    'jonah': 'Jonah',
    'jon': 'Jonah',
    'mic': 'Micah',
    'mi': 'Micah',
    'mc': 'Micah',
    'nah': 'Nahum',
    'na': 'Nahum',
    'hab': 'Habakkuk',
    'hb': 'Habakkuk',
    'zeph': 'Zephaniah',
    'zep': 'Zephaniah',
    'zp': 'Zephaniah',
    'hag': 'Haggai',
    'hg': 'Haggai',
    'zech': 'Zechariah',
    'zec': 'Zechariah',
    'zc': 'Zechariah',
    'mal': 'Malachi',
    'ml': 'Malachi',
    
    # New Testament
    'matt': 'Matthew',
    'mt': 'Matthew',
    'mat': 'Matthew',
    'mark': 'Mark',
    'mk': 'Mark',
    'mr': 'Mark',
    'luke': 'Luke',
    'lk': 'Luke',
    'lu': 'Luke',
    'john': 'John',
    'jn': 'John',
    'jhn': 'John',
    'acts': 'Acts',
    'ac': 'Acts',
    'rom': 'Romans',
    'ro': 'Romans',
    'rm': 'Romans',
    '1 cor': '1 Corinthians',
    '1cor': '1 Corinthians',
    '1 co': '1 Corinthians',
    '1co': '1 Corinthians',
    'i cor': '1 Corinthians',
    'i co': '1 Corinthians',
    '2 cor': '2 Corinthians',
    '2cor': '2 Corinthians',
    '2 co': '2 Corinthians',
    '2co': '2 Corinthians',
    'ii cor': '2 Corinthians',
    'ii co': '2 Corinthians',
    'gal': 'Galatians',
    'ga': 'Galatians',
    'eph': 'Ephesians',
    'ep': 'Ephesians',
    'phil': 'Philippians',
    'php': 'Philippians',
    'pp': 'Philippians',
    'col': 'Colossians',
    'cl': 'Colossians',
    '1 thess': '1 Thessalonians',
    '1thess': '1 Thessalonians',
    '1 th': '1 Thessalonians',
    '1th': '1 Thessalonians',
    'i thess': '1 Thessalonians',
    'i th': '1 Thessalonians',
    '2 thess': '2 Thessalonians',
    '2thess': '2 Thessalonians',
    '2 th': '2 Thessalonians',
    '2th': '2 Thessalonians',
    'ii thess': '2 Thessalonians',
    'ii th': '2 Thessalonians',
    '1 tim': '1 Timothy',
    '1tim': '1 Timothy',
    '1 ti': '1 Timothy',
    '1ti': '1 Timothy',
    'i tim': '1 Timothy',
    'i ti': '1 Timothy',
    '2 tim': '2 Timothy',
    '2tim': '2 Timothy',
    '2 ti': '2 Timothy',
    '2ti': '2 Timothy',
    'ii tim': '2 Timothy',
    'ii ti': '2 Timothy',
    'titus': 'Titus',
    'tit': 'Titus',
    'ti': 'Titus',
    'philem': 'Philemon',
    'phm': 'Philemon',
    'phlm': 'Philemon',
    'heb': 'Hebrews',
    'he': 'Hebrews',
    'james': 'James',
    'jas': 'James',
    'jm': 'James',
    '1 pet': '1 Peter',
    '1pet': '1 Peter',
    '1 pe': '1 Peter',
    '1pe': '1 Peter',
    'i pet': '1 Peter',
    'i pe': '1 Peter',
    '2 pet': '2 Peter',
    '2pet': '2 Peter',
    '2 pe': '2 Peter',
    '2pe': '2 Peter',
    'ii pet': '2 Peter',
    'ii pe': '2 Peter',
    '1 john': '1 John',
    '1john': '1 John',
    '1 jn': '1 John',
    '1jn': '1 John',
    'i john': '1 John',
    'i jn': '1 John',
    '2 john': '2 John',
    '2john': '2 John',
    '2 jn': '2 John',
    '2jn': '2 John',
    'ii john': '2 John',
    'ii jn': '2 John',
    '3 john': '3 John',
    '3john': '3 John',
    '3 jn': '3 John',
    '3jn': '3 John',
    'iii john': '3 John',
    'iii jn': '3 John',
    'jude': 'Jude',
    'jud': 'Jude',
    'jd': 'Jude',
    'rev': 'Revelation',
    're': 'Revelation',
    'rv': 'Revelation',
}

# List of all canonical book names
CANONICAL_BOOKS = [
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
    '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
    'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
    'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
    'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
    'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
    'Haggai', 'Zechariah', 'Malachi',
    'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
    '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
    'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
    '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
    'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
    'Jude', 'Revelation'
]

def normalize_book_name(book_name: str) -> str:
    """
    Normalize a book name to its canonical form.
    
    Args:
        book_name: Book name to normalize
        
    Returns:
        Canonical book name or original if not recognized
    """
    # Convert to lowercase for case-insensitive matching
    book_lower = book_name.lower()
    
    # Check exact matches first
    for canonical in CANONICAL_BOOKS:
        if book_lower == canonical.lower():
            return canonical
    
    # Check aliases
    if book_lower in BOOK_ALIASES:
        return BOOK_ALIASES[book_lower]
    
    # If no match, return original
    return book_name

def parse_reference(reference: str) -> Optional[Tuple[str, int, int, Optional[int]]]:
    """
    Parse a Bible reference into its components.
    
    Args:
        reference: Bible reference string (e.g., "Genesis 1:1-3", "John 3:16")
        
    Returns:
        Tuple of (book_name, chapter, verse_start, verse_end) or None if invalid
    """
    try:
        # Common patterns:
        # "Genesis 1:1"
        # "Gen 1:1-3"
        # "Psalm 23"
        # "Matthew 5:3-10"
        
        # Basic regex to match reference patterns
        pattern = r'([1-3]?\s?[A-Za-z]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?'
        match = re.match(pattern, reference.strip())
        
        if not match:
            logger.warning(f"Failed to parse reference: {reference}")
            return None
        
        # Extract components
        book_raw, chapter_str, verse_start_str, verse_end_str = match.groups()
        
        # Normalize book name
        book_name = normalize_book_name(book_raw)
        
        # Convert to integers
        chapter = int(chapter_str)
        
        # If verse_start is None, it's a whole chapter reference
        if verse_start_str is None:
            verse_start = 1  # Start from verse 1
            verse_end = None  # All verses in the chapter
        else:
            verse_start = int(verse_start_str)
            verse_end = int(verse_end_str) if verse_end_str else verse_start
        
        return (book_name, chapter, verse_start, verse_end)
    
    except Exception as e:
        logger.error(f"Error parsing reference '{reference}': {e}")
        return None

def extract_references(text: str) -> List[str]:
    """
    Extract Bible references from a text.
    
    Args:
        text: Text to search for references
        
    Returns:
        List of reference strings found in the text
    """
    # Common reference patterns
    patterns = [
        r'([1-3]?\s?[A-Za-z]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?',  # Genesis 1:1-3
        r'([1-3]?\s?[A-Za-z]+)\.?\s+(\d+)(?::(\d+)(?:-(\d+))?)?'  # Gen. 1:1-3
    ]
    
    references = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            ref_text = match.group(0)
            if parse_reference(ref_text):  # Verify it's a valid reference
                references.append(ref_text)
    
    return references

def is_valid_reference(reference: str) -> bool:
    """
    Check if a string is a valid Bible reference.
    
    Args:
        reference: Reference string to check
        
    Returns:
        True if valid, False otherwise
    """
    return parse_reference(reference) is not None 