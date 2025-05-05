#!/usr/bin/env python3
"""
Script to check module imports and paths for BibleScholarProject
"""

import sys
import os
import importlib

def check_module(module_name, prefix=""):
    """Check if a module can be imported and show its path."""
    full_module_name = f"{prefix}{module_name}" if prefix else module_name
    try:
        module = importlib.import_module(full_module_name)
        print(f"✓ Successfully imported '{full_module_name}'")
        if hasattr(module, '__file__'):
            print(f"  Path: {module.__file__}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import '{full_module_name}'")
        print(f"  Error: {e}")
        return False

def main():
    """Main function to check module imports."""
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    print("\nChecking module imports:")
    
    # Check if we're in BibleScholarProject directory
    in_biblescholar = os.path.basename(os.getcwd()) == "BibleScholarProject"
    print(f"Running in BibleScholarProject directory: {in_biblescholar}")
    
    # Core modules to check
    modules_to_check = [
        'src',
        'src.utils',
        'src.database',
        'src.api',
        'src.etl',
        'src.tvtms',
        'src.utils.db_utils',
        'src.database.connection'
    ]
    
    # First check if modules are importable from parent directory
    print("\n=== Checking imports from root project ===")
    for module_name in modules_to_check:
        check_module(module_name)
        print()
    
    # Now check local imports (without prefix)
    if in_biblescholar:
        print("\n=== Checking local imports ===")
        # Add current directory to sys.path if not already there
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        
        for module_name in modules_to_check:
            check_module(module_name)
            print()
    
    print("Import check completed.")
    
    # Check API modules specifically
    print("\n=== Checking API modules ===")
    api_modules = [
        'proper_names_api',
        'morphology_api',
        'tagged_text_api'
    ]
    
    for api_module in api_modules:
        # Check if file exists in local structure
        local_path = os.path.join("src", "api", f"{api_module}.py")
        root_path = os.path.join("..", "src", "api", f"{api_module}.py")
        
        print(f"Module: {api_module}")
        print(f"  Local path exists: {os.path.exists(local_path)}")
        print(f"  Root path exists: {os.path.exists(root_path)}")
        
        # Try importing
        try:
            # Try with different approaches
            module_paths = [
                f"src.api.{api_module}",
                api_module
            ]
            
            imported = False
            for path in module_paths:
                try:
                    module = importlib.import_module(path)
                    print(f"  ✓ Successfully imported as '{path}'")
                    if hasattr(module, '__file__'):
                        print(f"    Path: {module.__file__}")
                    imported = True
                    break
                except ImportError:
                    continue
            
            if not imported:
                print(f"  ✗ Could not import {api_module} with any method")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()

if __name__ == "__main__":
    main() 