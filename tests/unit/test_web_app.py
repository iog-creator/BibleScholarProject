#!/usr/bin/env python3
"""
Test script to verify the web application integration with external resources API.
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append('.')

try:
    print("Testing web application with external resources integration...")
    
    # Try to import the web app and related modules
    from web_app import app, verse_with_resources
    from api.external_resources_api import external_resources_bp
    
    print("Successfully imported web_app and external_resources_bp")
    
    # Check that the blueprint is registered
    if external_resources_bp.name in [bp.name for bp in app.blueprints.values()]:
        print("External resources blueprint is correctly registered with the web app")
    else:
        print("ERROR: External resources blueprint is NOT registered with the web app")
        sys.exit(1)
    
    # Get the list of routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule.rule}")
    
    print("\nAvailable routes in web app:")
    for route in routes:
        if 'external_resources' in route or 'verse_with_resources' in route:
            print(f"  - {route}")
    
    # Test the verse_with_resources view function
    print("\nTesting verse_with_resources route...")
    if hasattr(sys.modules['web_app'], 'verse_with_resources'):
        print("  - verse_with_resources function exists")
        
        # Check if the route is registered
        verse_resource_routes = [rule for rule in app.url_map.iter_rules() 
                               if rule.endpoint == 'verse_with_resources']
        if verse_resource_routes:
            print(f"  - Route registered: {verse_resource_routes[0]}")
        else:
            print("  - ERROR: verse_with_resources route not found in URL map")
    else:
        print("  - ERROR: verse_with_resources function not found in web_app module")
    
    print("\nWeb app test completed successfully!")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 