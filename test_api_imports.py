<<<<<<< HEAD
#!/usr/bin/env python3
"""
Test script to verify that all API modules can be imported correctly.
Run this after fixing import statements with fix_imports.py.
"""

import os
import sys
import importlib

def test_api_imports():
    """Test if API modules can be imported correctly."""
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    
    # Make sure the current directory is in the Python path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        print(f"Added current directory to sys.path: {os.getcwd()}")
    
    # API modules to test
    api_modules = [
        'src.api.proper_names_api',
        'src.api.morphology_api',
        'src.api.tagged_text_api',
        'src.api.lexicon_api',
        'src.api.external_resources_api'
    ]
    
    # Helper utility modules they depend on
    utility_modules = [
        'src.utils.db_utils',
        'src.database.connection'
    ]
    
    # Test utility modules first
    print("\n== Testing Utility Module Imports ==")
    for module_name in utility_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            if hasattr(module, '__file__'):
                print(f"  Path: {module.__file__}")
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    # Test API modules
    print("\n== Testing API Module Imports ==")
    success_count = 0
    for module_name in api_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            if hasattr(module, '__file__'):
                print(f"  Path: {module.__file__}")
            
            # Get the content of each module's attributes
            print(f"  Blueprint name: {getattr(module, module_name.split('.')[-1], None)}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    print(f"\nSuccessfully imported {success_count} of {len(api_modules)} API modules")
    
    # Test a complete API route chain (if imports were successful)
    if success_count > 0:
        print("\n== Testing complete API import chain ==")
        try:
            from src.api.proper_names_api import proper_names_api
            print("✓ Successfully imported proper_names_api blueprint")
        except Exception as e:
            print(f"✗ Failed to import proper_names_api blueprint")
            print(f"  Error: {e}")

if __name__ == "__main__":
=======
#!/usr/bin/env python3
"""
Test script to verify that all API modules can be imported correctly.
Run this after fixing import statements with fix_imports.py.
"""

import os
import sys
import importlib

def test_api_imports():
    """Test if API modules can be imported correctly."""
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    
    # Make sure the current directory is in the Python path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        print(f"Added current directory to sys.path: {os.getcwd()}")
    
    # API modules to test
    api_modules = [
        'src.api.proper_names_api',
        'src.api.morphology_api',
        'src.api.tagged_text_api',
        'src.api.lexicon_api',
        'src.api.external_resources_api'
    ]
    
    # Helper utility modules they depend on
    utility_modules = [
        'src.utils.db_utils',
        'src.database.connection'
    ]
    
    # Test utility modules first
    print("\n== Testing Utility Module Imports ==")
    for module_name in utility_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            if hasattr(module, '__file__'):
                print(f"  Path: {module.__file__}")
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    # Test API modules
    print("\n== Testing API Module Imports ==")
    success_count = 0
    for module_name in api_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            if hasattr(module, '__file__'):
                print(f"  Path: {module.__file__}")
            
            # Get the content of each module's attributes
            print(f"  Blueprint name: {getattr(module, module_name.split('.')[-1], None)}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    print(f"\nSuccessfully imported {success_count} of {len(api_modules)} API modules")
    
    # Test a complete API route chain (if imports were successful)
    if success_count > 0:
        print("\n== Testing complete API import chain ==")
        try:
            from src.api.proper_names_api import proper_names_api
            print("✓ Successfully imported proper_names_api blueprint")
        except Exception as e:
            print(f"✗ Failed to import proper_names_api blueprint")
            print(f"  Error: {e}")

if __name__ == "__main__":
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
    test_api_imports() 