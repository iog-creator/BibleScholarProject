#!/usr/bin/env python3
"""
Simple test script for DSPy-enhanced semantic search.

This script provides a command-line interface to quickly test
the DSPy-enhanced semantic search functionality.

Usage:
    python test_dspy_semantic_search.py "your search query" [--translation KJV] [--limit 10] [--no-dspy]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the semantic search functionality
from src.dspy_programs.semantic_search import search_verses, complex_search, EnhancedSemanticSearch

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test DSPy-enhanced semantic search for Bible verses")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--translation", "-t", type=str, default="KJV", help="Bible translation (default: KJV)")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--no-dspy", action="store_true", help="Disable DSPy enhancements")
    parser.add_argument("--complex", "-c", action="store_true", help="Perform complex search with multi-hop reasoning")
    parser.add_argument("--compare", action="store_true", help="Compare DSPy-enhanced and standard search")
    parser.add_argument("--expand", "-e", action="store_true", help="Show query expansion")
    return parser.parse_args()

def format_output(results, header=None):
    """Format search results for display."""
    if header:
        print(f"\n{header}")
        print("=" * len(header))
    
    for i, result in enumerate(results):
        print(f"\n[{i+1}] {result['reference']} ({result['translation']}) - {result['similarity']}% match")
        print(f"    {result['text']}")

def main():
    """Main function."""
    # Load environment variables
    load_dotenv('.env.dspy')
    
    # Parse command line arguments
    args = parse_args()
    
    # Print header
    print(f"\nDSPy-Enhanced Semantic Search Test")
    print(f"Query: {args.query}")
    print(f"Translation: {args.translation}")
    print(f"Limit: {args.limit}")
    print(f"DSPy enabled: {not args.no_dspy}")
    
    try:
        # Show query expansion if requested
        if args.expand:
            search = EnhancedSemanticSearch(use_dspy=not args.no_dspy)
            expanded_queries = search.expand_query(args.query)
            
            print("\nQuery Expansion:")
            print("===============")
            for i, query in enumerate(expanded_queries):
                print(f"[{i+1}] {query}")
        
        # Perform the appropriate search
        if args.compare:
            # Compare DSPy-enhanced and standard search
            dspy_results = search_verses(args.query, args.translation, args.limit, use_dspy=True)
            standard_results = search_verses(args.query, args.translation, args.limit, use_dspy=False)
            
            format_output(dspy_results, "DSPy-Enhanced Results")
            format_output(standard_results, "Standard Vector Search Results")
        
        elif args.complex:
            # Perform complex search with multi-hop reasoning
            results = complex_search(args.query, args.translation, args.limit, use_dspy=not args.no_dspy)
            
            # Display primary results
            format_output(results['primary_results'], "Primary Results")
            
            # Display related topics
            if 'related_topics' in results and results['related_topics']:
                print("\nRelated Biblical Topics:")
                print("=======================")
                for topic in results['related_topics']:
                    print(f"- {topic}")
            
            # Display topic results
            if 'topic_results' in results:
                for topic, verses in results['topic_results'].items():
                    if verses:
                        format_output(verses, f"Results for '{topic}'")
        
        else:
            # Perform standard search
            results = search_verses(args.query, args.translation, args.limit, use_dspy=not args.no_dspy)
            format_output(results, "Search Results")
        
        print("\nSearch completed successfully.")
        return 0
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 