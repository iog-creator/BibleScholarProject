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
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    # Try to import, but don't fail if not available yet
    from src.utils import dspy_collector
except ImportError:
    print("Warning: dspy_collector module not found. This is expected if the system is not yet set up.")
    dspy_collector = None

def get_connection():
    """Get database connection."""
    try:
        # Try to use the project's connection utility
        try:
            from src.database.connection import get_connection
            return get_connection()
        except ImportError:
            pass
        
        # Try alternative import paths
        try:
            from src.database.db_utils import get_connection as get_db_conn
            return get_db_conn()
        except ImportError:
            pass

        # Fall back to manual connection
        try:
            import psycopg2
            return psycopg2.connect(
                dbname=os.environ.get("DB_NAME", "bible_db"),
                user=os.environ.get("DB_USER", "postgres"),
                password=os.environ.get("DB_PASSWORD", "postgres"),
                host=os.environ.get("DB_HOST", "localhost")
            )
        except:
            print("Warning: Could not connect to the database. Make sure it's running and credentials are correct.")
            return None
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_status():
    """Check current DSPy data status."""
    try:
        # Check if dspy_collector module is available
        if dspy_collector is None:
            print("DSPy collector module not available. System may not be fully set up.")
            print("Run 'make dspy-refresh' to set up the system.")
            return

        # Get state file info
        try:
            state_hash, state_data = dspy_collector.load_state()
        except Exception as e:
            print(f"Error loading state data: {e}")
            print("No DSPy state file found. Training data has not been generated yet.")
            return
        
        if state_hash is None:
            print("No DSPy state file found. Training data has not been generated yet.")
            return
        
        # Load the state file directly to get more info
        try:
            with open(dspy_collector.STATE_FILE_PATH, 'r', encoding='utf-8') as f:
                state_info = json.load(f)
            last_updated = datetime.fromisoformat(state_info.get("last_updated", ""))
        except:
            print("State file exists but couldn't be parsed. It may be corrupted.")
            return
        
        print("\nDSPy Training Data Status")
        print("========================")
        print(f"Last updated: {last_updated}")
        print(f"Database state hash: {state_hash}")
        
        # Check existing data files
        data_dir = dspy_collector.OUTPUT_DIR
        if data_dir.exists():
            print("\nData Files:")
            for file in data_dir.glob("*.jsonl"):
                size = file.stat().st_size / 1024  # KB
                print(f"  - {file.name}: {size:.1f} KB")
        else:
            print("\nNo data files found.")
        
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
        print("Stack trace:")
        traceback.print_exc()

def check_database_status():
    """Check database status and return connection."""
    try:
        conn = get_connection()
        if conn is None:
            print("Database connection not available. Please check your configuration.")
            return None
            
        cursor = conn.cursor()
        
        # Check if tables exist
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'bible'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'verses' not in tables:
                print("Warning: 'bible.verses' table not found. Database may not be set up correctly.")
                return conn
            
            # Check verse counts
            cursor.execute("""
                SELECT translation_source, COUNT(*) 
                FROM bible.verses 
                GROUP BY translation_source
            """)
            
            translations = cursor.fetchall()
            
            if not translations:
                print("Warning: No Bible translations found in the database.")
        except Exception as e:
            print(f"Error querying database: {e}")
            
        return conn
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        traceback.print_exc()
        return None

def refresh_data(specific_types=None):
    """Force refresh of DSPy training data."""
    print("Refreshing DSPy training data...")
    
    # Check if dspy_collector module is available
    if dspy_collector is None:
        print("DSPy collector module not available. Please ensure it's properly installed.")
        return False
    
    # Check database status
    conn = check_database_status()
    if conn is None:
        print("Cannot refresh data without database connection.")
        return False
    
    try:
        # Force regeneration
        result = dspy_collector.force_regeneration(conn)
        
        if result:
            print("DSPy training data successfully refreshed!")
        else:
            print("Error refreshing DSPy training data.")
        
        conn.close()
        return result
    except Exception as e:
        print(f"Error during data refresh: {e}")
        traceback.print_exc()
        if conn:
            conn.close()
        return False

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