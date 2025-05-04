#!/usr/bin/env python3
"""
Test script to verify the external resources API implementation.
"""

import sys
import logging

# Set up logging to print to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Print directly to ensure output
print("Starting external resources API test...")

# Add the current directory to the path
sys.path.append('.')

try:
    # Import the external resources blueprint
    from api.external_resources_api import external_resources_bp
    print("Successfully imported external_resources_bp")
    
    # Try to import specific functions
    print("\nChecking API functions:")
    for function_name in dir(external_resources_bp):
        if not function_name.startswith('_'):  # Skip private attributes
            print(f"  - {function_name}")
    
    # Print the content of the cache
    from flask import Flask
    
    # Create a test Flask app and register the blueprint
    app = Flask(__name__)
    app.register_blueprint(external_resources_bp)
    print("\nSuccessfully registered external_resources_bp with Flask app")
    
    # Get the list of routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule.rule}")
    
    print("\nAvailable routes:")
    for route in routes:
        print(f"  - {route}")
    
    print("\nExternal resources routes:")
    found_routes = False
    for route in routes:
        if 'external_resources' in route:
            print(f"  - {route}")
            found_routes = True
    
    if not found_routes:
        print("  No external resources routes found")
    
    print("\nExternal resources API test completed successfully!")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 