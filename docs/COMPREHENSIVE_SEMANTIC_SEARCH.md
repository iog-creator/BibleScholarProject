# Comprehensive Semantic Search with Bible Database Integration

This document outlines the strategy for integrating all available database resources with the pgvector semantic search functionality in the BibleScholarProject.

## Available Database Resources

The Bible database contains a rich set of interconnected resources that can be leveraged to enhance semantic search:

| Resource Type | Table(s) | Record Count | Purpose |
|--------------|----------|--------------|---------|
| **Core Bible Text** | `bible.verses` | 93,426 | Base verse text across translations |
| **Vector Embeddings** | `bible.verse_embeddings` | 93,426 | 768-dimension semantic vectors |
| **Hebrew Lexicon** | `bible.hebrew_entries` | 9,349 | Strong's Hebrew definitions |
| **Greek Lexicon** | `bible.greek_entries`, `bible.lsj_entries` | 10,847 / 10,846 | Strong's Greek + LSJ lexicon entries |
| **Morphological Analysis** | `bible.hebrew_ot_words`, `bible.greek_nt_words` | 308,189 / 142,096 | Word-level analysis with Strong's IDs |
| **Proper Names** | `bible.proper_names`, related tables | 1,317 | Biblical name entities and relationships |
| **Arabic Resources** | `bible.arabic_verses`, `bible.arabic_words` | 31,091 | Arabic translation and word data |
| **Word Relationships** | `bible.word_relationships` | 17,608 | Semantic relationships between words |
| **Cross-Language Terms** | `bible.cross_language_terms` | 3 | Terms with equivalent meaning across languages |
| **Versification** | `bible.versification_mappings` | 1,786 | Maps between different verse numbering systems |

## Integration Approach

### 1. Multi-Source Semantic Search

Enable searching across all available text resources:

```sql
-- Multi-source semantic search query
WITH query_embedding AS (
    SELECT %s::vector AS embedding
)
SELECT 
    'Hebrew' AS source_type,
    v.book_name, 
    v.chapter_num, 
    v.verse_num, 
    v.verse_text,
    v.translation_source,
    1 - (e.embedding <=> (SELECT embedding FROM query_embedding)) AS similarity
FROM 
    bible.verse_embeddings e
    JOIN bible.verses v ON e.verse_id = v.id
WHERE 
    v.translation_source = 'TAHOT'
UNION ALL
SELECT 
    'Greek' AS source_type,
    v.book_name, 
    v.chapter_num, 
    v.verse_num, 
    v.verse_text,
    v.translation_source,
    1 - (e.embedding <=> (SELECT embedding FROM query_embedding)) AS similarity
FROM 
    bible.verse_embeddings e
    JOIN bible.verses v ON e.verse_id = v.id
WHERE 
    v.translation_source = 'TAGNT'
UNION ALL
SELECT 
    'Arabic' AS source_type,
    NULL AS book_name,
    av.chapter, 
    av.verse, 
    av.text,
    'Arabic' AS translation_source,
    0.0 AS similarity  -- For Arabic verses without embeddings, ranked last
FROM 
    bible.arabic_verses av
WHERE 
    av.text ILIKE %s  -- Use text search for Arabic
ORDER BY 
    similarity DESC, source_type
LIMIT 20;
```

### 2. Lexicon-Enhanced Results

Enrich search results with relevant lexical information:

```python
def get_enriched_search_results(query, translation="KJV", limit=10):
    """
    Get semantic search results enriched with lexical data.
    """
    # Get query embedding vector
    query_embedding = get_embedding(query)
    
    # Determine which lexicon and word tables to use
    is_hebrew = translation in ['TAHOT']
    lexicon_table = "bible.hebrew_entries" if is_hebrew else "bible.greek_entries"
    word_table = "bible.hebrew_ot_words" if is_hebrew else "bible.greek_nt_words"
    lsj_join = "" if is_hebrew else "LEFT JOIN bible.lsj_entries lsj ON w.strongs_id = lsj.strongs_id"
    
    # Format the embedding for PostgreSQL
    embedding_array = format_vector_for_postgres(query_embedding)
    
    # Build and execute query
    sql = f"""
    WITH similar_verses AS (
        SELECT 
            v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text,
            v.translation_source,
            1 - (e.embedding <=> %s::vector) AS similarity
        FROM 
            bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
        WHERE 
            v.translation_source = %s
        ORDER BY 
            e.embedding <=> %s::vector
        LIMIT %s
    )
    SELECT 
        sv.book_name, sv.chapter_num, sv.verse_num, sv.verse_text, sv.similarity,
        w.word_text, w.word_position, w.strongs_id, w.grammar_code,
        l.lemma, l.definition, l.transliteration
        {', lsj.full_entry AS lsj_definition' if not is_hebrew else ''}
    FROM 
        similar_verses sv
        JOIN {word_table} w ON w.verse_id = sv.id
        JOIN {lexicon_table} l ON l.strongs_id = w.strongs_id
        {lsj_join}
    ORDER BY 
        sv.similarity DESC, sv.id, w.word_position
    """
    
    # Execute the query and return formatted results
    # ...implementation details...
```

### 3. Proper Name Search and Relationships

Enable searching for biblical proper names and their relationships:

```sql
-- Find all verses containing a specific proper name
WITH name_search AS (
    SELECT name_id 
    FROM bible.proper_names 
    WHERE name ILIKE %s OR transliteration ILIKE %s
)
SELECT 
    v.book_name, v.chapter_num, v.verse_num, v.verse_text,
    pn.name, pn.transliteration, pn.description,
    1 - (e.embedding <=> %s::vector) AS semantic_similarity
FROM 
    bible.proper_names pn
    JOIN bible.proper_name_forms pnf ON pn.name_id = pnf.name_id
    JOIN bible.hebrew_ot_words w ON w.word_text = pnf.form
    JOIN bible.verses v ON w.verse_id = v.id
    LEFT JOIN bible.verse_embeddings e ON v.id = e.verse_id
WHERE 
    pn.name_id IN (SELECT name_id FROM name_search)
ORDER BY 
    semantic_similarity DESC
LIMIT 20;

-- Find related names
SELECT 
    pn1.name AS name1, 
    pn2.name AS name2, 
    pnr.relationship_type
FROM 
    bible.proper_name_relationships pnr
    JOIN bible.proper_names pn1 ON pnr.name_id1 = pn1.name_id
    JOIN bible.proper_names pn2 ON pnr.name_id2 = pn2.name_id
WHERE 
    pn1.name ILIKE %s OR pn2.name ILIKE %s
LIMIT 20;
```

### 4. Cross-Language Term Mapping

Connect theological terms across language barriers:

```sql
-- Find equivalent terms across languages
WITH term_search AS (
    SELECT term_id 
    FROM bible.cross_language_terms 
    WHERE hebrew_term ILIKE %s OR greek_term ILIKE %s OR english_term ILIKE %s
)
SELECT 
    clt.hebrew_term, clt.greek_term, clt.english_term,
    clt.theological_category
FROM 
    bible.cross_language_terms clt
WHERE 
    clt.term_id IN (SELECT term_id FROM term_search);

-- Find verses containing equivalent terms in different languages
WITH term_search AS (
    SELECT term_id, hebrew_term, greek_term, english_term
    FROM bible.cross_language_terms 
    WHERE hebrew_term ILIKE %s OR greek_term ILIKE %s OR english_term ILIKE %s
)
SELECT 
    v.translation_source,
    v.book_name, v.chapter_num, v.verse_num, v.verse_text,
    ts.hebrew_term, ts.greek_term, ts.english_term,
    1 - (e.embedding <=> %s::vector) AS semantic_similarity
FROM 
    term_search ts
    LEFT JOIN bible.hebrew_ot_words hw ON hw.word_text ILIKE ts.hebrew_term
    LEFT JOIN bible.greek_nt_words gw ON gw.word_text ILIKE ts.greek_term
    LEFT JOIN bible.verses v ON v.id = COALESCE(hw.verse_id, gw.verse_id)
    LEFT JOIN bible.verse_embeddings e ON v.id = e.verse_id
WHERE 
    v.id IS NOT NULL
ORDER BY 
    semantic_similarity DESC
LIMIT 20;
```

### 5. Word Relationship Network

Leverage word relationship data to expand search context:

```sql
-- Find related words based on semantic relationships
WITH base_words AS (
    SELECT DISTINCT strongs_id
    FROM bible.hebrew_ot_words
    WHERE verse_id IN (
        SELECT id 
        FROM bible.verses
        WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
    )
)
SELECT 
    bw.strongs_id AS source_strongs,
    wr.related_strongs_id AS target_strongs,
    wr.relationship_type,
    he1.lemma AS source_lemma,
    he2.lemma AS target_lemma,
    he1.definition AS source_def,
    he2.definition AS target_def
FROM 
    base_words bw
    JOIN bible.word_relationships wr ON bw.strongs_id = wr.strongs_id
    JOIN bible.hebrew_entries he1 ON bw.strongs_id = he1.strongs_id
    JOIN bible.hebrew_entries he2 ON wr.related_strongs_id = he2.strongs_id
LIMIT 50;
```

### 6. Versification System Mapping

Handle different versification systems in search:

```sql
-- Map a verse reference between different versification systems
SELECT 
    source_book, source_chapter, source_verse,
    target_book, target_chapter, target_verse,
    system_from, system_to
FROM 
    bible.versification_mappings
WHERE 
    source_book = %s AND source_chapter = %s AND source_verse = %s
    AND system_from = %s AND system_to = %s;

-- Find a verse across different versification systems and translations
WITH verse_mappings AS (
    SELECT 
        source_book, source_chapter, source_verse,
        target_book, target_chapter, target_verse
    FROM 
        bible.versification_mappings
    WHERE 
        source_book = %s AND source_chapter = %s AND source_verse = %s
        AND system_from = 'KJV' -- source system
)
SELECT 
    v.translation_source,
    v.book_name, v.chapter_num, v.verse_num, v.verse_text,
    1 - (e.embedding <=> %s::vector) AS similarity
FROM 
    verse_mappings vm
    JOIN bible.verses v ON (
        v.book_name = vm.target_book AND 
        v.chapter_num = vm.target_chapter AND 
        v.verse_num = vm.target_verse
    )
    LEFT JOIN bible.verse_embeddings e ON v.id = e.verse_id
ORDER BY 
    similarity DESC;
```

### 7. Arabic Text Integration

Connect Arabic text with vector search capabilities:

```python
def search_arabic_with_vector_similarity(query, limit=10):
    """
    Search Arabic text with approximate vector similarity.
    
    Since Arabic verses might not have direct embeddings, we:
    1. Find the verse in a translation that does have embeddings
    2. Use that verse's embedding to find similar verses
    3. Map to corresponding Arabic verses
    """
    # First get query embedding
    query_embedding = get_embedding(query)
    embedding_array = format_vector_for_postgres(query_embedding)
    
    # Find similar verses in a translation with embeddings (KJV)
    sql = """
    WITH similar_kjv_verses AS (
        SELECT 
            v.book_name, v.chapter_num, v.verse_num,
            1 - (e.embedding <=> %s::vector) AS similarity
        FROM 
            bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
        WHERE 
            v.translation_source = 'KJV'
        ORDER BY 
            e.embedding <=> %s::vector
        LIMIT %s
    )
    SELECT 
        skv.book_name, skv.chapter_num, skv.verse_num, skv.similarity,
        av.text AS arabic_text
    FROM 
        similar_kjv_verses skv
        JOIN bible.arabic_verses av ON (
            av.book = skv.book_name AND 
            av.chapter = skv.chapter_num AND 
            av.verse = skv.verse_num
        )
    ORDER BY 
        skv.similarity DESC
    """
    
    # Execute the query and return results
    # ...implementation details...
```

## Implementation Architecture

The comprehensive search system will use these components:

### 1. Core API Endpoints

```
/api/comprehensive-search
  - q: query text
  - translation: primary translation to search
  - include_lexicon: include lexical data (default: true)
  - include_related: include related terms (default: true)
  - include_proper_names: identify and include proper names (default: true)
  - cross_language: search across language boundaries (default: false)
  - limit: maximum results (default: 10)

/api/theological-term-search
  - term: theological term to search
  - language: term language (hebrew, greek, english, arabic)
  - include_equivalent: include equivalent terms in other languages

/api/name-search
  - name: proper name to search
  - include_relationships: include related names
  - relationship_type: filter by relationship type
```

### 2. Database View Creation

Create views to simplify complex queries:

```sql
-- Create comprehensive verse view with embeddings
CREATE OR REPLACE VIEW bible.comprehensive_verses AS
SELECT 
    v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text, v.translation_source,
    e.embedding
FROM 
    bible.verses v
    LEFT JOIN bible.verse_embeddings e ON v.id = e.verse_id;

-- Create theological term view
CREATE OR REPLACE VIEW bible.theological_terms AS
SELECT 
    w.verse_id, w.word_text, w.strongs_id, w.word_position,
    v.book_name, v.chapter_num, v.verse_num, v.translation_source,
    h.lemma, h.definition
FROM 
    bible.hebrew_ot_words w
    JOIN bible.verses v ON w.verse_id = v.id
    JOIN bible.hebrew_entries h ON w.strongs_id = h.strongs_id
WHERE 
    w.strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
UNION ALL
SELECT 
    w.verse_id, w.word_text, w.strongs_id, w.word_position,
    v.book_name, v.chapter_num, v.verse_num, v.translation_source,
    g.lemma, g.definition
FROM 
    bible.greek_nt_words w
    JOIN bible.verses v ON w.verse_id = v.id
    JOIN bible.greek_entries g ON w.strongs_id = g.strongs_id
WHERE 
    w.strongs_id IN ('G2316', 'G2962', 'G26');
```

### 3. Function Implementation

Create reusable database functions:

```sql
-- Function to search verses with theological term highlighting
CREATE OR REPLACE FUNCTION bible.search_with_theological_terms(
    query_vector vector,
    translation_src text,
    limit_count integer
) RETURNS TABLE (
    book_name text,
    chapter_num integer,
    verse_num integer,
    verse_text text,
    translation_source text,
    similarity float,
    theological_terms jsonb
) AS $$
BEGIN
    RETURN QUERY
    WITH similar_verses AS (
        SELECT 
            v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text,
            v.translation_source,
            1 - (e.embedding <=> query_vector) AS similarity
        FROM 
            bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
        WHERE 
            v.translation_source = translation_src
        ORDER BY 
            e.embedding <=> query_vector
        LIMIT limit_count
    ),
    verse_theological_terms AS (
        SELECT 
            sv.id,
            jsonb_agg(
                jsonb_build_object(
                    'word', w.word_text,
                    'strongs_id', w.strongs_id,
                    'definition', l.definition,
                    'position', w.word_position
                )
            ) AS terms
        FROM 
            similar_verses sv
            JOIN bible.hebrew_ot_words w ON sv.id = w.verse_id
            JOIN bible.hebrew_entries l ON w.strongs_id = l.strongs_id
        WHERE 
            w.strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
        GROUP BY 
            sv.id
    )
    SELECT 
        sv.book_name,
        sv.chapter_num,
        sv.verse_num,
        sv.verse_text,
        sv.translation_source,
        sv.similarity,
        COALESCE(vtt.terms, '[]'::jsonb) AS theological_terms
    FROM 
        similar_verses sv
        LEFT JOIN verse_theological_terms vtt ON sv.id = vtt.id
    ORDER BY 
        sv.similarity DESC;
END;
$$ LANGUAGE plpgsql;
```

## Future Enhancements

1. **Generate Embeddings for Arabic Verses**
   - Create vector embeddings for Arabic verses for direct semantic search

2. **Cross-Lingual Embeddings**
   - Train or adapt embedding models that can bridge language differences

3. **Proper Name Entity Networks**
   - Build specialized search for biblical places, people, and events

4. **Theological Concept Vectors**
   - Create vector representations for specific theological concepts
   - Enable searching by theological meaning rather than just lexical content

5. **Advanced Statistics**
   - Generate statistical reports on word usage, theological term distribution
   - Create visualization tools for semantic relationships

## Implementation Schedule

1. **Phase 1: Base Integration**
   - Connect pgvector search with lexicon and word-level data
   - Implement API endpoints for lexicon-enhanced search

2. **Phase 2: Proper Name and Relationship Integration**
   - Add proper name search capabilities
   - Implement word relationship network navigation

3. **Phase 3: Cross-Language Integration**
   - Add cross-language term mapping
   - Implement functions for searching across language boundaries

4. **Phase 4: Arabic Integration**
   - Connect Arabic text with vector search
   - Implement versification system mapping for comprehensive results

5. **Phase 5: Advanced Features**
   - Implement theological concept vectors
   - Build visualization and statistical analysis tools 