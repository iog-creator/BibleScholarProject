# Bible Translations

This document provides details on the Bible translations available in the BibleScholarProject database.

## Available Translations

| Translation | Description | Verse Count | Source Type | Language |
|-------------|-------------|-------------|------------|----------|
| KJV | King James Version (1611) | 31,100 | Public Domain | English |
| ASV | American Standard Version (1901) | 31,103 | Public Domain | English |
| ESV | English Standard Version | 4 (sample) | Licensed | English |
| TAGNT | Translators Amalgamated Greek NT | 7,958 | Open License | Greek |
| TAHOT | Translators Amalgamated Hebrew OT | 23,261 | Open License | Hebrew |

## Translation Details

### King James Version (KJV)

**Status**: Complete (31,100 verses)  
**Source**: Public Domain  
**Year**: 1611  
**Description**: The King James Version (also known as the Authorized Version) is a classic English translation of the Bible, commissioned by King James I of England in 1604 and published in 1611. It has significantly influenced English literature and language.

**Data Source**: 
- GitHub repository: `https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json`
- Loaded via `load_kjv_bible.py`

**Sample Text (John 3:16)**:
```
For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.
```

### American Standard Version (ASV)

**Status**: Complete (31,103 verses)  
**Source**: Public Domain  
**Year**: 1901  
**Description**: The American Standard Version is an American revision of the English Revised Version of 1885. It was published in 1901 and is notable for its accuracy and use of the divine name "Jehovah" instead of "LORD." It served as the basis for many modern translations, including the RSV and NASB.

**Data Source**:
- GitHub repository: `https://raw.githubusercontent.com/bibleapi/bibleapi-bibles-json/master/asv.json`
- Loaded via `direct_asv_download.py`

**Sample Text (John 3:16)**:
```
For God so loved the world, that he gave his only begotten Son, that whosoever believeth on him should not perish, but have eternal life.
```

### English Standard Version (ESV)

**Status**: Sample only (4 verses)  
**Source**: Licensed content from Crossway  
**Year**: 2001 (with revisions)  
**Description**: The English Standard Version is a modern English translation that balances word-for-word precision with readability. It is based on the Revised Standard Version and aims for accuracy while maintaining literary excellence.

**Data Source**:
- STEPBible-Data: `STEPBible-Data/Tagged-Bibles/TTESV - Translators Tags for ESV`
- Tagged version includes Strong's number references
- Loaded via `load_esv_bible.py`

**Integration Details**:
- Modified database schema to support multiple translations per verse
- Added translation_source to unique constraints
- Enhanced tests to validate ESV data integrity
- Created dedicated test module (test_esv_bible_data.py)
- Strong's number mapping maintained where available

**Technical Considerations**:
- ESV text with Strong's tagging follows format: `word {HnnnnX}` where H is the language prefix and X is any optional extensions
- Requires special parsing for preserving Strong's numbers and morphological information
- Strong's-tagged ESV words can be linked to Hebrew/Greek lexicon entries

**License Restrictions**: 
- Full version requires license from Crossway
- Limited to sample verses for demonstration purposes
- Attribution required: "Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), copyright © 2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved."

**Sample Text (John 3:16)**:
```
For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.
```

### Translators Amalgamated Greek NT (TAGNT)

**Status**: Complete New Testament (7,958 verses)  
**Source**: Open License (CC BY 4.0)  
**Year**: Modern compilation  
**Description**: Greek text that includes all the words in NA27/28, TR and other major editions (SBLGNT, Treg, Byz, WH, THGNT). Each word is marked with the editions that contain it, positional variants, and meaning variants.

**Data Source**: 
- STEPBible-Data: `Translators Amalgamated OT+NT/TAGNT - Translators Amalgamated Greek NT - TyndaleHouse.com STEPBible.org CC BY.txt`

### Translators Amalgamated Hebrew OT (TAHOT)

**Status**: Complete Old Testament (23,261 verses)  
**Source**: Open License (CC BY 4.0)  
**Year**: Modern compilation  
**Description**: The Leningrad codex based on Westminster via OpenScriptures, corrected from colour scans, with full morphological and semantic tags for all words, prefixes and suffixes.

**Data Source**:
- STEPBible-Data: `Translators Amalgamated OT+NT/TAHOT - Translators Amalgamated Hebrew OT - TyndaleHouse.com STEPBible.org CC BY.txt`

## Adding New Translations

When adding new translations to the database:

1. **Public Domain Translations**: Use the loading pattern in `load_kjv_bible.py` or `direct_asv_download.py`
2. **Licensed Translations**: Ensure proper licensing is in place before inclusion
3. **Storage Format**: All translations should be stored in the `bible.verses` table with proper `translation_source` identifier
4. **Validation**: Verify the expected verse count after loading

## Usage Guidelines

### API Access

All translations can be accessed through the standard API endpoints:

```
/api/verses?translation=CODE&book=BookName&chapter=N&verse=N
```

Replace `CODE` with the translation code (KJV, ASV, etc.).

### Translation Comparison

To compare translations side-by-side, use the comparison endpoint:

```
/api/compare?book=BookName&chapter=N&verse=N&translations=KJV,ASV
```

### Search

To search across all translations or specific translations:

```
/api/search?text=SearchTerm&translations=KJV,ASV
```

If no `translations` parameter is provided, search will be performed across all available translations.

## Verification Queries

To verify the available translations and their verse counts:

```sql
SELECT translation_source, COUNT(*) 
FROM bible.verses 
GROUP BY translation_source
ORDER BY translation_source;
```

To compare a specific verse across translations:

```sql
SELECT translation_source, verse_text
FROM bible.verses
WHERE book_name = 'John' AND chapter_num = 3 AND verse_num = 16
ORDER BY translation_source;
``` 