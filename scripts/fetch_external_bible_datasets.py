#!/usr/bin/env python3
"""
External Bible Datasets Fetcher

This script downloads and processes Bible datasets from various external sources
for integration with the BibleScholarProject's Bible QA system.

Usage:
    python scripts/fetch_external_bible_datasets.py --output-dir data/raw/external_datasets
"""

import os
import sys
import json
import logging
import argparse
import requests
import zipfile
import tarfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dataset_fetcher.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define paths
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "external_datasets"
PROCESSED_DIR = DATA_DIR / "processed" / "dspy_training_data" / "external"

# Create necessary directories
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def download_file(url: str, output_path: Path, description: str = "dataset") -> bool:
    """
    Download a file from a URL to a specified path with progress reporting.
    
    Args:
        url: URL to download
        output_path: Path to save the file
        description: Description for logging
        
    Returns:
        bool: Success or failure
    """
    try:
        logger.info(f"Downloading {description} from {url}")
        
        # Make a streaming request
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Get total file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Write the file
        with open(output_path, 'wb') as f:
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Report progress for large files
                    if total_size > 10 * 1024 * 1024:  # For files > 10MB
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Downloaded {downloaded / (1024 * 1024):.1f}MB / {total_size / (1024 * 1024):.1f}MB ({percent:.1f}%)")
        
        logger.info(f"Successfully downloaded {description} to {output_path}")
        return True
    
    except requests.RequestException as e:
        logger.error(f"Error downloading {description}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text[:500]}...")
        return False
    
    except Exception as e:
        logger.error(f"Error downloading {description}: {e}")
        return False

def extract_archive(archive_path: Path, extract_dir: Path) -> bool:
    """
    Extract a zip or tar archive.
    
    Args:
        archive_path: Path to the archive
        extract_dir: Directory to extract to
        
    Returns:
        bool: Success or failure
    """
    try:
        logger.info(f"Extracting {archive_path} to {extract_dir}")
        
        if not extract_dir.exists():
            extract_dir.mkdir(parents=True)
        
        if str(archive_path).endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        elif str(archive_path).endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_dir)
        
        elif str(archive_path).endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_dir)
        
        else:
            logger.error(f"Unsupported archive format: {archive_path}")
            return False
        
        logger.info(f"Successfully extracted {archive_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error extracting archive {archive_path}: {e}")
        return False

def fetch_strongs_dictionary() -> List[Dict[str, Any]]:
    """
    Fetch and process Strong's dictionary data.
    
    Returns:
        List of QA pairs about Strong's dictionary entries
    """
    try:
        logger.info("Processing Strong's dictionary data")
        
        # URLs for Strong's dictionary data
        urls = {
            "hebrew": "https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.json",
            "greek": "https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.json"
        }
        
        qa_pairs = []
        
        for lang, url in urls.items():
            output_path = RAW_DIR / f"strongs-{lang}-dictionary.json"
            
            # Download the file if it doesn't exist
            if not output_path.exists() or os.path.getsize(output_path) < 1000:
                if not download_file(url, output_path, f"Strong's {lang} dictionary"):
                    continue
            
            # Read and process the dictionary
            with open(output_path, 'r', encoding='utf-8') as f:
                dictionary = json.load(f)
            
            # Generate QA pairs from dictionary entries
            for strongs_id, entry in dictionary.items():
                # Skip entries with missing data
                if not entry.get("lemma") or not entry.get("derivation") or not entry.get("strongs_def"):
                    continue
                
                # Create context
                context = f"Strong's: {strongs_id}, {lang.capitalize()}: {entry.get('lemma', '')}, "
                context += f"Transliteration: {entry.get('translit', '')}, "
                context += f"Definition: {entry.get('strongs_def', '')}"
                
                # Create QA pair about definition
                qa_pairs.append({
                    "question": f"What is the meaning of the {lang} word '{entry.get('lemma', '')}' (Strong's {strongs_id})?",
                    "answer": f"The {lang} word '{entry.get('lemma', '')}' (Strong's {strongs_id}) means: {entry.get('strongs_def', '')}",
                    "context": context,
                    "metadata": {
                        "source": "strongs_dictionary",
                        "type": "lexical",
                        "strongs_id": strongs_id,
                        "language": lang
                    }
                })
                
                # Create QA pair about etymology
                if entry.get("derivation"):
                    qa_pairs.append({
                        "question": f"What is the derivation or etymology of the {lang} word '{entry.get('lemma', '')}' (Strong's {strongs_id})?",
                        "answer": f"The {lang} word '{entry.get('lemma', '')}' (Strong's {strongs_id}) is derived from: {entry.get('derivation', '')}",
                        "context": context,
                        "metadata": {
                            "source": "strongs_dictionary",
                            "type": "etymology",
                            "strongs_id": strongs_id,
                            "language": lang
                        }
                    })
        
        logger.info(f"Generated {len(qa_pairs)} QA pairs from Strong's dictionary")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error processing Strong's dictionary: {e}")
        return []

def fetch_web_bible_text() -> List[Dict[str, Any]]:
    """
    Fetch and process World English Bible (WEB) translation.
    
    Returns:
        List of QA pairs about WEB verses
    """
    try:
        logger.info("Processing World English Bible (WEB) data")
        
        # URL for WEB Bible JSON
        url = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_web.json"
        output_path = RAW_DIR / "en_web.json"
        
        # Download the file if it doesn't exist
        if not output_path.exists() or os.path.getsize(output_path) < 1000:
            if not download_file(url, output_path, "World English Bible (WEB)"):
                return []
        
        # Read and process the Bible data
        with open(output_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        
        qa_pairs = []
        
        # Generate QA pairs from verses
        for book in bible_data:
            book_name = book.get("name", "")
            book_abbrev = book.get("abbrev", "")
            
            for chapter_idx, chapter in enumerate(book.get("chapters", []), 1):
                for verse_idx, verse_text in enumerate(chapter, 1):
                    # Skip empty verses
                    if not verse_text or len(verse_text.strip()) < 5:
                        continue
                    
                    # Create reference
                    reference = f"{book_name} {chapter_idx}:{verse_idx}"
                    
                    # Create QA pair about verse content
                    qa_pairs.append({
                        "question": f"What does {reference} say in the World English Bible translation?",
                        "answer": verse_text,
                        "context": f"Book: {book_name}, Chapter: {chapter_idx}, Verse: {verse_idx}, Translation: WEB",
                        "metadata": {
                            "source": "web_bible",
                            "type": "verse_text",
                            "book": book_name,
                            "chapter": chapter_idx,
                            "verse": verse_idx,
                            "translation": "WEB"
                        }
                    })
                    
                    # Create QA pair about verse meaning (for selected verses)
                    if len(verse_text.split()) > 10 and (verse_idx == 1 or verse_idx % 10 == 0):
                        qa_pairs.append({
                            "question": f"What is the meaning or significance of {reference}?",
                            "answer": f"In {reference}, the Bible says: '{verse_text}'. This verse " +
                                    f"is part of the {book_name} chapter {chapter_idx} narrative.",
                            "context": f"Book: {book_name}, Chapter: {chapter_idx}, Verse: {verse_idx}, Translation: WEB",
                            "metadata": {
                                "source": "web_bible",
                                "type": "verse_meaning",
                                "book": book_name,
                                "chapter": chapter_idx,
                                "verse": verse_idx,
                                "translation": "WEB"
                            }
                        })
        
        logger.info(f"Generated {len(qa_pairs)} QA pairs from WEB Bible")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error processing WEB Bible: {e}")
        return []

def fetch_step_bible_lexicons() -> List[Dict[str, Any]]:
    """
    Fetch and process STEP Bible lexicons data.
    
    Returns:
        List of QA pairs about lexical entries
    """
    try:
        logger.info("Processing STEP Bible lexicons data")
        
        # Check if STEPBible-Data directory exists locally
        step_dir = BASE_DIR / "STEPBible-Data"
        
        if not step_dir.exists():
            # Download from GitHub if not available locally
            logger.info("STEPBible-Data not found locally, downloading from GitHub")
            github_url = "https://github.com/STEPBible/STEPBible-Data/archive/refs/heads/master.zip"
            output_path = RAW_DIR / "STEPBible-Data.zip"
            
            if not download_file(github_url, output_path, "STEP Bible data"):
                return []
            
            # Extract the ZIP file
            extract_dir = RAW_DIR / "STEPBible-Data-extract"
            if not extract_archive(output_path, extract_dir):
                return []
            
            # Move the extracted directory to the correct location
            extracted_dir = extract_dir / "STEPBible-Data-master"
            if extracted_dir.exists():
                if step_dir.exists():
                    shutil.rmtree(step_dir)
                shutil.move(str(extracted_dir), str(step_dir))
        
        # Process STEP Bible lexicons
        lexicon_paths = list(step_dir.glob("Lexicons/*.txt"))
        
        if not lexicon_paths:
            logger.error("No lexicon files found in STEPBible-Data")
            return []
        
        qa_pairs = []
        
        for lexicon_path in lexicon_paths:
            lexicon_name = lexicon_path.stem
            
            # Skip files that aren't actual lexicons
            if "readme" in lexicon_name.lower() or "license" in lexicon_name.lower():
                continue
            
            logger.info(f"Processing lexicon: {lexicon_name}")
            
            try:
                # Read the lexicon file
                with open(lexicon_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Process each line
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse tab-separated data
                    parts = line.split("\t")
                    if len(parts) < 3:
                        continue
                    
                    # Extract key information
                    strongs_id = parts[0].strip() if len(parts) > 0 else ""
                    lemma = parts[1].strip() if len(parts) > 1 else ""
                    definition = parts[2].strip() if len(parts) > 2 else ""
                    
                    # Skip entries with missing data
                    if not strongs_id or not lemma or not definition:
                        continue
                    
                    # Determine language
                    lang = "Hebrew" if strongs_id.startswith("H") else "Greek" if strongs_id.startswith("G") else "Unknown"
                    
                    # Create context
                    context = f"Strong's: {strongs_id}, {lang}: {lemma}, Definition: {definition}, Source: STEP Bible {lexicon_name}"
                    
                    # Create QA pair
                    qa_pairs.append({
                        "question": f"What does the STEP Bible lexicon say about the {lang} word '{lemma}' (Strong's {strongs_id})?",
                        "answer": f"According to the STEP Bible {lexicon_name} lexicon, the {lang} word '{lemma}' (Strong's {strongs_id}) means: {definition}",
                        "context": context,
                        "metadata": {
                            "source": "step_bible_lexicon",
                            "type": "lexical",
                            "strongs_id": strongs_id,
                            "lexicon": lexicon_name,
                            "language": lang.lower()
                        }
                    })
            
            except Exception as e:
                logger.error(f"Error processing lexicon file {lexicon_path}: {e}")
                continue
        
        logger.info(f"Generated {len(qa_pairs)} QA pairs from STEP Bible lexicons")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error processing STEP Bible lexicons: {e}")
        return []

def save_qa_pairs(qa_pairs: List[Dict[str, Any]], output_dir: Path, dataset_name: str):
    """
    Save QA pairs to a JSONL file.
    
    Args:
        qa_pairs: List of QA pairs
        output_dir: Directory to save to
        dataset_name: Name of the dataset
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output file
        output_path = output_dir / f"{dataset_name}_qa_pairs.jsonl"
        
        # Write QA pairs to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for qa_pair in qa_pairs:
                f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(qa_pairs)} QA pairs to {output_path}")
    
    except Exception as e:
        logger.error(f"Error saving QA pairs: {e}")

def main():
    """Main function to fetch and process external Bible datasets."""
    parser = argparse.ArgumentParser(description="Fetch and process external Bible datasets")
    parser.add_argument("--output-dir", type=str, default="data/processed/dspy_training_data/external",
                      help="Directory to save processed datasets")
    args = parser.parse_args()
    
    # Get output directory
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each dataset
    datasets = {
        "strongs_dictionary": fetch_strongs_dictionary,
        "web_bible": fetch_web_bible_text,
        "step_bible_lexicons": fetch_step_bible_lexicons
    }
    
    all_qa_pairs = []
    
    # Process each dataset
    for dataset_name, fetch_function in datasets.items():
        try:
            logger.info(f"Processing dataset: {dataset_name}")
            qa_pairs = fetch_function()
            
            if qa_pairs:
                # Save individual dataset
                save_qa_pairs(qa_pairs, output_dir, dataset_name)
                
                # Add to combined dataset
                all_qa_pairs.extend(qa_pairs)
                logger.info(f"Added {len(qa_pairs)} QA pairs from {dataset_name}")
            else:
                logger.warning(f"No QA pairs generated for {dataset_name}")
        
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_name}: {e}")
    
    # Save combined dataset
    save_qa_pairs(all_qa_pairs, output_dir, "all_external_datasets")
    
    logger.info(f"Total QA pairs across all datasets: {len(all_qa_pairs)}")
    logger.info("External dataset processing complete")

if __name__ == "__main__":
    main() 