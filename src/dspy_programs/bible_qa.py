#!/usr/bin/env python3
"""
Bible QA DSPy Module

This module provides DSPy-powered Bible question answering with:
1. Basic QA functionality
2. Enhanced semantic search capabilities
3. Theological term understanding
4. Multi-hop reasoning for complex questions

Usage:
    from src.dspy_programs.bible_qa import BibleQA, TheologicalBibleQA
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

try:
    import dspy
except ImportError:
    raise ImportError("DSPy is required. Install with: pip install dspy")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bible_qa.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Basic Bible QA signature
class BibleQASignature(dspy.Signature):
    """Answer questions about Bible passages with theological accuracy."""
    context = dspy.InputField(desc="Optional context from Bible passages")
    question = dspy.InputField(desc="A question about Bible content, history, or theology")
    answer = dspy.OutputField(desc="A comprehensive, accurate answer based on the Bible")

# Enhanced signature with conversation history
class BibleQAWithHistorySignature(dspy.Signature):
    """Answer questions about Bible passages with theological accuracy and conversation history."""
    context = dspy.InputField(desc="Optional context from Bible passages")
    question = dspy.InputField(desc="A question about Bible content, history, or theology")
    history = dspy.InputField(desc="Previous conversation turns as a list of questions and answers", default=[])
    answer = dspy.OutputField(desc="A comprehensive, accurate answer based on the Bible")

# Theological term signature
class TheologicalTermSignature(dspy.Signature):
    """Analyze theological terms with linguistic and historical context."""
    term = dspy.InputField(desc="Theological term or concept to analyze")
    language = dspy.InputField(desc="Original language (Hebrew, Greek, Aramaic, etc.)")
    strongs_id = dspy.InputField(desc="Strong's ID if applicable", default="")
    analysis = dspy.OutputField(desc="Detailed analysis of the term's meaning, usage, and theological significance")

# Multi-hop reasoning signature
class BibleMultiHopSignature(dspy.Signature):
    """Answer complex theological questions requiring multi-hop reasoning."""
    question = dspy.InputField(desc="Complex theological or biblical question")
    context = dspy.InputField(desc="Optional context from Bible passages", default="")
    reasoning_path = dspy.OutputField(desc="Step-by-step reasoning path to answer the question")
    answer = dspy.OutputField(desc="Final comprehensive answer based on reasoning")

# Basic Bible QA Module
class BibleQA(dspy.Module):
    """Basic Bible QA module."""
    
    def __init__(self):
        super().__init__()
        self.qa_predictor = dspy.Predict(BibleQASignature)
    
    def forward(self, context, question):
        """Answer a question based on context."""
        # Format the input for better performance
        formatted_question = f"Answer this Bible question: {question}"
        if context and len(context.strip()) > 0:
            formatted_context = f"Based on this context: {context}"
            return self.qa_predictor(context=formatted_context, question=formatted_question)
        else:
            return self.qa_predictor(context="", question=formatted_question)

# Enhanced Bible QA with conversation history
class BibleQAWithHistory(dspy.Module):
    """Bible QA module with conversation history support."""
    
    def __init__(self):
        super().__init__()
        self.qa_predictor = dspy.Predict(BibleQAWithHistorySignature)
    
    def forward(self, context, question, history=None):
        """
        Answer a question based on context and conversation history.
        
        Args:
            context: Bible passage context (optional)
            question: The question to answer
            history: List of (question, answer) tuples representing conversation history
        
        Returns:
            Object with answer attribute
        """
        # Format the input for better performance
        formatted_question = f"Answer this Bible question: {question}"
        formatted_context = ""
        
        if context and len(context.strip()) > 0:
            formatted_context = f"Based on this context: {context}"
        
        # Format history if provided
        if history and isinstance(history, list) and len(history) > 0:
            return self.qa_predictor(
                context=formatted_context,
                question=formatted_question,
                history=history
            )
        else:
            return self.qa_predictor(
                context=formatted_context,
                question=formatted_question,
                history=[]
            )

# Theological Term Analysis Module
class TheologicalTermAnalyzer(dspy.Module):
    """Module for analyzing theological terms."""
    
    def __init__(self):
        super().__init__()
        self.term_predictor = dspy.Predict(TheologicalTermSignature)
    
    def forward(self, term, language="", strongs_id=""):
        """
        Analyze a theological term.
        
        Args:
            term: Theological term or concept
            language: Original language (Hebrew, Greek, etc.)
            strongs_id: Strong's ID if applicable
        
        Returns:
            Object with analysis attribute
        """
        return self.term_predictor(
            term=term,
            language=language,
            strongs_id=strongs_id
        )

# Multi-hop reasoning module for complex theological questions
class TheologicalBibleQA(dspy.Module):
    """Advanced Bible QA module with multi-hop reasoning for complex theological questions."""
    
    def __init__(self):
        super().__init__()
        self.multihop_predictor = dspy.Predict(BibleMultiHopSignature)
        self.basic_qa = BibleQA()  # Fallback for simple questions
    
    def forward(self, question, context=""):
        """
        Answer complex theological questions using multi-hop reasoning.
        
        Args:
            question: Complex theological or biblical question
            context: Bible passage context (optional)
        
        Returns:
            Object with reasoning_path and answer attributes
        """
        # First determine if this is a complex question requiring multi-hop reasoning
        is_complex = self._is_complex_question(question)
        
        if is_complex:
            # Use multi-hop reasoning for complex questions
            return self.multihop_predictor(
                question=question,
                context=context
            )
        else:
            # Use basic QA for simple questions
            basic_result = self.basic_qa(context=context, question=question)
            
            # Format the result to match the multi-hop signature
            class MultiHopResult:
                def __init__(self, answer):
                    self.reasoning_path = "Question identified as straightforward, using direct answering."
                    self.answer = answer
            
            return MultiHopResult(basic_result.answer)
    
    def _is_complex_question(self, question):
        """
        Determine if a question is complex enough to require multi-hop reasoning.
        
        Args:
            question: The question to analyze
            
        Returns:
            bool: True if complex, False otherwise
        """
        # Check for markers of complex questions
        complexity_markers = [
            "how does", "compare", "relationship between", 
            "theological significance", "how do", "what are the implications",
            "interpret", "symbolism", "different views", "reconcile",
            "connection between", "how would", "why did"
        ]
        
        # Check if any markers are present
        question_lower = question.lower()
        for marker in complexity_markers:
            if marker in question_lower:
                return True
        
        # Check for presence of multiple theological terms
        theological_terms = [
            "salvation", "justification", "sanctification", "redemption",
            "atonement", "covenant", "grace", "faith", "trinity", "incarnation",
            "predestination", "election", "sin", "resurrection", "messiah",
            "prophecy", "apocalypse", "heaven", "hell", "judgment"
        ]
        
        term_count = sum(1 for term in theological_terms if term in question_lower)
        if term_count >= 2:
            return True
        
        # Check question length as a proxy for complexity
        if len(question.split()) > 15:
            return True
        
        return False

# Integrated Bible QA system with enhanced features
class IntegratedBibleQA(dspy.Module):
    """
    Integrated Bible QA system with enhanced features from the combined dataset.
    
    This module:
    1. Routes questions to specialized sub-modules based on question type
    2. Combines linguistic, theological, and historical knowledge
    3. Leverages the integrated dataset capabilities
    """
    
    def __init__(self):
        super().__init__()
        # Initialize sub-modules
        self.basic_qa = BibleQA()
        self.theological_qa = TheologicalBibleQA()
        self.term_analyzer = TheologicalTermAnalyzer()
        self.history_qa = BibleQAWithHistory()
    
    def forward(self, question, context="", history=None):
        """
        Answer a Bible-related question using the appropriate sub-module.
        
        Args:
            question: The question to answer
            context: Optional Bible passage context
            history: Optional conversation history
        
        Returns:
            Object with answer attribute (and potentially other attributes)
        """
        # Determine question type
        question_type = self._classify_question(question)
        
        # Route to appropriate sub-module
        if question_type == "theological_term":
            # Extract term information
            term, language, strongs_id = self._extract_term_info(question)
            result = self.term_analyzer(term=term, language=language, strongs_id=strongs_id)
            
            # Reformat result to standard format
            class StandardResult:
                def __init__(self, answer):
                    self.answer = answer
            
            return StandardResult(result.analysis)
        
        elif question_type == "complex_theological":
            return self.theological_qa(question=question, context=context)
        
        elif question_type == "conversational" and history:
            return self.history_qa(context=context, question=question, history=history)
        
        else:  # Basic questions
            return self.basic_qa(context=context, question=question)
    
    def _classify_question(self, question):
        """
        Classify the question type for routing.
        
        Args:
            question: The question to classify
            
        Returns:
            str: Question type
        """
        question_lower = question.lower()
        
        # Check for theological term questions
        term_patterns = [
            "meaning of", "what does", "definition of", "etymology of",
            "translate", "translation of", "hebrew word", "greek word", 
            "strong's", "strongs", "lexicon"
        ]
        
        for pattern in term_patterns:
            if pattern in question_lower:
                return "theological_term"
        
        # Check for complex theological questions
        if self.theological_qa._is_complex_question(question):
            return "complex_theological"
        
        # Check for conversational questions (requires history to use)
        conversational_markers = [
            "follow up", "related to that", "on that note", "additionally",
            "furthermore", "building on", "continuing", "earlier", "previous",
            "you mentioned", "you said", "elaborate", "expand", "tell me more"
        ]
        
        for marker in conversational_markers:
            if marker in question_lower:
                return "conversational"
        
        # Default to basic question
        return "basic"
    
    def _extract_term_info(self, question):
        """
        Extract theological term information from a question.
        
        Args:
            question: Question about a theological term
            
        Returns:
            tuple: (term, language, strongs_id)
        """
        # Default values
        term = ""
        language = ""
        strongs_id = ""
        
        question_lower = question.lower()
        
        # Try to extract term
        term_markers = ["meaning of", "definition of", "what does", "translate"]
        for marker in term_markers:
            if marker in question_lower:
                # Find the term after the marker
                pos = question_lower.find(marker) + len(marker)
                remaining = question[pos:].strip()
                
                # Extract the term
                if "mean" in remaining:
                    term = remaining.split("mean")[0].strip()
                elif "?" in remaining:
                    term = remaining.split("?")[0].strip()
                else:
                    term = remaining.strip()
                
                # Clean up the term
                term = term.strip("\"'.,;: ")
                if term.startswith("the "):
                    term = term[4:]
                break
        
        # Try to extract language
        if "hebrew" in question_lower:
            language = "Hebrew"
        elif "greek" in question_lower:
            language = "Greek"
        elif "aramaic" in question_lower:
            language = "Aramaic"
        
        # Try to extract Strong's ID
        if "strong's" in question_lower or "strongs" in question_lower:
            import re
            # Look for patterns like H1234 or G5678
            matches = re.findall(r'[HG]\d{1,4}', question)
            if matches:
                strongs_id = matches[0]
        
        return term, language, strongs_id

# Function to create a DSPy Bible QA model
def create_bible_qa_model(model_type="basic"):
    """
    Create a Bible QA model of the specified type.
    
    Args:
        model_type: Type of model (basic, history, theological, integrated)
        
    Returns:
        dspy.Module: The requested Bible QA model
    """
    if model_type == "history":
        return BibleQAWithHistory()
    elif model_type == "theological":
        return TheologicalBibleQA()
    elif model_type == "term":
        return TheologicalTermAnalyzer()
    elif model_type == "integrated":
        return IntegratedBibleQA()
    else:
        return BibleQA() 