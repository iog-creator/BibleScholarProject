# Additional Training Data for Bible QA

This document outlines how to utilize additional data sources from the Bible database for training and validating the Bible QA system.

## Available Data Sources

The Bible database contains rich data sources that can enhance training for the Bible QA system beyond the basic verse text. The full database schema can be inspected using:

```bash
python scripts/list_db_tables.py --verbose
```

Key tables include:

| Table | Description | Row Count | Key Fields |
|-------|-------------|-----------|------------|
| `verses` | Core verse texts across all translations | 93,426 | book_name, chapter_num, verse_num, translation_source |
| `hebrew_entries` | Hebrew lexicon with Strongs IDs | 9,349 | strongs_id, hebrew_word, definition |
| `greek_entries` | Greek lexicon with Strongs IDs | 10,847 | strongs_id, greek_word, definition |
| `hebrew_ot_words` | Hebrew OT words with Strongs IDs | 308,189 | book_name, chapter_num, verse_num, strongs_id |
| `greek_nt_words` | Greek NT words with Strongs IDs | 142,096 | book_name, chapter_num, verse_num, strongs_id |
| `arabic_verses` | Arabic translation verses | 31,091 | book_name, chapter_num, verse_num |
| `proper_names` | Biblical proper names | 1,317 | name, type, description |
| `verse_embeddings` | Vector embeddings for verses | 93,426 | verse_id, embedding |

## Training Data Generation

### Theological Term Training

Generate training examples focused on theological terms using Hebrew and Greek lexicons:

```python
# Example: Generate theological term QA pairs
def generate_theological_term_examples(output_file, num_examples=100):
    """
    Generate QA pairs focusing on theological terms from Hebrew and Greek lexicons.
    
    Args:
        output_file: Path to save the generated examples
        num_examples: Number of examples to generate
    """
    from src.database.secure_connection import get_secure_connection
    import json
    import random
    
    # Important Hebrew theological terms
    hebrew_terms = ['H430', 'H3068', 'H2617', 'H539', 'H7225']  # Elohim, YHWH, Hesed, Aman, Reshith
    
    # Important Greek theological terms
    greek_terms = ['G26', 'G5485', 'G4102', 'G1680', 'G40']  # Agape, Charis, Pistis, Elpis, Hagios
    
    conn = get_secure_connection(mode='read')
    examples = []
    
    try:
        with conn.cursor() as cursor:
            # Get Hebrew terms
            cursor.execute("""
                SELECT strongs_id, hebrew_word, definition, gloss
                FROM bible.hebrew_entries
                WHERE strongs_id IN %s
            """, (tuple(hebrew_terms),))
            
            hebrew_data = {row[0]: {
                'term': row[1],
                'definition': row[2],
                'gloss': row[3]
            } for row in cursor.fetchall()}
            
            # Get Greek terms
            cursor.execute("""
                SELECT strongs_id, greek_word, definition, gloss
                FROM bible.greek_entries
                WHERE strongs_id IN %s
            """, (tuple(greek_terms),))
            
            greek_data = {row[0]: {
                'term': row[1],
                'definition': row[2],
                'gloss': row[3]
            } for row in cursor.fetchall()}
            
            # Generate examples
            for _ in range(num_examples):
                # Randomly choose Hebrew or Greek
                if random.random() < 0.5 and hebrew_data:
                    strongs_id = random.choice(list(hebrew_data.keys()))
                    term_data = hebrew_data[strongs_id]
                    language = "Hebrew"
                elif greek_data:
                    strongs_id = random.choice(list(greek_data.keys()))
                    term_data = greek_data[strongs_id]
                    language = "Greek"
                else:
                    continue
                
                # Generate question
                term = term_data['term']
                gloss = term_data['gloss']
                
                question_types = [
                    f"What is the meaning of {term} ({strongs_id}) in the Bible?",
                    f"Explain the theological significance of {gloss} ({strongs_id}) in {language}.",
                    f"How is {gloss} ({strongs_id}) used in Biblical context?",
                    f"What is the definition of the {language} word {term} ({strongs_id})?"
                ]
                
                example = {
                    "question": random.choice(question_types),
                    "answer": term_data['definition'],
                    "metadata": {
                        "strongs_id": strongs_id,
                        "language": language,
                        "category": "theological_term"
                    }
                }
                
                examples.append(example)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')
                
        print(f"Generated {len(examples)} theological term examples")
        
    except Exception as e:
        print(f"Error generating theological term examples: {str(e)}")
    finally:
        conn.close()
```

### Cross-Language Training

To train the model on cross-language concepts:

```python
# Example: Generate cross-language concept examples
def generate_cross_language_examples(output_file, num_examples=50):
    """
    Generate examples that connect concepts across Hebrew, Greek and Arabic.
    
    Args:
        output_file: Path to save the generated examples
        num_examples: Number of examples to generate
    """
    # Implementation details...
```

### Proper Name Training

```python
# Example: Generate proper name examples
def generate_proper_name_examples(output_file, num_examples=50):
    """
    Generate examples about Biblical proper names and their relationships.
    
    Args:
        output_file: Path to save the generated examples
        num_examples: Number of examples to generate
    """
    # Implementation details...
```

## Integration with DSPy Training

The additional training data can be integrated with the DSPy training pipeline:

```python
# Update train_dspy_bible_qa.py to use additional data sources
def prepare_training_data():
    """Prepare comprehensive training data for DSPy Bible QA"""
    # Load regular QA pairs
    qa_pairs = load_qa_dataset("data/processed/bible_training_data/qa_dataset_train.jsonl")
    
    # Load theological term examples
    theological_examples = load_qa_dataset("data/processed/bible_training_data/theological_terms_train.jsonl")
    
    # Load cross-language examples
    cross_language_examples = load_qa_dataset("data/processed/bible_training_data/cross_language_train.jsonl")
    
    # Combine all data sources with appropriate weighting
    combined_examples = qa_pairs + theological_examples + cross_language_examples
    
    # Balance dataset to ensure proper representation
    return balance_dataset(combined_examples)
```

## Running the Training

To train the Bible QA system with the enhanced dataset:

1. Generate the additional training data:
```bash
python scripts/generate_theological_term_examples.py
python scripts/generate_cross_language_examples.py
python scripts/generate_proper_name_examples.py
```

2. Run the DSPy training with the enhanced dataset:
```bash
python train_dspy_bible_qa.py --use-enhanced-data
```

## Evaluating the Results

The enhanced training dataset should improve performance on:

1. Questions about theological concepts
2. Cross-language theological inquiries
3. Named entity questions about Biblical people, places, and events
4. Multi-turn conversational scenarios that build on previous context

Track the model's performance using MLflow:

```bash
# View training metrics
python -c "import mlflow; mlflow.search_runs(filter_string='tags.\"mlflow.runName\" = \"bible_qa_enhanced_training\"')"
```

## Best Practices

1. **Balance the Dataset**: Ensure equal representation of different categories (verses, theological terms, proper names).
2. **Cross-Validation**: Reserve some examples from each category for validation.
3. **Gradual Expansion**: Start with a small set of high-quality examples and gradually expand.
4. **Track Source Distribution**: Monitor the distribution of examples from different data sources.
5. **Focus on Quality**: Prioritize high-quality examples over quantity.

## References

- See the cursor rule `.cursor/rules/additional_training_data.mdc` for implementation guidelines
- Consult `docs/features/dataset_validation_expansion.md` for validation dataset expansion
- Review `docs/reference/DATABASE_SCHEMA.md` for detailed database schema information 