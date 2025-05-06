#!/usr/bin/env python3
"""
DSPy Training Data Refresh Utility

This script provides a command-line interface for managing DSPy training data collection:
1. Check current status (database hash, last collection date)
2. Force regeneration of all training data
3. Refresh specific dataset types

Usage:
  python scripts/refresh_dspy_data.py status  # Check current status
  python scripts/refresh_dspy_data.py refresh # Force refresh of all data
  python scripts/refresh_dspy_data.py refresh --type qa,theological # Refresh specific types
"""

import os
import sys
import json
import argparse
import psycopg2
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils import dspy_collector

def get_connection():
    """Get database connection."""
    try:
        # Try to use the project's connection utility
        try:
            from src.database.connection import get_connection
            return get_connection()
        except ImportError:
            pass
        
        # Fall back to manual connection
        return psycopg2.connect(
            dbname="bible_db",
            user="postgres",
            password="postgres",
            host="localhost"
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def check_status():
    """Check current DSPy data status."""
    try:
        # Get state file info
        state_hash, state_data = dspy_collector.load_state()
        
        if state_hash is None:
            print("No DSPy state file found. Training data has not been generated yet.")
            return
        
        # Load the state file directly to get more info
        with open(dspy_collector.STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            state_info = json.load(f)
        
        last_updated = datetime.fromisoformat(state_info.get("last_updated", ""))
        
        print("\nDSPy Training Data Status")
        print("========================")
        print(f"Last updated: {last_updated}")
        print(f"Database state hash: {state_hash}")
        
        # Check existing data files
        data_dir = dspy_collector.OUTPUT_DIR
        print("\nData Files:")
        for file in data_dir.glob("*.jsonl"):
            size = file.stat().st_size / 1024  # KB
            print(f"  - {file.name}: {size:.1f} KB")
        
        # Show translation statistics
        if state_data and "translation_counts" in state_data:
            print("\nTranslation Counts:")
            for trans, count in state_data["translation_counts"]:
                print(f"  - {trans}: {count} verses")
        
        # Show theological term counts
        if state_data and "theological_counts" in state_data:
            print("\nTheological Term Counts:")
            critical_terms = {
                "H430": "Elohim",
                "H3068": "YHWH",
                "H113": "Adon",
                "H2617": "Chesed",
                "H539": "Aman"
            }
            for term_id, count in state_data["theological_counts"]:
                term_name = critical_terms.get(term_id, term_id)
                print(f"  - {term_name} ({term_id}): {count} occurrences")
                
    except Exception as e:
        print(f"Error checking status: {e}")
        sys.exit(1)

def check_database_status():
    """Check database status and return connection."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'bible'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'verses' not in tables:
            print("Error: 'bible.verses' table not found. Database may not be set up correctly.")
            sys.exit(1)
        
        # Check verse counts
        cursor.execute("""
            SELECT translation_source, COUNT(*) 
            FROM bible.verses 
            GROUP BY translation_source
        """)
        
        translations = cursor.fetchall()
        
        if not translations:
            print("Warning: No Bible translations found in the database.")
        
        return conn
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def refresh_data(specific_types=None):
    """Force refresh of DSPy training data."""
    print("Refreshing DSPy training data...")
    
    # Check database status
    conn = check_database_status()
    
    # Force regeneration
    result = dspy_collector.force_regeneration(conn)
    
    if result:
        print("DSPy training data successfully refreshed!")
    else:
        print("Error refreshing DSPy training data.")
        
    conn.close()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="DSPy Training Data Management Utility")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check current DSPy data status")
    
    # Refresh command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh DSPy training data")
    refresh_parser.add_argument("--type", type=str, help="Specific data types to refresh (comma-separated)")
    
    args = parser.parse_args()
    
    # Default to status if no command provided
    if not args.command:
        args.command = "status"
    
    # Execute the appropriate command
    if args.command == "status":
        check_status()
    elif args.command == "refresh":
        specific_types = args.type.split(",") if args.type else None
        refresh_data(specific_types)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 