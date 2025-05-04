<<<<<<< HEAD
#!/usr/bin/env python3
"""
Script to fix import statements in API files.
This allows the files to work properly within the BibleScholarProject structure.
"""

import os
import re

def fix_imports_in_file(file_path):
    """Fix import statements in a file."""
    print(f"Fixing imports in: {file_path}")
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False
    
    # Print the first few lines of the file for debugging
    lines = content.splitlines()[:15]  # First 15 lines
    print(f"  First few lines of {file_path}:")
    for i, line in enumerate(lines):
        if 'import' in line or 'from' in line:
            print(f"    {i+1}: {line} [IMPORT]")
        else:
            print(f"    {i+1}: {line}")
    
    # Define patterns to search for and their replacements
    replacements = [
        # Fix absolute imports to be relative
        (r'from database', r'from src.database'),
        (r'from utils', r'from src.utils'),
        (r'from api', r'from src.api'),
        (r'from etl', r'from src.etl'),
        (r'from tvtms', r'from src.tvtms'),
        # Fix imports from parent directory
        (r'import database', r'import src.database'),
        (r'import utils', r'import src.utils'),
        (r'import api', r'import src.api'),
        (r'import etl', r'import src.etl'),
        (r'import tvtms', r'import src.tvtms'),
        # Fix specific db_utils import that's problematic
        (r'from src.database.db_utils', r'from src.utils.db_utils'),
        (r'from database.db_utils', r'from src.utils.db_utils')
    ]
    
    # Apply replacements
    modified_content = content
    changes = 0
    for pattern, replacement in replacements:
        # Count matches before replacement
        matches = len(re.findall(pattern, modified_content))
        if matches > 0:
            print(f"  Found {matches} instances of '{pattern}'")
            changes += matches
        
        # Apply replacement
        modified_content = re.sub(pattern, replacement, modified_content)
    
    # Check if content was modified
    if content != modified_content:
        # Write the modified content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"  ✓ Fixed {changes} imports in: {file_path}")
        except Exception as e:
            print(f"  Error writing file: {e}")
            return False
    else:
        print(f"  No changes needed in: {file_path}")
    
    return content != modified_content

def main():
    """Main function to fix imports."""
    # Files to fix
    api_files = [
        os.path.join('src', 'api', 'proper_names_api.py'),
        os.path.join('src', 'api', 'morphology_api.py'),
        os.path.join('src', 'api', 'tagged_text_api.py'),
        os.path.join('src', 'api', 'lexicon_api.py'),
        os.path.join('src', 'api', 'external_resources_api.py')
    ]
    
    # Fix imports in API files
    changes_made = 0
    files_processed = 0
    
    for file_path in api_files:
        if os.path.exists(file_path):
            files_processed += 1
            if fix_imports_in_file(file_path):
                changes_made += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nTotal files modified: {changes_made} of {files_processed} (out of {len(api_files)} total)")
    
    # Create or update __init__.py in API directory
    api_init_path = os.path.join('src', 'api', '__init__.py')
    if not os.path.exists(api_init_path) or os.path.getsize(api_init_path) == 0:
        try:
            with open(api_init_path, 'w', encoding='utf-8') as f:
                f.write('"""API module for the BibleScholarProject.\n\nThis module contains various API endpoints for accessing Bible data.\n"""\n')
            print(f"Created/Updated {api_init_path}")
        except Exception as e:
            print(f"Error creating/updating {api_init_path}: {e}")
    
    # Create or update __init__.py in utils directory if needed
    utils_init_path = os.path.join('src', 'utils', '__init__.py')
    if not os.path.exists(utils_init_path) or os.path.getsize(utils_init_path) == 0:
        try:
            with open(utils_init_path, 'w', encoding='utf-8') as f:
                f.write('"""Utility module for the BibleScholarProject.\n\nThis module contains various utility functions.\n"""\n')
            print(f"Created/Updated {utils_init_path}")
        except Exception as e:
            print(f"Error creating/updating {utils_init_path}: {e}")
    
    print("\nDone fixing imports!")

if __name__ == "__main__":
=======
#!/usr/bin/env python3
"""
Script to fix import statements in API files.
This allows the files to work properly within the BibleScholarProject structure.
"""

import os
import re

def fix_imports_in_file(file_path):
    """Fix import statements in a file."""
    print(f"Fixing imports in: {file_path}")
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False
    
    # Print the first few lines of the file for debugging
    lines = content.splitlines()[:15]  # First 15 lines
    print(f"  First few lines of {file_path}:")
    for i, line in enumerate(lines):
        if 'import' in line or 'from' in line:
            print(f"    {i+1}: {line} [IMPORT]")
        else:
            print(f"    {i+1}: {line}")
    
    # Define patterns to search for and their replacements
    replacements = [
        # Fix absolute imports to be relative
        (r'from database', r'from src.database'),
        (r'from utils', r'from src.utils'),
        (r'from api', r'from src.api'),
        (r'from etl', r'from src.etl'),
        (r'from tvtms', r'from src.tvtms'),
        # Fix imports from parent directory
        (r'import database', r'import src.database'),
        (r'import utils', r'import src.utils'),
        (r'import api', r'import src.api'),
        (r'import etl', r'import src.etl'),
        (r'import tvtms', r'import src.tvtms'),
        # Fix specific db_utils import that's problematic
        (r'from src.database.db_utils', r'from src.utils.db_utils'),
        (r'from database.db_utils', r'from src.utils.db_utils')
    ]
    
    # Apply replacements
    modified_content = content
    changes = 0
    for pattern, replacement in replacements:
        # Count matches before replacement
        matches = len(re.findall(pattern, modified_content))
        if matches > 0:
            print(f"  Found {matches} instances of '{pattern}'")
            changes += matches
        
        # Apply replacement
        modified_content = re.sub(pattern, replacement, modified_content)
    
    # Check if content was modified
    if content != modified_content:
        # Write the modified content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"  ✓ Fixed {changes} imports in: {file_path}")
        except Exception as e:
            print(f"  Error writing file: {e}")
            return False
    else:
        print(f"  No changes needed in: {file_path}")
    
    return content != modified_content

def main():
    """Main function to fix imports."""
    # Files to fix
    api_files = [
        os.path.join('src', 'api', 'proper_names_api.py'),
        os.path.join('src', 'api', 'morphology_api.py'),
        os.path.join('src', 'api', 'tagged_text_api.py'),
        os.path.join('src', 'api', 'lexicon_api.py'),
        os.path.join('src', 'api', 'external_resources_api.py')
    ]
    
    # Fix imports in API files
    changes_made = 0
    files_processed = 0
    
    for file_path in api_files:
        if os.path.exists(file_path):
            files_processed += 1
            if fix_imports_in_file(file_path):
                changes_made += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nTotal files modified: {changes_made} of {files_processed} (out of {len(api_files)} total)")
    
    # Create or update __init__.py in API directory
    api_init_path = os.path.join('src', 'api', '__init__.py')
    if not os.path.exists(api_init_path) or os.path.getsize(api_init_path) == 0:
        try:
            with open(api_init_path, 'w', encoding='utf-8') as f:
                f.write('"""API module for the BibleScholarProject.\n\nThis module contains various API endpoints for accessing Bible data.\n"""\n')
            print(f"Created/Updated {api_init_path}")
        except Exception as e:
            print(f"Error creating/updating {api_init_path}: {e}")
    
    # Create or update __init__.py in utils directory if needed
    utils_init_path = os.path.join('src', 'utils', '__init__.py')
    if not os.path.exists(utils_init_path) or os.path.getsize(utils_init_path) == 0:
        try:
            with open(utils_init_path, 'w', encoding='utf-8') as f:
                f.write('"""Utility module for the BibleScholarProject.\n\nThis module contains various utility functions.\n"""\n')
            print(f"Created/Updated {utils_init_path}")
        except Exception as e:
            print(f"Error creating/updating {utils_init_path}: {e}")
    
    print("\nDone fixing imports!")

if __name__ == "__main__":
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
    main() 