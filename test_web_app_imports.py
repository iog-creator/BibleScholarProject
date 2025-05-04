<<<<<<< HEAD
#!/usr/bin/env python3
"""
Test script to verify web application imports are working correctly.
"""

import sys
import os
import importlib

def test_web_app_imports():
    """Test if web app modules can be imported correctly."""
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    
    # Make sure the current directory is in the Python path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        print(f"Added current directory to sys.path: {os.getcwd()}")
    
    # Web app modules to test
    web_modules = [
        'src.web_app',
        'src.web_app_minimal'
    ]
    
    # Import the modules
    for module_name in web_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            
            # Check for Flask app object
            if hasattr(module, 'app'):
                print(f"  Found Flask app object: {module.app}")
            else:
                print(f"  No Flask app object found")
                
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    # Try to instantiate a Flask app from web_app
    try:
        from src.web_app import app
        print("\n✓ Successfully imported Flask app object from web_app")
        print(f"  App name: {app.name}")
        print(f"  Routes defined: {[rule.rule for rule in app.url_map.iter_rules()]}")
    except Exception as e:
        print("\n✗ Failed to import Flask app object from web_app")
        print(f"  Error: {e}")

if __name__ == "__main__":
=======
#!/usr/bin/env python3
"""
Test script to verify web application imports are working correctly.
"""

import sys
import os
import importlib

def test_web_app_imports():
    """Test if web app modules can be imported correctly."""
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    
    # Make sure the current directory is in the Python path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        print(f"Added current directory to sys.path: {os.getcwd()}")
    
    # Web app modules to test
    web_modules = [
        'src.web_app',
        'src.web_app_minimal'
    ]
    
    # Import the modules
    for module_name in web_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ Successfully imported '{module_name}'")
            
            # Check for Flask app object
            if hasattr(module, 'app'):
                print(f"  Found Flask app object: {module.app}")
            else:
                print(f"  No Flask app object found")
                
        except Exception as e:
            print(f"✗ Failed to import '{module_name}'")
            print(f"  Error: {e}")
    
    # Try to instantiate a Flask app from web_app
    try:
        from src.web_app import app
        print("\n✓ Successfully imported Flask app object from web_app")
        print(f"  App name: {app.name}")
        print(f"  Routes defined: {[rule.rule for rule in app.url_map.iter_rules()]}")
    except Exception as e:
        print("\n✗ Failed to import Flask app object from web_app")
        print(f"  Error: {e}")

if __name__ == "__main__":
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
    test_web_app_imports() 