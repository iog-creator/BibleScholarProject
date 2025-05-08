#!/usr/bin/env python3
"""
Enhanced Bible QA with DSPy and Database Verification

This module implements a Bible QA system that:
1. Uses DSPy-optimized models for question answering
2. Verifies answers against the Bible database for factual accuracy
3. Utilizes extensive example datasets for few-shot learning
4. Combines database lookup with model reasoning
5. Handles theological concepts with proper term recognition

Usage:
    from src.dspy_programs.enhanced_bible_qa import EnhancedBibleQA
    
    qa_system = EnhancedBibleQA()
    response = qa_system.answer("What does Genesis 1:1 say?")
"""

import os
import sys
import json
import logging
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import dspy
import mlflow
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import database utilities
from src.database.connection import get_db_connection, get_connection_string
from src.database.secure_connection import get_secure_connection, secure_connection
from src.utils.bible_reference_parser import parse_reference
from src.utils.vector_search import search_verses_by_semantic_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bible_qa_enhanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
dspy_env_path = Path(".env.dspy")
if dspy_env_path.exists():
    load_dotenv(dspy_env_path, override=True)
    logger.info("Loaded DSPy environment variables")

# Define signatures for DSPy
class BibleReferenceExtractor(dspy.Signature):
    """Extract Bible references from a question."""
    question = dspy.InputField(desc="The question about the Bible")
    references = dspy.OutputField(desc="List of Bible references mentioned in the question (e.g., ['Genesis 1:1', 'John 3:16'])")
    requires_lookup = dspy.OutputField(desc="Whether the question requires looking up specific Bible verses (true/false)")

class TheologicalTermExtractor(dspy.Signature):
    """Extract theological terms from a question."""
    question = dspy.InputField(desc="The question about the Bible")
    theological_terms = dspy.OutputField(desc="List of theological terms mentioned in the question (e.g., ['Elohim', 'YHWH', 'Chesed'])")
    hebrew_terms = dspy.OutputField(desc="List of Hebrew terms with Strong's numbers if present (e.g., ['H430 (Elohim)', 'H3068 (YHWH)'])")

class BibleQA(dspy.Signature):
    """Answer questions about the Bible with DB-verified responses."""
    question = dspy.InputField(desc="The question about the Bible")
    context = dspy.InputField(desc="Bible verses and information relevant to the question")
    theological_terms = dspy.InputField(desc="Theological terms relevant to the question")
    answer = dspy.OutputField(desc="Precise, factual answer to the question based on the Bible")

class DatabaseVerifier(dspy.Signature):
    """Verify if an answer is consistent with the Bible database."""
    question = dspy.InputField(desc="The original question")
    proposed_answer = dspy.InputField(desc="The proposed answer to verify")
    database_context = dspy.InputField(desc="Relevant information from the Bible database")
    is_consistent = dspy.OutputField(desc="Whether the proposed answer is consistent with the database (true/false)")
    corrected_answer = dspy.OutputField(desc="Corrected answer if the proposed answer was inconsistent")
    explanation = dspy.OutputField(desc="Explanation of why the answer was or wasn't consistent")

class EnhancedBibleQA:
    """
    Enhanced Bible QA system that combines DSPy-optimized models with database verification.
    """
    
    def __init__(self, model_path: str = None, use_lm_studio: bool = False):
        """
        Initialize the Enhanced Bible QA system.
        
        Args:
            model_path: Path to the DSPy model to use (None for default)
            use_lm_studio: Whether to use LM Studio for inference
        """
        self.model_path = model_path
        self.use_lm_studio = use_lm_studio
        self.db_conn = None
        self.default_translation = "KJV"  # Default to King James Version
        
        # Initialize DSPy modules
        self._initialize_dspy()
        
        # Load example datasets
        self._load_examples()
        
    def _initialize_dspy(self):
        """Initialize DSPy modules and LM configuration."""
        
        # Configure the language model based on settings
        if self.use_lm_studio:
            lm_studio_api_url = os.environ.get('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
            lm_studio_model = os.environ.get('LM_STUDIO_CHAT_MODEL', 'mistral-nemo-instruct-2407')
            
            logger.info(f"Using LM Studio with model {lm_studio_model}")
            
            # Simply create an LM with openai base_url
            lm = dspy.LM(
                f"openai/{lm_studio_model}",
                api_base=lm_studio_api_url,
                api_key="dummy-key"  # LM Studio doesn't check API key
            )
            dspy.settings.configure(lm=lm)
        else:
            # Try to load a saved DSPy model
            if self.model_path:
                logger.info(f"Loading DSPy model from {self.model_path}")
                try:
                    # Try to load with MLflow first
                    try:
                        import mlflow.dspy
                        model = mlflow.dspy.load_model(self.model_path)
                        logger.info(f"Loaded model from MLflow: {self.model_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load from MLflow: {e}")
                        # Fall back to regular loading
                        model = dspy.load(self.model_path)
                        logger.info(f"Loaded model from path: {self.model_path}")
                    
                    # Extract the LM from the loaded model if possible
                    if hasattr(model, "lm"):
                        dspy.settings.configure(lm=model.lm)
                    # Otherwise, use the model directly
                    else:
                        dspy.settings.configure(lm=model)
                except Exception as e:
                    logger.error(f"Error loading model: {e}")
                    logger.warning("Falling back to default model configuration")
                    # Continue with default configuration
            else:
                logger.info("Using default DSPy configuration")
                # Default model configuration will be used
        
        # Initialize the module pipeline
        self.reference_extractor = dspy.ChainOfThought(BibleReferenceExtractor)
        self.term_extractor = dspy.ChainOfThought(TheologicalTermExtractor)
        self.qa_module = dspy.ChainOfThought(BibleQA)
        self.verifier = dspy.ChainOfThought(DatabaseVerifier)
        
    def _load_examples(self):
        """Load example datasets for few-shot learning."""
        self.qa_examples = []
        self.theological_examples = []
        
        # Load QA examples
        try:
            qa_path = Path("data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json")
            if qa_path.exists():
                with open(qa_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert to DSPy examples
                    for item in data:
                        example = dspy.Example(
                            question=item.get("question", ""),
                            context=item.get("context", ""),
                            theological_terms="",  # Will fill this later
                            answer=item.get("answer", "")
                        )
                        self.qa_examples.append(example)
                logger.info(f"Loaded {len(self.qa_examples)} QA examples from {qa_path}")
        except Exception as e:
            logger.error(f"Error loading QA examples: {e}")
        
        # Load theological term examples
        try:
            terms_path = Path("data/processed/dspy_training_data/theological_terms_dataset.jsonl")
            if terms_path.exists():
                with open(terms_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('//'):
                            data = json.loads(line)
                            # Create theological example
                            term_info = [
                                f"{data.get('strongs_id', '')} ({data.get('transliteration', '')}): {data.get('definition', '')}"
                            ]
                            example = dspy.Example(
                                question=f"What is the meaning of {data.get('transliteration', '')}?",
                                theological_terms=term_info,
                                hebrew_terms=[f"{data.get('strongs_id', '')} ({data.get('transliteration', '')})"]
                            )
                            self.theological_examples.append(example)
                logger.info(f"Loaded {len(self.theological_examples)} theological term examples from {terms_path}")
        except Exception as e:
            logger.error(f"Error loading theological term examples: {e}")
            
    def _get_db_connection(self):
        """Get a database connection, creating it if needed."""
        if self.db_conn is None:
            # Create a new connection
            try:
                self.db_conn = get_db_connection()
                logger.info("Connected to Bible database")
            except Exception as e:
                logger.error(f"Error connecting to database: {e}")
                try:
                    self.db_conn = get_secure_connection(mode='read')
                    logger.info("Connected to Bible database using secure connection")
                except Exception as e:
                    logger.error(f"Error connecting to database with secure connection: {e}")
                    self.db_conn = None
        return self.db_conn
    
    def _look_up_verses(self, references: List[str], translation: str = None) -> str:
        """Look up Bible verses by reference."""
        if not translation:
            translation = self.default_translation
            
        context_verses = []
        conn = self._get_db_connection()
        
        with conn.cursor() as cur:
            for ref in references:
                try:
                    # Parse the reference
                    parsed = parse_reference(ref)
                    if not parsed:
                        continue
                        
                    book, chapter, verse_start, verse_end = parsed
                    
                    # If verse_end is None, set it to verse_start for single verse lookup
                    if verse_end is None:
                        verse_end = verse_start
                    
                    # Query the database
                    query = """
                    SELECT book_name, chapter_num, verse_num, verse_text
                    FROM bible.verses
                    WHERE book_name = %s
                    AND chapter_num = %s
                    AND verse_num BETWEEN %s AND %s
                    AND translation_source = %s
                    ORDER BY chapter_num, verse_num
                    """
                    
                    cur.execute(query, (book, chapter, verse_start, verse_end, translation))
                    verses = cur.fetchall()
                    
                    for verse in verses:
                        book_name, chapter_num, verse_num, verse_text = verse
                        context_verses.append(f"{book_name} {chapter_num}:{verse_num}: {verse_text}")
                        
                except Exception as e:
                    logger.error(f"Error looking up reference {ref}: {e}")
        
        return "\n".join(context_verses)
    
    def _get_verses_by_semantic_search(self, question: str, top_k: int = 5, translation: str = None) -> str:
        """Get relevant verses using semantic search."""
        if not translation:
            translation = self.default_translation
            
        try:
            # Use vector search to find relevant verses
            results = search_verses_by_semantic_similarity(question, translation, limit=top_k)
            
            context_verses = []
            for verse in results:
                book_name = verse.get('book_name')
                chapter_num = verse.get('chapter_num')
                verse_num = verse.get('verse_num')
                verse_text = verse.get('verse_text')
                
                context_verses.append(f"{book_name} {chapter_num}:{verse_num}: {verse_text}")
                
            return "\n".join(context_verses)
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return ""
    
    def _get_theological_terms(self, terms: List[str]) -> str:
        """Look up theological terms in the database."""
        if not terms:
            return ""
            
        conn = self._get_db_connection()
        term_info = []
        
        with conn.cursor() as cur:
            for term in terms:
                # Extract Strong's ID if present (e.g., "H430")
                strongs_match = re.search(r'([HG]\d+)', term)
                
                if strongs_match:
                    strongs_id = strongs_match.group(1)
                    
                    # Query the appropriate table based on Strong's ID prefix
                    if strongs_id.startswith('H'):
                        query = """
                        SELECT strongs_id, hebrew_word as term, transliteration, definition
                        FROM bible.hebrew_entries
                        WHERE strongs_id = %s
                        """
                    else:  # G prefix
                        query = """
                        SELECT strongs_id, greek_word as term, transliteration, definition
                        FROM bible.greek_entries
                        WHERE strongs_id = %s
                        """
                    
                    cur.execute(query, (strongs_id,))
                    results = cur.fetchall()
                    
                    for result in results:
                        # Handle both tuple and dict result types
                        if isinstance(result, dict):
                            s_id = result.get('strongs_id', '')
                            s_term = result.get('term', '')
                            s_trans = result.get('transliteration', '')
                            s_def = result.get('definition', '')
                        else:  # Handle as tuple
                            s_id = result[0] if len(result) > 0 else ''
                            s_term = result[1] if len(result) > 1 else ''
                            s_trans = result[2] if len(result) > 2 else ''
                            s_def = result[3] if len(result) > 3 else ''
                        term_info.append(f"{s_id} ({s_trans}): {s_def}")
                else:
                    # Try to look up by transliteration
                    # Remove parentheses if present
                    clean_term = re.sub(r'[\(\)]', '', term).strip()
                    
                    # Try Hebrew entries first
                    query = """
                    SELECT strongs_id, hebrew_word as term, transliteration, definition
                    FROM bible.hebrew_entries
                    WHERE LOWER(transliteration) = LOWER(%s)
                    OR LOWER(hebrew_word) = LOWER(%s)
                    """
                    
                    cur.execute(query, (clean_term, clean_term))
                    results = cur.fetchall()
                    
                    if not results:
                        # Try Greek entries if Hebrew returned nothing
                        query = """
                        SELECT strongs_id, greek_word as term, transliteration, definition
                        FROM bible.greek_entries
                        WHERE LOWER(transliteration) = LOWER(%s)
                        OR LOWER(greek_word) = LOWER(%s)
                        """
                        
                        cur.execute(query, (clean_term, clean_term))
                        results = cur.fetchall()
                    
                    for result in results:
                        # Handle both tuple and dict result types
                        if isinstance(result, dict):
                            s_id = result.get('strongs_id', '')
                            s_term = result.get('term', '')
                            s_trans = result.get('transliteration', '')
                            s_def = result.get('definition', '')
                        else:  # Handle as tuple
                            s_id = result[0] if len(result) > 0 else ''
                            s_term = result[1] if len(result) > 1 else ''
                            s_trans = result[2] if len(result) > 2 else ''
                            s_def = result[3] if len(result) > 3 else ''
                        term_info.append(f"{s_id} ({s_trans}): {s_def}")
        
        return "\n".join(term_info)
    
    def answer(self, question: str, translation: str = None) -> Dict[str, Any]:
        """
        Answer a Bible question with database verification.
        
        Args:
            question: The Bible question to answer
            translation: Bible translation to use (default: KJV)
            
        Returns:
            Dictionary containing the answer and metadata
        """
        if not translation:
            translation = self.default_translation
        
        # Step 1: Extract Bible references from the question
        reference_result = self.reference_extractor(question=question)
        references = reference_result.references
        requires_lookup = reference_result.requires_lookup
        
        # Convert string to list if needed
        if isinstance(references, str):
            if references.startswith('[') and references.endswith(']'):
                # Parse JSON array
                try:
                    references = json.loads(references)
                except:
                    references = [r.strip() for r in references.strip('[]').split(',')]
            else:
                references = [references]
        
        # Step 2: Extract theological terms
        term_result = self.term_extractor(question=question)
        theological_terms = term_result.theological_terms
        hebrew_terms = term_result.hebrew_terms
        
        # Convert string to list if needed
        if isinstance(theological_terms, str):
            if theological_terms.startswith('[') and theological_terms.endswith(']'):
                try:
                    theological_terms = json.loads(theological_terms)
                except:
                    theological_terms = [t.strip() for t in theological_terms.strip('[]').split(',')]
            else:
                theological_terms = [theological_terms]
                
        if isinstance(hebrew_terms, str):
            if hebrew_terms.startswith('[') and hebrew_terms.endswith(']'):
                try:
                    hebrew_terms = json.loads(hebrew_terms)
                except:
                    hebrew_terms = [t.strip() for t in hebrew_terms.strip('[]').split(',')]
            else:
                hebrew_terms = [hebrew_terms]
        
        # Step 3: Look up Bible verses and theological terms
        context = ""
        
        # If specific references were extracted, look them up
        if references and requires_lookup:
            verse_context = self._look_up_verses(references, translation)
            if verse_context:
                context += verse_context + "\n\n"
        
        # If no specific references or additional context needed, use semantic search
        if not references or not requires_lookup or not context:
            semantic_context = self._get_verses_by_semantic_search(question, translation=translation)
            if semantic_context:
                context += "Semantically relevant verses:\n" + semantic_context + "\n\n"
        
        # Look up theological terms
        term_context = ""
        all_terms = list(set(theological_terms + hebrew_terms))
        if all_terms:
            term_context = self._get_theological_terms(all_terms)
            if term_context:
                context += "Theological terms:\n" + term_context
        
        # Step 4: Generate answer using DSPy
        qa_result = self.qa_module(
            question=question,
            context=context,
            theological_terms=term_context
        )
        proposed_answer = qa_result.answer
        
        # Step 5: Verify answer against database
        verification = self.verifier(
            question=question,
            proposed_answer=proposed_answer,
            database_context=context
        )
        
        # Determine final answer based on verification
        final_answer = proposed_answer
        if hasattr(verification, 'is_consistent') and not verification.is_consistent:
            if hasattr(verification, 'corrected_answer') and verification.corrected_answer:
                final_answer = verification.corrected_answer
        
        # Log the result with MLflow if available
        try:
            with mlflow.start_run(run_name="bible_qa_inference"):
                mlflow.log_param("question", question)
                mlflow.log_param("translation", translation)
                mlflow.log_metric("references_found", len(references) if references else 0)
                mlflow.log_metric("theological_terms_found", len(all_terms) if all_terms else 0)
                
                # Log whether verification changed the answer
                answer_changed = final_answer != proposed_answer
                mlflow.log_metric("answer_verified", 0 if answer_changed else 1)
                
                # Log artifacts
                with open("logs/temp_context.txt", "w", encoding="utf-8") as f:
                    f.write(context)
                mlflow.log_artifact("logs/temp_context.txt")
        except Exception as e:
            logger.warning(f"Failed to log with MLflow: {e}")
        
        # Return the result
        return {
            "question": question,
            "answer": final_answer,
            "references": references,
            "theological_terms": all_terms,
            "context": context,
            "proposed_answer": proposed_answer,
            "verification": {
                "is_consistent": getattr(verification, 'is_consistent', True),
                "explanation": getattr(verification, 'explanation', "")
            }
        }
        
def configure_optimizers(qa_system: EnhancedBibleQA):
    """Configure DSPy optimizers for the QA system components."""
    # Define metrics
    from dspy.teleprompt import BootstrapFewShot
    
    # Use bootstrap few-shot learning for reference extraction
    bootstrap_ref = BootstrapFewShot(qa_system.reference_extractor, max_bootstrapped_demos=5)
    qa_system.reference_extractor = bootstrap_ref.compile(qa_system.qa_examples)
    
    # Bootstrap theological term extraction
    bootstrap_term = BootstrapFewShot(qa_system.term_extractor, max_bootstrapped_demos=5)
    qa_system.term_extractor = bootstrap_term.compile(qa_system.theological_examples)
    
    # Bootstrap QA module with all examples
    bootstrap_qa = BootstrapFewShot(qa_system.qa_module, max_bootstrapped_demos=8)
    qa_system.qa_module = bootstrap_qa.compile(qa_system.qa_examples)
    
    return qa_system

def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="Enhanced Bible QA with Database Verification")
    parser.add_argument("--question", type=str, help="Question to answer")
    parser.add_argument("--translation", type=str, default="KJV", help="Bible translation to use")
    parser.add_argument("--model-path", type=str, help="Path to DSPy model")
    parser.add_argument("--use-lm-studio", action="store_true", help="Use LM Studio for inference")
    parser.add_argument("--optimize", action="store_true", help="Apply DSPy optimizers")
    args = parser.parse_args()
    
    # Create and configure QA system
    qa_system = EnhancedBibleQA(model_path=args.model_path, use_lm_studio=args.use_lm_studio)
    
    # Apply optimizers if requested
    if args.optimize:
        qa_system = configure_optimizers(qa_system)
    
    # Answer the question if provided
    if args.question:
        result = qa_system.answer(args.question, translation=args.translation)
        
        # Print formatted result
        print("\nQuestion:", result["question"])
        print("\nAnswer:", result["answer"])
        print("\nReferences found:", result["references"])
        if result["theological_terms"]:
            print("\nTheological terms:", result["theological_terms"])
        
        # Print verification details
        print("\nVerification:")
        print("  Consistent with DB:", result["verification"]["is_consistent"])
        if result["verification"]["explanation"]:
            print("  Explanation:", result["verification"]["explanation"])
    else:
        print("No question provided. Use --question to ask a Bible question.")

if __name__ == "__main__":
    main() 