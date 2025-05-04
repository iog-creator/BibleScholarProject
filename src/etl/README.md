# ETL (Extract, Transform, Load) Components

This directory contains all the ETL scripts for processing STEPBible data.

## Contents

- `etl_lexicons.py`: Process Hebrew and Greek lexicon data
- `etl_greek_nt.py`: Process Greek New Testament tagged text
- `etl_hebrew_ot.py`: Process Hebrew Old Testament tagged text
- `etl_arabic_bible.py`: Process Arabic Bible (SVD) tagged text
- `extract_relationships.py`: Extract relationships between words

### Subdirectories

- `morphology/`: Scripts for processing Hebrew and Greek morphology codes
- `names/`: Scripts for processing proper names data

## Usage

The ETL scripts are typically run in the following order:

1. Load reference data (books, abbreviations)
2. Process lexicons (Hebrew and Greek)
3. Process morphology codes
4. Process tagged texts (Hebrew, Greek, Arabic)
5. Extract word relationships
6. Process proper names 