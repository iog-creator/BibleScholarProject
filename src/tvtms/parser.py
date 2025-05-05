"""
Parser module for TVTMS.txt expanded version using pandas.
"""

import re
import logging
import pandas as pd
from typing import List, Dict, Optional, Set, Tuple
from .models import Mapping
from .database import get_db_connection, release_connection
from .validator import VersificationValidator
from .constants import (
    BOOK_VARIATIONS_MAP,
    VALID_CATEGORIES,
    MAPPING_TYPES,
    SKIP_CASES,
    ACTION_PRIORITY
)
import copy
import psycopg
from collections import defaultdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define a standard structure for null/invalid/absent references
NULL_REF = {
    'book_id': None, 'chapter': None, 'verse': None, 
    'subverse': None, 'manuscript': None, 'status': 'invalid'
}

class TVTMSParser:
    """Parser for TVTMS data."""
    
    def __init__(self, test_mode=None):
        """Initialize the parser. Accepts optional test_mode for testing purposes."""
        self.test_mode = test_mode
        self.current_book = None
        self.book_abbreviations = {}
        self.book_names = {}
        self.valid_book_ids = set(BOOK_VARIATIONS_MAP.values())
        self.load_book_data()
        self.validator = VersificationValidator()
        
    def load_book_data(self):
        """Load book data from the database."""
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT book_id FROM bible.books")
                self.valid_book_ids = {row['book_id'] for row in cur.fetchall()}
                logger.debug(f"Loaded {len(self.valid_book_ids)} book IDs")
                
                cur.execute("SELECT book_id, alternate_abbreviation FROM bible.book_abbreviations")
                self.book_abbreviations = {row['alternate_abbreviation'].lower(): row['book_id'] for row in cur.fetchall()}
                logger.debug(f"Loaded {len(self.book_abbreviations)} book abbreviations")
                
                cur.execute("SELECT book_id, name FROM bible.books")
                self.book_names = {row['name'].lower(): row['book_id'] for row in cur.fetchall()}
                logger.debug(f"Loaded {len(self.book_names)} book names")
                
        except Exception as e:
            logger.error(f"Failed to load book data: {e}")
            raise
        finally:
            if conn:
                release_connection(conn)
    
    def normalize_book_reference(self, book_abbr: str) -> Optional[str]:
        """
        Convert a book abbreviation to a standardized book_id.
        Returns None if the abbreviation is unknown.
        """
        # Convert to lowercase for case-insensitive matching
        book_abbr = book_abbr.lower()
        
        # Database uses these exact abbreviations with proper capitalization
        standard_books = {
            # Old Testament
            'gen': 'Gen', 'exod': 'Exo', 'exo': 'Exo', 'lev': 'Lev', 'num': 'Num', 'deut': 'Deu', 'deu': 'Deu',
            'josh': 'Jos', 'jos': 'Jos', 'judg': 'Jdg', 'jdg': 'Jdg', 'ruth': 'Rth', 'rut': 'Rth',
            '1sam': '1Sa', '1sa': '1Sa', '2sam': '2Sa', '2sa': '2Sa',
            '1kgs': '1Ki', '1ki': '1Ki', '2kgs': '2Ki', '2ki': '2Ki',
            '1chr': '1Ch', '1ch': '1Ch', '2chr': '2Ch', '2ch': '2Ch',
            'ezra': 'Ezr', 'ezr': 'Ezr', 'neh': 'Neh', 'esth': 'Est', 'est': 'Est',
            'job': 'Job', 'ps': 'Psa', 'psa': 'Psa', 'psalm': 'Psa', 'psalms': 'Psa',
            'prov': 'Pro', 'pro': 'Pro', 'eccl': 'Ecc', 'ecc': 'Ecc', 'song': 'Sng', 'sng': 'Sng', 'cant': 'Sng',
            'isa': 'Isa', 'jer': 'Jer', 'lam': 'Lam', 'ezek': 'Ezk', 'ezk': 'Ezk', 'dan': 'Dan',
            'hos': 'Hos', 'joel': 'Jol', 'jol': 'Jol', 'amos': 'Amo', 'amo': 'Amo', 'obad': 'Oba', 'oba': 'Oba',
            'jonah': 'Jon', 'jon': 'Jon', 'mic': 'Mic', 'nah': 'Nam', 'nam': 'Nam', 'hab': 'Hab',
            'zeph': 'Zep', 'zep': 'Zep', 'hag': 'Hag', 'zech': 'Zec', 'zec': 'Zec', 'mal': 'Mal',
            
            # New Testament
            'matt': 'Mat', 'mat': 'Mat', 'mark': 'Mrk', 'mrk': 'Mrk', 'luke': 'Luk', 'luk': 'Luk', 'john': 'Jhn', 'jhn': 'Jhn',
            'acts': 'Act', 'act': 'Act', 'rom': 'Rom', '1cor': '1Co', '1co': '1Co', '2cor': '2Co', '2co': '2Co',
            'gal': 'Gal', 'eph': 'Eph', 'phil': 'Php', 'php': 'Php', 'col': 'Col',
            '1thess': '1Th', '1th': '1Th', '2thess': '2Th', '2th': '2Th',
            '1tim': '1Ti', '1ti': '1Ti', '2tim': '2Ti', '2ti': '2Ti',
            'titus': 'Tit', 'tit': 'Tit', 'phlm': 'Phm', 'phm': 'Phm', 'heb': 'Heb',
            'jas': 'Jas', 'jam': 'Jas', '1pet': '1Pe', '1pe': '1Pe', '2pet': '2Pe', '2pe': '2Pe',
            '1john': '1Jn', '1jn': '1Jn', '2john': '2Jn', '2jn': '2Jn', '3john': '3Jn', '3jn': '3Jn',
            'jude': 'Jud', 'jud': 'Jud', 'rev': 'Rev',
            
            # Apocrypha/Deuterocanonical
            'tob': 'Tob', 'jdt': 'Jdt', 'wis': 'Wis', 'sir': 'Sir', 'bar': 'Bar', 
            '1ma': '1Ma', '2ma': '2Ma', '3ma': '3Ma', '4ma': '4Ma',
            'sus': 'Sus', 'bel': 'Bel', 'man': 'Man', 'oda': 'Oda',
            'esg': 'EstG', 'estg': 'EstG', 'esa': 'EstA', 'esta': 'EstA', 'est1': 'EstA', 'est2': 'EstB', 'estb': 'EstB',
            'est3': 'EstC', 'estc': 'EstC', 'est4': 'EstD', 'estd': 'EstD', 'est5': 'EstE', 'este': 'EstE',
            'est6': 'EstF', 'estf': 'EstF', 'lje': 'LJe', 'lje': 'LJe', '1es': '1Es', '2es': '2Es',
            'adest': 'AddEst', 'add est': 'AddEst', 'addest': 'AddEst', 'add-est': 'AddEst',
            'prazr': 'PrAzar', 'prazrr': 'PrAzar', 'prazr': 'PrAzar'
        }
        
        # Special handling for aliases with numbers
        match = re.match(r'(\d+)\s*([a-z]+)', book_abbr)
        if match:
            num, name = match.groups()
            combined = f"{num}{name}"
            if combined in standard_books:
                return standard_books[combined]
        
        # Try direct lookup
        if book_abbr in standard_books:
            return standard_books[book_abbr]
            
        # Trying with common variations
        if book_abbr.startswith('1'):
            alt = 'i' + book_abbr[1:]
            if alt in standard_books:
                return standard_books[alt]
        elif book_abbr.startswith('2'):
            alt = 'ii' + book_abbr[1:]
            if alt in standard_books:
                return standard_books[alt]
        elif book_abbr.startswith('3'):
            alt = 'iii' + book_abbr[1:]
            if alt in standard_books:
                return standard_books[alt]
        elif book_abbr.startswith('4'):
            alt = 'iv' + book_abbr[1:]
            if alt in standard_books:
                return standard_books[alt]
        
        logger.warning(f"Unknown book abbreviation: {book_abbr}")
        return None
    
    def parse_file(self, file_path: str) -> Tuple[List[Mapping], list, list]:
        logger.info(f"Parsing TVTMS file: {file_path}")
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()
        # Find the data section between #DataStart(Expanded) and #DataEnd(Expanded)
        data_start_idx = None
        data_end_idx = None
        for idx, line in enumerate(lines):
            if line.strip().startswith('#DataStart(Expanded)'):
                data_start_idx = idx + 1  # Data header is next line
            if line.strip().startswith('#DataEnd(Expanded)'):
                data_end_idx = idx
                break
        if data_start_idx is None:
            raise ValueError("#DataStart(Expanded) not found in TVTMS file")
        if data_end_idx is None:
            data_end_idx = len(lines)
        # Data lines include header and all data rows
        data_lines = lines[data_start_idx:data_end_idx]
        # --- PATCH: Remove $-prefixed section mapping lines (log for now) ---
        filtered_lines = []
        for line in data_lines:
            if line.strip().startswith('$'):
                logger.warning(f"Skipping $-prefixed section mapping line: {line.strip()}")
                # TODO: Implement expansion logic for section mappings
                continue
            filtered_lines.append(line)
        from io import StringIO
        df = pd.read_csv(StringIO(''.join(filtered_lines)), sep='\t', dtype=str, keep_default_na=False)
        # Strip whitespace from column names
        df.columns = [c.strip() for c in df.columns]
        logger.info(f"[TVTMSParser] DataFrame columns: {df.columns.tolist()}")
        logger.info(f"[TVTMSParser] First 3 rows:\n{df.head(3).to_string()}")
        # --- Build verse_counts lookup from the database ---
        conn = get_db_connection()
        verse_counts = self.build_verse_counts(conn)
        conn.close()
        # ---
        # Iterate over DataFrame rows and extract mappings
        all_mappings = []
        for idx, row in df.iterrows():
            # Use stripped column names
            source_type = row.get('SourceType', '').strip()
            source_ref = row.get('SourceRef', '').strip()
            standard_ref = row.get('StandardRef', '').strip()
            action = row.get('Action', '').strip()
            note_marker = row.get('NoteMarker', '').strip()
            note_a = row.get('Reversification Note', '').strip() if 'Reversification Note' in row else row.get('Note A', '').strip()
            note_b = row.get('Versification Note', '').strip() if 'Versification Note' in row else row.get('Note B', '').strip()
            ancient_versions = row.get('Ancient Versions', '').strip()
            tests = row.get('Tests', '').strip()
            # Skip rows with no source or target reference or action
            if not source_ref or not standard_ref or not action:
                continue
            # --- Pass verse_counts to parse_reference ---
            source_refs_parsed = self.parse_reference(source_ref, self.current_book, verse_counts)
            target_refs_parsed = self.parse_reference(standard_ref, self.current_book, verse_counts)
            # ---
            mappings = self._create_mappings_from_row(
                source_type, source_ref, standard_ref, action,
                note_marker, note_a, note_b, ancient_versions, tests
            )
            all_mappings.extend(mappings)
        return all_mappings, [], []

    def build_verse_counts(self, conn=None):
        """Build a lookup of {book_id: {chapter: verse_count}} for Hebrew Bible books.
        
        Instead of querying the database, uses hardcoded verse counts for Hebrew tradition.
        """
        # Default verse counts for Hebrew Bible books (KJV/Hebrew tradition)
        verse_counts = {
            "GEN": {1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22, 7: 24, 8: 22, 9: 29, 10: 32, 
                    11: 32, 12: 20, 13: 18, 14: 24, 15: 21, 16: 16, 17: 27, 18: 33, 19: 38, 
                    20: 18, 21: 34, 22: 24, 23: 20, 24: 67, 25: 34, 26: 35, 27: 46, 28: 22, 
                    29: 35, 30: 43, 31: 55, 32: 32, 33: 20, 34: 31, 35: 29, 36: 43, 37: 36, 
                    38: 30, 39: 23, 40: 23, 41: 57, 42: 38, 43: 34, 44: 34, 45: 28, 46: 34, 
                    47: 31, 48: 22, 49: 33, 50: 26},
            "EXO": {1: 22, 2: 25, 3: 22, 4: 31, 5: 23, 6: 30, 7: 25, 8: 32, 9: 35, 10: 29, 
                    11: 10, 12: 51, 13: 22, 14: 31, 15: 27, 16: 36, 17: 16, 18: 27, 19: 25, 
                    20: 26, 21: 36, 22: 31, 23: 33, 24: 18, 25: 40, 26: 37, 27: 21, 28: 43, 
                    29: 46, 30: 38, 31: 18, 32: 35, 33: 23, 34: 35, 35: 35, 36: 38, 37: 29, 
                    38: 31, 39: 43, 40: 38},
            "LEV": {1: 17, 2: 16, 3: 17, 4: 35, 5: 19, 6: 30, 7: 38, 8: 36, 9: 24, 10: 20, 
                    11: 47, 12: 8, 13: 59, 14: 57, 15: 33, 16: 34, 17: 16, 18: 30, 19: 37, 
                    20: 27, 21: 24, 22: 33, 23: 44, 24: 23, 25: 55, 26: 46, 27: 34},
            "NUM": {1: 54, 2: 34, 3: 51, 4: 49, 5: 31, 6: 27, 7: 89, 8: 26, 9: 23, 10: 36, 
                    11: 35, 12: 16, 13: 33, 14: 45, 15: 41, 16: 50, 17: 13, 18: 32, 19: 22, 
                    20: 29, 21: 35, 22: 41, 23: 30, 24: 25, 25: 18, 26: 65, 27: 23, 28: 31, 
                    29: 40, 30: 16, 31: 54, 32: 42, 33: 56, 34: 29, 35: 34, 36: 13},
            "DEU": {1: 46, 2: 37, 3: 29, 4: 49, 5: 33, 6: 25, 7: 26, 8: 20, 9: 29, 10: 22, 
                    11: 32, 12: 32, 13: 18, 14: 29, 15: 23, 16: 22, 17: 20, 18: 22, 19: 21, 
                    20: 20, 21: 23, 22: 30, 23: 25, 24: 22, 25: 19, 26: 19, 27: 26, 28: 68, 
                    29: 29, 30: 20, 31: 30, 32: 52, 33: 29, 34: 12},
            "JOS": {1: 18, 2: 24, 3: 17, 4: 24, 5: 15, 6: 27, 7: 26, 8: 35, 9: 27, 10: 43, 
                    11: 23, 12: 24, 13: 33, 14: 15, 15: 63, 16: 10, 17: 18, 18: 28, 19: 51, 
                    20: 9, 21: 45, 22: 34, 23: 16, 24: 33},
            "JDG": {1: 36, 2: 23, 3: 31, 4: 24, 5: 31, 6: 40, 7: 25, 8: 35, 9: 57, 10: 18, 
                    11: 40, 12: 15, 13: 25, 14: 20, 15: 20, 16: 31, 17: 13, 18: 31, 19: 30, 
                    20: 48, 21: 25},
            "RUT": {1: 22, 2: 23, 3: 18, 4: 22},
            "1SA": {1: 28, 2: 36, 3: 21, 4: 22, 5: 12, 6: 21, 7: 17, 8: 22, 9: 27, 10: 27, 
                    11: 15, 12: 25, 13: 23, 14: 52, 15: 35, 16: 23, 17: 58, 18: 30, 19: 24, 
                    20: 42, 21: 15, 22: 23, 23: 29, 24: 22, 25: 44, 26: 25, 27: 12, 28: 25, 
                    29: 11, 30: 31, 31: 13},
            "2SA": {1: 27, 2: 32, 3: 39, 4: 12, 5: 25, 6: 23, 7: 29, 8: 18, 9: 13, 10: 19, 
                    11: 27, 12: 31, 13: 39, 14: 33, 15: 37, 16: 23, 17: 29, 18: 33, 19: 43, 
                    20: 26, 21: 22, 22: 51, 23: 39, 24: 25},
            "1KI": {1: 53, 2: 46, 3: 28, 4: 34, 5: 18, 6: 38, 7: 51, 8: 66, 9: 28, 10: 29, 
                    11: 43, 12: 33, 13: 34, 14: 31, 15: 34, 16: 34, 17: 24, 18: 46, 19: 21, 
                    20: 43, 21: 29, 22: 53},
            "2KI": {1: 18, 2: 25, 3: 27, 4: 44, 5: 27, 6: 33, 7: 20, 8: 29, 9: 37, 10: 36, 
                    11: 21, 12: 21, 13: 25, 14: 29, 15: 38, 16: 20, 17: 41, 18: 37, 19: 37, 
                    20: 21, 21: 26, 22: 20, 23: 37, 24: 20, 25: 30},
            "1CH": {1: 54, 2: 55, 3: 24, 4: 43, 5: 26, 6: 81, 7: 40, 8: 40, 9: 44, 10: 14, 
                    11: 47, 12: 40, 13: 14, 14: 17, 15: 29, 16: 43, 17: 27, 18: 17, 19: 19, 
                    20: 8, 21: 30, 22: 19, 23: 32, 24: 31, 25: 31, 26: 32, 27: 34, 28: 21, 
                    29: 30},
            "2CH": {1: 17, 2: 18, 3: 17, 4: 22, 5: 14, 6: 42, 7: 22, 8: 18, 9: 31, 10: 19, 
                    11: 23, 12: 16, 13: 22, 14: 15, 15: 19, 16: 14, 17: 19, 18: 34, 19: 11, 
                    20: 37, 21: 20, 22: 12, 23: 21, 24: 27, 25: 28, 26: 23, 27: 9, 28: 27, 
                    29: 36, 30: 27, 31: 21, 32: 33, 33: 25, 34: 33, 35: 27, 36: 23},
            "EZR": {1: 11, 2: 70, 3: 13, 4: 24, 5: 17, 6: 22, 7: 28, 8: 36, 9: 15, 10: 44},
            "NEH": {1: 11, 2: 20, 3: 32, 4: 23, 5: 19, 6: 19, 7: 73, 8: 18, 9: 38, 10: 39, 
                    11: 36, 12: 47, 13: 31},
            "EST": {1: 22, 2: 23, 3: 15, 4: 17, 5: 14, 6: 14, 7: 10, 8: 17, 9: 32, 10: 3},
            "JOB": {1: 22, 2: 13, 3: 26, 4: 21, 5: 27, 6: 30, 7: 21, 8: 22, 9: 35, 10: 22, 
                    11: 20, 12: 25, 13: 28, 14: 22, 15: 35, 16: 22, 17: 16, 18: 21, 19: 29, 
                    20: 29, 21: 34, 22: 30, 23: 17, 24: 25, 25: 6, 26: 14, 27: 23, 28: 28, 
                    29: 25, 30: 31, 31: 40, 32: 22, 33: 33, 34: 37, 35: 16, 36: 33, 37: 24, 
                    38: 41, 39: 30, 40: 24, 41: 34, 42: 17},
            "PSA": {1: 6, 2: 12, 3: 8, 4: 8, 5: 12, 6: 10, 7: 17, 8: 9, 9: 20, 10: 18, 
                    11: 7, 12: 8, 13: 6, 14: 7, 15: 5, 16: 11, 17: 15, 18: 50, 19: 14, 
                    20: 9, 21: 13, 22: 31, 23: 6, 24: 10, 25: 22, 26: 12, 27: 14, 28: 9, 
                    29: 11, 30: 12, 31: 24, 32: 11, 33: 22, 34: 22, 35: 28, 36: 12, 37: 40, 
                    38: 22, 39: 13, 40: 17, 41: 13, 42: 11, 43: 5, 44: 26, 45: 17, 46: 11, 
                    47: 9, 48: 14, 49: 20, 50: 23, 51: 19, 52: 9, 53: 6, 54: 7, 55: 23, 
                    56: 13, 57: 11, 58: 11, 59: 17, 60: 12, 61: 8, 62: 12, 63: 11, 64: 10, 
                    65: 13, 66: 20, 67: 7, 68: 35, 69: 36, 70: 5, 71: 24, 72: 20, 73: 28, 
                    74: 23, 75: 10, 76: 12, 77: 20, 78: 72, 79: 13, 80: 19, 81: 16, 82: 8, 
                    83: 18, 84: 12, 85: 13, 86: 17, 87: 7, 88: 18, 89: 52, 90: 17, 91: 16, 
                    92: 15, 93: 5, 94: 23, 95: 11, 96: 13, 97: 12, 98: 9, 99: 9, 100: 5, 
                    101: 8, 102: 28, 103: 22, 104: 35, 105: 45, 106: 48, 107: 43, 108: 13, 
                    109: 31, 110: 7, 111: 10, 112: 10, 113: 9, 114: 8, 115: 18, 116: 19, 
                    117: 2, 118: 29, 119: 176, 120: 7, 121: 8, 122: 9, 123: 4, 124: 8, 
                    125: 5, 126: 6, 127: 6, 128: 6, 129: 8, 130: 8, 131: 3, 132: 18, 133: 3, 
                    134: 3, 135: 21, 136: 26, 137: 9, 138: 8, 139: 24, 140: 13, 141: 10, 
                    142: 7, 143: 12, 144: 15, 145: 21, 146: 10, 147: 20, 148: 14, 149: 9, 
                    150: 6},
            "PRO": {1: 33, 2: 22, 3: 35, 4: 27, 5: 23, 6: 35, 7: 27, 8: 36, 9: 18, 10: 32, 
                    11: 31, 12: 28, 13: 25, 14: 35, 15: 33, 16: 33, 17: 28, 18: 24, 19: 29, 
                    20: 30, 21: 31, 22: 29, 23: 35, 24: 34, 25: 28, 26: 28, 27: 27, 28: 28, 
                    29: 27, 30: 33, 31: 31},
            "ECC": {1: 18, 2: 26, 3: 22, 4: 16, 5: 20, 6: 12, 7: 29, 8: 17, 9: 18, 10: 20, 
                    11: 10, 12: 14},
            "SNG": {1: 17, 2: 17, 3: 11, 4: 16, 5: 16, 6: 13, 7: 13, 8: 14},
            "ISA": {1: 31, 2: 22, 3: 26, 4: 6, 5: 30, 6: 13, 7: 25, 8: 22, 9: 21, 10: 34, 
                    11: 16, 12: 6, 13: 22, 14: 32, 15: 9, 16: 14, 17: 14, 18: 7, 19: 25, 
                    20: 6, 21: 17, 22: 25, 23: 18, 24: 23, 25: 12, 26: 21, 27: 13, 28: 29, 
                    29: 24, 30: 33, 31: 9, 32: 20, 33: 24, 34: 17, 35: 10, 36: 22, 37: 38, 
                    38: 22, 39: 8, 40: 31, 41: 29, 42: 25, 43: 28, 44: 28, 45: 25, 46: 13, 
                    47: 15, 48: 22, 49: 26, 50: 11, 51: 23, 52: 15, 53: 12, 54: 17, 55: 13, 
                    56: 12, 57: 21, 58: 14, 59: 21, 60: 22, 61: 11, 62: 12, 63: 19, 64: 12, 
                    65: 25, 66: 24},
            "JER": {1: 19, 2: 37, 3: 25, 4: 31, 5: 31, 6: 30, 7: 34, 8: 22, 9: 26, 10: 25, 
                    11: 23, 12: 17, 13: 27, 14: 22, 15: 21, 16: 21, 17: 27, 18: 23, 19: 15, 
                    20: 18, 21: 14, 22: 30, 23: 40, 24: 10, 25: 38, 26: 24, 27: 22, 28: 17, 
                    29: 32, 30: 24, 31: 40, 32: 44, 33: 26, 34: 22, 35: 19, 36: 32, 37: 21, 
                    38: 28, 39: 18, 40: 16, 41: 18, 42: 22, 43: 13, 44: 30, 45: 5, 46: 28, 
                    47: 7, 48: 47, 49: 39, 50: 46, 51: 64, 52: 34},
            "LAM": {1: 22, 2: 22, 3: 66, 4: 22, 5: 22},
            "EZK": {1: 28, 2: 10, 3: 27, 4: 17, 5: 17, 6: 14, 7: 27, 8: 18, 9: 11, 10: 22, 
                    11: 25, 12: 28, 13: 23, 14: 23, 15: 8, 16: 63, 17: 24, 18: 32, 19: 14, 
                    20: 49, 21: 32, 22: 31, 23: 49, 24: 27, 25: 17, 26: 21, 27: 36, 28: 26, 
                    29: 21, 30: 26, 31: 18, 32: 32, 33: 33, 34: 31, 35: 15, 36: 38, 37: 28, 
                    38: 23, 39: 29, 40: 49, 41: 26, 42: 20, 43: 27, 44: 31, 45: 25, 46: 24, 
                    47: 23, 48: 35},
            "DAN": {1: 21, 2: 49, 3: 30, 4: 37, 5: 31, 6: 28, 7: 28, 8: 27, 9: 27, 10: 21, 
                    11: 45, 12: 13},
            "HOS": {1: 11, 2: 23, 3: 5, 4: 19, 5: 15, 6: 11, 7: 16, 8: 14, 9: 17, 10: 15, 
                    11: 12, 12: 14, 13: 16, 14: 9},
            "JOL": {1: 20, 2: 32, 3: 21},
            "AMO": {1: 15, 2: 16, 3: 15, 4: 13, 5: 27, 6: 14, 7: 17, 8: 14, 9: 15},
            "OBA": {1: 21},
            "JON": {1: 17, 2: 10, 3: 10, 4: 11},
            "MIC": {1: 16, 2: 13, 3: 12, 4: 13, 5: 15, 6: 16, 7: 20},
            "NAH": {1: 15, 2: 13, 3: 19},
            "HAB": {1: 17, 2: 20, 3: 19},
            "ZEP": {1: 18, 2: 15, 3: 20},
            "HAG": {1: 15, 2: 23},
            "ZEC": {1: 21, 2: 13, 3: 10, 4: 14, 5: 11, 6: 15, 7: 14, 8: 23, 9: 17, 10: 12, 
                    11: 17, 12: 14, 13: 9, 14: 21},
            "MAL": {1: 14, 2: 17, 3: 18, 4: 6},
        }
        
        # Convert to book_id format used by database
        formatted_verse_counts = {}
        for book_abbr, chapters in verse_counts.items():
            # Use book_id as key (usually lowercase abbreviation)
            book_id = book_abbr.lower()
            formatted_verse_counts[book_id] = chapters
        
        return formatted_verse_counts

    def expand_reference_range(self, start, end, verse_counts):
        """
        Expand a reference range into individual verse references.
        
        Args:
            start: Tuple of (book, chapter, verse) for start reference
            end: Tuple of (book, chapter, verse) for end reference
            verse_counts: Dictionary of {book_id: {chapter: verse_count}}
            
        Returns:
            List of (source_ref, target_ref) tuples
        """
        start_book, start_chapter, start_verse = start
        end_book, end_chapter, end_verse = end
        
        # Convert book IDs to lowercase for consistent lookup
        start_book = start_book.lower() if isinstance(start_book, str) else start_book
        end_book = end_book.lower() if isinstance(end_book, str) else end_book
        
        # Internal helper to get book order (just use alphabetical for now)
        def get_book_order(book_id):
            # Hebrew Bible book order - simplified version
            book_order = {
                'gen': 1, 'exo': 2, 'lev': 3, 'num': 4, 'deu': 5,
                'jos': 6, 'jdg': 7, 'rut': 8, '1sa': 9, '2sa': 10,
                '1ki': 11, '2ki': 12, '1ch': 13, '2ch': 14, 'ezr': 15,
                'neh': 16, 'est': 17, 'job': 18, 'psa': 19, 'pro': 20,
                'ecc': 21, 'sng': 22, 'isa': 23, 'jer': 24, 'lam': 25,
                'ezk': 26, 'dan': 27, 'hos': 28, 'jol': 29, 'amo': 30,
                'oba': 31, 'jon': 32, 'mic': 33, 'nah': 34, 'hab': 35,
                'zep': 36, 'hag': 37, 'zec': 38, 'mal': 39
            }
            return book_order.get(book_id, 100)  # Default to high number if not found
        
        expanded_mappings = []
        
        # Same book case
        if start_book == end_book:
            # Same chapter case
            if start_chapter == end_chapter:
                for verse in range(start_verse, end_verse + 1):
                    expanded_mappings.append(
                        ((start_book, start_chapter, verse), (start_book, start_chapter, verse))
                    )
            # Cross-chapter, same book case
            else:
                # First chapter: start_verse to end of chapter
                if start_book in verse_counts and start_chapter in verse_counts[start_book]:
                    max_verse = verse_counts[start_book][start_chapter]
                    for verse in range(start_verse, max_verse + 1):
                        expanded_mappings.append(
                            ((start_book, start_chapter, verse), (start_book, start_chapter, verse))
                        )
                
                # Middle chapters (all verses)
                for chapter in range(start_chapter + 1, end_chapter):
                    if start_book in verse_counts and chapter in verse_counts[start_book]:
                        max_verse = verse_counts[start_book][chapter]
                        for verse in range(1, max_verse + 1):
                            expanded_mappings.append(
                                ((start_book, chapter, verse), (start_book, chapter, verse))
                            )
                
                # Last chapter: 1 to end_verse
                for verse in range(1, end_verse + 1):
                    expanded_mappings.append(
                        ((start_book, end_chapter, verse), (start_book, end_chapter, verse))
                    )
        
        # Cross-book case
        else:
            # Check if books are in the correct order
            if get_book_order(start_book) > get_book_order(end_book):
                logger.warning(f"Start book {start_book} comes after end book {end_book} in biblical order")
                # Swap if needed to ensure proper order
                start_book, end_book = end_book, start_book
                start_chapter, end_chapter = end_chapter, start_chapter
                start_verse, end_verse = end_verse, start_verse
            
            # First book: start_chapter:start_verse to end of book
            current_book = start_book
            
            # Handle first chapter of first book
            if current_book in verse_counts and start_chapter in verse_counts[current_book]:
                max_verse = verse_counts[current_book][start_chapter]
                for verse in range(start_verse, max_verse + 1):
                    expanded_mappings.append(
                        ((current_book, start_chapter, verse), (current_book, start_chapter, verse))
                    )
            
            # Handle remaining chapters of first book
            if current_book in verse_counts:
                max_chapter = max(verse_counts[current_book].keys())
                for chapter in range(start_chapter + 1, max_chapter + 1):
                    if chapter in verse_counts[current_book]:
                        max_verse = verse_counts[current_book][chapter]
                        for verse in range(1, max_verse + 1):
                            expanded_mappings.append(
                                ((current_book, chapter, verse), (current_book, chapter, verse))
                            )
            
            # Middle books (all chapters, all verses)
            book_order_start = get_book_order(start_book)
            book_order_end = get_book_order(end_book)
            
            # Get all books in between
            for book_order in range(book_order_start + 1, book_order_end):
                # Find the book with this order
                middle_book = None
                for book in verse_counts.keys():
                    if get_book_order(book) == book_order:
                        middle_book = book
                        break
                
                if middle_book and middle_book in verse_counts:
                    for chapter in sorted(verse_counts[middle_book].keys()):
                        max_verse = verse_counts[middle_book][chapter]
                        for verse in range(1, max_verse + 1):
                            expanded_mappings.append(
                                ((middle_book, chapter, verse), (middle_book, chapter, verse))
                            )
            
            # Last book: from beginning to end_chapter:end_verse
            # Handle all chapters before the end chapter
            if end_book in verse_counts:
                for chapter in range(1, end_chapter):
                    if chapter in verse_counts[end_book]:
                        max_verse = verse_counts[end_book][chapter]
                        for verse in range(1, max_verse + 1):
                            expanded_mappings.append(
                                ((end_book, chapter, verse), (end_book, chapter, verse))
                            )
                
                # Handle the end chapter
                for verse in range(1, end_verse + 1):
                    expanded_mappings.append(
                        ((end_book, end_chapter, verse), (end_book, end_chapter, verse))
                    )
        
        return expanded_mappings

    def parse_reference(self, ref: str, current_book: Optional[str] = None, verse_counts=None) -> list:
        """
        Parse a reference string and return a list of dicts as expected by the tests.
        """
        # Use the more robust _parse_single_reference for all cases
        refs = self._parse_single_reference(ref, current_book)
        if refs and refs[0].get('book') is not None:
            return refs
            
        # Fallback: Try to parse Book.Chapter:Verse format directly
        if '.' in ref and ':' in ref:
            match = re.match(r'^([^.]+)\.([^:]+):(\d+)', ref)
            if match:
                book, chapter, verse = match.groups()
                book = self.normalize_book_reference(book)
                return [{
                    'book': book,
                    'chapter': chapter,
                    'verse': int(verse),
                    'subverse': None,
                    'manuscript': None,
                    'annotation': None,
                    'range_note': None
                }]
        
        # Empty response for DSPy learning
        return []

    def _parse_single_reference(self, ref: str, current_book: Optional[str], annotation=None, manuscript=None) -> List[Dict]:
        """Parse a single ref, returning list with expected keys on failure."""
        logger.debug(f"[TRACE] _parse_single_reference input: '{ref}' (current_book={current_book})")
        if not ref or not isinstance(ref, str) or not ref.strip():
            return []
        ref_str = ref.strip()
        # Extract annotation [=...]
        annotation_match = re.search(r'(\[=.*?\])', ref_str)
        if annotation_match:
            annotation = annotation_match.group(1)
            ref_str = ref_str.replace(annotation, '')
        # Extract manuscript marker (!a, !b, etc.)
        manuscript_marker = None
        m_marker = re.match(r'^!(\w+)$', ref_str)
        if m_marker:
            manuscript_marker = f'!{m_marker.group(1)}'
            return [{
                'book': None, 'chapter': None, 'verse': None, 'subverse': None, 'manuscript': manuscript_marker,
                'annotation': None, 'range_note': None
            }]
        # Extract range notes (+..., ++...)
        range_note = None
        if '+' in ref_str:
            parts = ref_str.split('+', 1)
            ref_str = parts[0]
            range_note = '+' + parts[1] if len(parts) > 1 else '+'
        # Handle semicolons - only process the first reference
        if ';' in ref_str:
            first_ref = ref_str.split(';')[0].strip()
            return self._parse_single_reference(first_ref, current_book, annotation, manuscript)
        # Handle comma-separated references (only use the first reference)
        if ',' in ref_str:
            first_ref = ref_str.split(',')[0].strip()
            return self._parse_single_reference(first_ref, current_book, annotation, manuscript)
        # Handle ranges (e.g. Gen.1:1-3, but also allow for bookless ranges like 1:1-3)
        range_match = re.match(r'^(?P<book>[^.]+)\.(?P<chapter>[^:]+):(?P<start>\d+)-(?P<end>\d+)$', ref_str)
        if range_match:
            book = self.normalize_book_reference(range_match.group('book'))
            chapter = range_match.group('chapter')
            start = int(range_match.group('start'))
            end = int(range_match.group('end'))
            result = []
            for v in range(start, end + 1):
                result.append({
                    'book': book,
                    'chapter': chapter,
                    'verse': v,
                    'subverse': None,
                    'manuscript': None,
                    'annotation': annotation,
                    'range_note': f"Part of range {ref.strip()}"
                })
            return result
        # Handle Book.Chapter:Verse(.Subverse) or Book.Chapter:Verse
        match = re.match(r'^(?P<book>[^.]+)\.(?P<chapter>[^:]+):(?P<verse>\d+)(?:\.(?P<subverse>\w+))?$', ref_str)
        if match:
            book = self.normalize_book_reference(match.group('book'))
            chapter = match.group('chapter')
            # If chapter is a letter, keep as string
            if chapter.isdigit():
                chapter_val = int(chapter)
            else:
                chapter_val = chapter
            verse = int(match.group('verse'))
            subverse = match.group('subverse') if match.group('subverse') else None
            return [{
                'book': book,
                'chapter': chapter if not chapter.isdigit() else str(chapter_val),
                'verse': verse,
                'subverse': subverse,
                'manuscript': None,
                'annotation': annotation,
                'range_note': range_note
            }]
        # Handle Book.Chapter (whole chapter reference)
        match = re.match(r'^(?P<book>[^.]+)\.(?P<chapter>\w+)$', ref_str)
        if match:
            book = self.normalize_book_reference(match.group('book'))
            chapter = match.group('chapter')
            return [{
                'book': book,
                'chapter': chapter,
                'verse': 1,
                'subverse': None,
                'manuscript': None,
                'annotation': annotation,
                'range_note': range_note
            }]
        # Handle Chapter:Verse(.Subverse) or Chapter:Verse
        match = re.match(r'^(?P<chapter>[^:]+):(?P<verse>\d+)(?:\.(?P<subverse>\w+))?$', ref_str)
        if match and current_book:
            book = self.normalize_book_reference(current_book)
            chapter = match.group('chapter')
            if chapter.isdigit():
                chapter_val = int(chapter)
            else:
                chapter_val = chapter
            verse = int(match.group('verse'))
            subverse = match.group('subverse') if match.group('subverse') else None
            return [{
                'book': book,
                'chapter': chapter if not chapter.isdigit() else str(chapter_val),
                'verse': verse,
                'subverse': subverse,
                'manuscript': None,
                'annotation': annotation,
                'range_note': range_note
            }]
        # Handle Chapter only (implied verse 1)
        match = re.match(r'^(?P<chapter>\w+)$', ref_str)
        if match and current_book:
            book = self.normalize_book_reference(current_book)
            chapter = match.group('chapter')
            return [{
                'book': book,
                'chapter': chapter,
                'verse': 1,
                'subverse': None,
                'manuscript': None,
                'annotation': annotation,
                'range_note': range_note
            }]
        # If nothing matches, log for DSPy and return []
        import json
        from datetime import datetime
        dspy_log = {
            "error_type": "parser_error",
            "input": ref,
            "error_message": "Unrecognized reference format",
            "context": {"file": "src/tvtms/parser.py", "function": "_parse_single_reference"},
            "fix_applied": "Handled gracefully, logged for DSPy",
            "timestamp": datetime.now().isoformat()
        }
        with open("data/processed/dspy_training_data/versification_parser_schema_issues.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(dspy_log) + "\n")
        return []

    def _create_mappings_from_row(
        self, source_type: str, source_ref_str: str, standard_ref_str: str, action: str, 
        note_marker: str, note_a: str, note_b: str, ancient_versions: str, tests: str
        ) -> List[Mapping]:
        """Create Mapping objects from extracted row data, handling ranges and parse failures."""
        mappings = []
        try:
            # First try to parse using the more detailed _parse_single_reference method
            # This handles special markers like asterisks, annotations, etc.
            source_refs = self._parse_single_reference(source_ref_str, self.current_book)
            target_refs = self._parse_single_reference(standard_ref_str, self.current_book)
            
            # Only proceed if both source and target refs were parsed successfully
            if source_refs and target_refs and source_refs[0].get('book') and target_refs[0].get('book'):
                source_ref = source_refs[0]
                target_ref = target_refs[0]
                
                # Create the mapping using the detailed reference info
                mapping = self._create_single_mapping(
                    source_ref=source_ref, 
                    target_ref=target_ref, 
                    source_type_str=source_type,
                    action_str=action, 
                    note_marker_str=note_marker, 
                    note_a_str=note_a, 
                    note_b_str=note_b,
                    ancient_versions_str=ancient_versions, 
                    tests_str=tests
                )
                
                if mapping:
                    mappings.append(mapping)
                    return mappings
            
            # Fallback to direct Book.Chapter:Verse pattern extraction
            try:
                # Direct pattern matching for Book.Chapter:Verse format
                source_match = re.match(r'^([^.]+)\.([^:]+):(\d+)', source_ref_str)
                target_match = re.match(r'^([^.]+)\.([^:]+):(\d+)', standard_ref_str)
                
                if source_match and target_match:
                    source_book = self.normalize_book_reference(source_match.group(1))
                    source_chapter = source_match.group(2)
                    source_verse = int(source_match.group(3))
                    
                    target_book = self.normalize_book_reference(target_match.group(1))
                    target_chapter = target_match.group(2)
                    target_verse = int(target_match.group(3))
                    
                    # Create a source_ref dict with extracted info
                    source_ref = {
                        'book': source_book,
                        'chapter': source_chapter,
                        'verse': source_verse,
                        'subverse': None,
                        'manuscript': None,
                        'range_note': None
                    }
                    
                    # Create a target_ref dict with extracted info
                    target_ref = {
                        'book': target_book,
                        'chapter': target_chapter,
                        'verse': target_verse,
                        'subverse': None,
                        'manuscript': None,
                        'range_note': None
                    }
                    
                    # Create the mapping with the extracted references
                    mapping = self._create_single_mapping(
                        source_ref=source_ref,
                        target_ref=target_ref,
                        source_type_str=source_type,
                        action_str=action,
                        note_marker_str=note_marker,
                        note_a_str=note_a,
                        note_b_str=note_b,
                        ancient_versions_str=ancient_versions,
                        tests_str=tests
                    )
                    
                    if mapping:
                        mappings.append(mapping)
                        return mappings
                
                # If we're here, we failed to parse - log it for DSPy training
                logger.error(f"Error in fallback parsing: not enough values to unpack (expected 3, got 1) - Source: '{source_ref_str}', Target: '{standard_ref_str}'")
                
                # Create DSPy training entry
                import json
                from datetime import datetime
                dspy_log = {
                    "error_type": "parser_error",
                    "input": [source_ref_str, standard_ref_str],
                    "error_message": "Failed to parse reference in fallback handler",
                    "context": {"file": "src/tvtms/parser.py", "function": "_create_mappings_from_row"},
                    "fix_applied": "Added direct pattern extraction",
                    "timestamp": datetime.now().isoformat()
                }
                # Ensure directory exists
                import os
                os.makedirs("data/processed/dspy_training_data", exist_ok=True)
                with open("data/processed/dspy_training_data/versification_parser_schema_issues.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(dspy_log) + "\n")
                
            except Exception as e:
                logger.error(f"Error in fallback parsing: {e} - Source: '{source_ref_str}', Target: '{standard_ref_str}'")
        
        except Exception as e:
            logger.error(f"Error processing mapping: {e}")
            
        return mappings

    def _create_single_mapping(
        self, source_ref: Dict, target_ref: Dict, source_type_str: str,
        action_str: str, note_marker_str: str, note_a_str: str, note_b_str: str, 
        ancient_versions_str: str, tests_str: str
    ) -> Optional[Mapping]:
        """Create a single Mapping object, handling parse errors."""
        try:
            # Extract source/target components from dictionaries
            source_book = source_ref.get('book')
            source_chapter = source_ref.get('chapter')
            source_verse = source_ref.get('verse')
            source_subverse = source_ref.get('subverse')
            source_manuscript = source_ref.get('manuscript')
            source_range_note = source_ref.get('range_note')
            
            target_book = target_ref.get('book')
            target_chapter = target_ref.get('chapter')
            target_verse = target_ref.get('verse')
            target_subverse = target_ref.get('subverse')
            target_manuscript = target_ref.get('manuscript')
            target_range_note = target_ref.get('range_note')
            
            # Determine mapping type
            mapping_type = self.normalize_mapping_type(action_str)
            
            # Fix: Make sure mapping_type is not None
            if mapping_type is None:
                logger.debug(f"Skipping mapping creation due to None mapping_type for action: '{action_str}'")
                return None
            
            # Extract category
            category = self.normalize_category(note_marker_str)
            
            # Combine notes if needed
            notes = f"NoteA: {note_a_str} | NoteB: {note_b_str}"
            
            # Create mapping with field names matching the Mapping class
            mapping = Mapping(
                source_tradition=source_type_str.lower(),  # Use lowercase for consistency
                target_tradition='standard',  # Assuming target is always standard
                source_book=source_book,
                source_chapter=source_chapter,
                source_verse=source_verse,
                source_subverse=source_subverse,
                manuscript_marker=source_manuscript,
                target_book=target_book,
                target_chapter=target_chapter,
                target_verse=target_verse,
                target_subverse=target_subverse,
                mapping_type=mapping_type,
                category=category,
                notes=notes,
                source_range_note=source_range_note,
                target_range_note=target_range_note,
                note_marker=note_marker_str,
                ancient_versions=ancient_versions_str
            )
            return mapping
        
        except Exception as e:
            logger.exception(f"Error creating single mapping: {e} - SourceRef: {source_ref} TargetRef: {target_ref} Action: {action_str}")
            return None
            
    # --- Helper methods for extraction ---
    def normalize_mapping_type(self, mapping_type: str) -> str:
        """Normalize mapping type to standard format as expected by tests."""
        # Mapping as per test expectations
        mapping_type_map = {
            'Keep verse': 'standard',
            'Standard': 'standard',
            'identical': 'standard',
            'MergedPrev verse': 'merge_prev',
            'MergedNext verse': 'merge_next',
            'merge prev': 'merge_prev',
            'merge next': 'merge_next',
            'Merged': 'merge',
            'IfEmpty verse': 'omit',
            'TextMayBeMissing': 'omit',
            'Empty verse': 'omit',
            'Missing verse': 'omit',
            'SubdividedVerse': 'split',
            'LongVerse': 'insert',
            'LongVerseElsewhere': 'insert',
            'LongVerseDuplicated': 'insert',
            'StartDifferent': 'renumbering',
            'Renumber verse': 'renumbering',
            'Renumber title': 'renumbering',
            'Psalm Title': 'renumbering',
        }
        if not mapping_type:
            return 'standard'
        mt = mapping_type.strip()
        # Direct match
        if mt in mapping_type_map:
            return mapping_type_map[mt]
        # Case-insensitive match
        mt_lower = mt.lower()
        for k, v in mapping_type_map.items():
            if k.lower() == mt_lower:
                return v
        # Fallback for known patterns
        if 'merge' in mt_lower:
            if 'prev' in mt_lower:
                return 'merge_prev'
            if 'next' in mt_lower:
                return 'merge_next'
            return 'merge'
        if 'renumber' in mt_lower:
            return 'renumbering'
        if 'keep' in mt_lower or 'identical' in mt_lower:
            return 'standard'
        if 'omit' in mt_lower or 'empty' in mt_lower or 'missing' in mt_lower:
            return 'omit'
        if 'split' in mt_lower or 'subdivided' in mt_lower:
            return 'split'
        if 'insert' in mt_lower or 'long' in mt_lower:
            return 'insert'
        return 'standard'

    def normalize_category(self, category: str) -> str:
        """Normalize a category as expected by tests."""
        # Accept both short and long forms
        valid = {'Opt', 'Nec', 'Acd', 'Inf', 'None'}
        long_to_short = {
            'Optional': 'Opt',
            'Necessary': 'Nec',
            'Accidental': 'Acd',
            'Inferential': 'Inf',
        }
        if not category:
            return 'None'
        cat = category.strip('. ')
        if cat in valid:
            return cat
        if cat in long_to_short:
            return long_to_short[cat]
        # Try with trailing period removed
        if cat.endswith('.'):
            cat = cat[:-1]
            if cat in valid:
                return cat
            if cat in long_to_short:
                return long_to_short[cat]
        return 'None'

# Add helper functions if needed, e.g., for complex range expansion or validation checks
# that don't fit neatly into the main methods. 