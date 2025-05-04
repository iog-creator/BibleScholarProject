"""Constants used across the TVTMS modules.

This module centralizes all constants used in the TVTMS system to avoid duplication
and ensure consistency across the codebase. It includes:

- Book name variations and mappings
- Valid categories for verse mappings
- Mapping types and their normalizations
- Special markers and their meanings
"""

# Comprehensive book variations map
BOOK_VARIATIONS_MAP = {
    'Genesis': 'Gen', 'Gen': 'Gen', 'Exodus': 'Exo', 'Exo': 'Exo', 'Ex': 'Exo',
    'Leviticus': 'Lev', 'Lev': 'Lev', 'Numbers': 'Num', 'Num': 'Num',
    'Deuteronomy': 'Deu', 'Deu': 'Deu', 'Deut': 'Deu',
    'Joshua': 'Jos', 'Jos': 'Jos', 'Josh': 'Jos',
    'Judges': 'Jdg', 'Jdg': 'Jdg', 'Judg': 'Jdg',
    'Ruth': 'Rut', 'Rut': 'Rut',
    '1 Samuel': '1Sa', '1Sa': '1Sa', '1Sam': '1Sa', 'First Samuel': '1Sa',
    '2 Samuel': '2Sa', '2Sa': '2Sa', '2Sam': '2Sa', 'Second Samuel': '2Sa',
    '1 Kings': '1Ki', '1Ki': '1Ki', '1Kgs': '1Ki', 'First Kings': '1Ki',
    '2 Kings': '2Ki', '2Ki': '2Ki', '2Kgs': '2Ki', 'Second Kings': '2Ki',
    '1 Chronicles': '1Ch', '1Ch': '1Ch', '1Chr': '1Ch', 'First Chronicles': '1Ch',
    '2 Chronicles': '2Ch', '2Ch': '2Ch', '2Chr': '2Ch', 'Second Chronicles': '2Ch',
    'Ezra': 'Ezr', 'Ezr': 'Ezr',
    'Nehemiah': 'Neh', 'Neh': 'Neh',
    'Esther': 'Est', 'Est': 'Est',
    'Job': 'Job',
    'Psalms': 'Psa', 'Psalm': 'Psa', 'Psa': 'Psa', 'Ps': 'Psa',
    'Proverbs': 'Pro', 'Pro': 'Pro', 'Prov': 'Pro',
    'Ecclesiastes': 'Ecc', 'Ecc': 'Ecc', 'Eccl': 'Ecc', 'Eccles': 'Ecc',
    'Song of Solomon': 'Sng', 'Song': 'Sng', 'Sng': 'Sng', 'Canticles': 'Sng',
    'Isaiah': 'Isa', 'Isa': 'Isa',
    'Jeremiah': 'Jer', 'Jer': 'Jer',
    'Lamentations': 'Lam', 'Lam': 'Lam', 'Lament': 'Lam',
    'Ezekiel': 'Ezk', 'Ezk': 'Ezk', 'Eze': 'Ezk', 'Ezek': 'Ezk',
    'Daniel': 'Dan', 'Dan': 'Dan',
    'Hosea': 'Hos', 'Hos': 'Hos',
    'Joel': 'Jol', 'Jol': 'Jol', 'Joe': 'Jol',
    'Amos': 'Amo', 'Amo': 'Amo',
    'Obadiah': 'Oba', 'Oba': 'Oba', 'Obad': 'Oba',
    'Jonah': 'Jon', 'Jon': 'Jon',
    'Micah': 'Mic', 'Mic': 'Mic',
    'Nahum': 'Nam', 'Nam': 'Nam', 'Nah': 'Nam',
    'Habakkuk': 'Hab', 'Hab': 'Hab',
    'Zephaniah': 'Zep', 'Zep': 'Zep', 'Zeph': 'Zep',
    'Haggai': 'Hag', 'Hag': 'Hag',
    'Zechariah': 'Zec', 'Zec': 'Zec', 'Zech': 'Zec',
    'Malachi': 'Mal', 'Mal': 'Mal',
    'Matthew': 'Mat', 'Mat': 'Mat', 'Matt': 'Mat', 'Mt': 'Mat',
    'Mark': 'Mrk', 'Mrk': 'Mrk', 'Mar': 'Mrk', 'Mk': 'Mrk',
    'Luke': 'Luk', 'Luk': 'Luk', 'Lk': 'Luk',
    'John': 'Jhn', 'Jhn': 'Jhn', 'Joh': 'Jhn', 'Jn': 'Jhn',
    'Acts': 'Act', 'Act': 'Act',
    'Romans': 'Rom', 'Rom': 'Rom',
    '1 Corinthians': '1Co', '1Co': '1Co', 'First Corinthians': '1Co',
    '2 Corinthians': '2Co', '2Co': '2Co', 'Second Corinthians': '2Co',
    'Galatians': 'Gal', 'Gal': 'Gal',
    'Ephesians': 'Eph', 'Eph': 'Eph',
    'Philippians': 'Php', 'Php': 'Php',
    'Colossians': 'Col', 'Col': 'Col',
    '1 Thessalonians': '1Th', '1Th': '1Th', 'First Thessalonians': '1Th',
    '2 Thessalonians': '2Th', '2Th': '2Th', 'Second Thessalonians': '2Th',
    '1 Timothy': '1Ti', '1Ti': '1Ti', 'First Timothy': '1Ti',
    '2 Timothy': '2Ti', '2Ti': '2Ti', 'Second Timothy': '2Ti',
    'Titus': 'Tit', 'Tit': 'Tit',
    'Philemon': 'Phm', 'Phm': 'Phm',
    'Hebrews': 'Heb', 'Heb': 'Heb',
    'James': 'Jas', 'Jas': 'Jas',
    '1 Peter': '1Pe', '1Pe': '1Pe', 'First Peter': '1Pe',
    '2 Peter': '2Pe', '2Pe': '2Pe', 'Second Peter': '2Pe',
    '1 John': '1Jn', '1Jn': '1Jn', 'First John': '1Jn',
    '2 John': '2Jn', '2Jn': '2Jn', 'Second John': '2Jn',
    '3 John': '3Jn', '3Jn': '3Jn', 'Third John': '3Jn',
    'Jude': 'Jud', 'Jud': 'Jud',
    'Revelation': 'Rev', 'Rev': 'Rev', 'Apocalypse': 'Rev',
    # Apocryphal books
    'Tobit': 'Tob', 'Tob': 'Tob',
    'Judith': 'Jdt', 'Jdt': 'Jdt',
    'Greek Esther': 'EsG', 'EsG': 'EsG',
    'Wisdom': 'Wis', 'Wis': 'Wis',
    'Sirach': 'Sir', 'Sir': 'Sir',
    'Baruch': 'Bar', 'Bar': 'Bar',
    'Letter of Jeremiah': 'LJe', 'LJe': 'LJe', 'Epistle of Jeremiah': 'LJe',
    'Greek Daniel': 'DaG', 'DaG': 'DaG',
    'Susanna': 'Sus', 'Sus': 'Sus',
    'Bel and the Dragon': 'Bel', 'Bel': 'Bel',
    '1 Maccabees': '1Ma', '1Ma': '1Ma', 'First Maccabees': '1Ma',
    '2 Maccabees': '2Ma', '2Ma': '2Ma', 'Second Maccabees': '2Ma',
    '3 Maccabees': '3Ma', '3Ma': '3Ma', 'Third Maccabees': '3Ma',
    '4 Maccabees': '4Ma', '4Ma': '4Ma', 'Fourth Maccabees': '4Ma',
    '1 Esdras': '1Es', '1Es': '1Es', 'First Esdras': '1Es',
    '2 Esdras': '2Es', '2Es': '2Es', 'Second Esdras': '2Es',
    'Prayer of Manasseh': 'Man', 'Man': 'Man',
    'Psalm 151': 'Ps2', 'Ps2': 'Ps2',
    'Psalms of Solomon': 'PsS', 'PsS': 'PsS',
    'Additions to Esther': 'Ade', 'Ade': 'Ade'
}

# Valid categories for verse mappings
# Includes standard categories and codes derived from NoteMarker
VALID_CATEGORIES = {
    'None', 'Absent', 'Title', 'Verse', 'Chapter',
    'Book', 'Range', 'Merged', 'Split', 'Insert',
    'Addition', 'Esther Segments',
    # Codes from CATEGORY_CODE_MAP
    'ADE', 'ESG', 'MRG', 'SPL',
    # Codes used in TVTMS expanded data
    'Acd', 'Nec', 'Opt', 'Inf'
}

# Mapping from category codes (found in NoteMarker) to full category names
CATEGORY_CODE_MAP = {
    'ADE': 'Addition',
    'ESG': 'Esther Segments',
    'MRG': 'Merged',
    'SPL': 'Split',
}

# --- ADD ACTION_PRIORITY ---
# Action priority order (as per STEPBible documentation)
# Used by both parser and action processor
ACTION_PRIORITY = [
    'Merged',
    'Renumber',
    'Keep',
    'IfEmpty',
    'Psalm Title',
    'Renumber Title'
]
# --- END ACTION_PRIORITY ---

# Valid mapping types (now derived directly from ACTION_PRIORITY + 'standard')
MAPPING_TYPES = set(ACTION_PRIORITY + ['standard'])

# Special markers and their meanings
SPECIAL_MARKERS = {
    '!a': 'First alternative reading',
    '!b': 'Second alternative reading',
    '!c': 'Third alternative reading',
    '!LXX': 'Septuagint reading',
    '!MT': 'Masoretic Text reading',
    '!V': 'Vulgate reading'
}

# Skip cases for book name normalization
SKIP_CASES = {
    'allbibles', 'na', 'esv', 'nrsv', 'niv', 'kjv', 'greek', 'latin',
    'english', 'arabic', 'italian', 'bangladeshi', 'sil', 'osis', 'absent'
} 