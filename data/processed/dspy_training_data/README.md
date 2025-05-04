# DSPy Training Data Directory

This directory contains all training data files for DSPy-based AI model development in the BibleScholarProject.

## File Naming and Purpose

- `hebrew_ot_tagging.jsonl`: Hebrew Old Testament word tagging (context: verse + word, labels: strongs_id, lemma, morphology)
- `greek_nt_tagging.jsonl`: Greek New Testament word tagging (context: verse + word, labels: strongs_id, lemma, morphology)
- `lexicon_lookup.jsonl`: Lexicon entry lookup (context: raw entry, labels: lemma, strongs_id, gloss, definition)
- `hebrew_strongs_fix_training_data.jsonl`: Hebrew Strong's ID extraction/fix (context: word + grammar_code, labels: extracted_strongs_id, fixed)
- `lexicon_api.jsonl`: API queries and responses for lexicon endpoints
- `tagged_text_api.jsonl`: API queries and responses for tagged text endpoints
- `morphology_api.jsonl`: API queries and responses for morphology endpoints
- `proper_names_api.jsonl`: API queries and responses for proper names endpoints
- `external_resources_api.jsonl`: API queries and responses for external resources endpoints

## Schema

Each file is a JSONL file (one JSON object per line) with the following fields:

- `context`: The input string (e.g., verse text, query, API endpoint + params)
- `labels`: The expected output (dict or string, e.g., tags, answer, parsed fields)
- `metadata` (optional): Any extra information (e.g., verse_ref, word_num, entry_type)

## Example
```json
{"context": "Gen 1:1 אלהים", "labels": {"strongs_id": "H430", "lemma": "אלהים", "morphology": "Noun"}, "metadata": {"verse_ref": "Gen.1.1", "word_num": 1}}
```

## Validation and Deduplication

- Use the provided validation script (`scripts/validate_dspy_training_data.py`) to check for malformed JSON, missing fields, or schema errors in all `.jsonl` files.
- Use the deduplication script (`scripts/deduplicate_dspy_training_data.py`) to remove duplicate examples (by `context` + `labels`).
- Do not log sensitive or user-identifiable data (see `.cursor/rules/database_access.mdc`).

## Using with DSPy

You can load these files as `dspy.Example` objects for use in DSPy pipelines:

```python
import dspy
import json

with open('data/processed/dspy_training_data/hebrew_ot_tagging.jsonl') as f:
    trainset = [dspy.Example(**json.loads(line)) for line in f]
```

See the [DSPy Example API](https://dspy.ai/api/primitives/Example/) for more details.

## References
- See `.cursor/rules/README.md` for project rules on DSPy training data logging
- [DSPy Programming Overview](https://dspy.ai/learn/programming/overview/)
- [DSPy Example API](https://dspy.ai/api/primitives/Example/) 