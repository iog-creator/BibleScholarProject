#!/usr/bin/env python
"""
Integration test script specifically for testing BibleScholarProject API endpoints.
"""

import requests
import sys
import subprocess
import time
import json
import os
from datetime import datetime

# Configuration
API_PORT = 5000
HOST = 'localhost'
API_URL = f'http://{HOST}:{API_PORT}'
API_TIMEOUT = 5  # API timeout in seconds

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_heading(text):
    """Print a heading for test sections."""
    print(f"\n{YELLOW}{'=' * 80}\n{text}\n{'=' * 80}{RESET}")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_failure(text):
    """Print a failure message."""
    print(f"{RED}✗ {text}{RESET}")

def test_api_health():
    """Test the API health endpoint."""
    print_heading("Testing API Health Endpoint")
    try:
        response = requests.get(f"{API_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print_success(f"API health endpoint is working")
            return True
        else:
            print_failure(f"API health endpoint returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to connect to API server: {e}")
        return False

def test_lexicon_api():
    """Test the lexicon API endpoints."""
    print_heading("Testing Lexicon API Endpoints")
    test_results = []
    
    # Test Hebrew lexicon entry
    try:
        response = requests.get(f"{API_URL}/api/lexicon/hebrew/H7225", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if 'strongs_id' in data and data['strongs_id'] == 'H7225':
                print_success("Hebrew lexicon entry retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Hebrew lexicon entry returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Hebrew lexicon entry returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew lexicon entry: {e}")
        test_results.append(False)
    
    # Test Greek lexicon entry
    try:
        response = requests.get(f"{API_URL}/api/lexicon/greek/G25", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if 'strongs_id' in data and data['strongs_id'] == 'G25':
                print_success("Greek lexicon entry retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Greek lexicon entry returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Greek lexicon entry returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Greek lexicon entry: {e}")
        test_results.append(False)
    
    # Test lexicon search
    try:
        response = requests.get(f"{API_URL}/api/lexicon/search", params={'q': 'love'}, timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Lexicon search returned {len(data)} results")
                test_results.append(True)
            else:
                print_failure(f"Lexicon search returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Lexicon search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test lexicon search: {e}")
        test_results.append(False)
    
    # Test lexicon stats
    try:
        response = requests.get(f"{API_URL}/api/lexicon/stats", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'hebrew_lexicon' in data and 'greek_lexicon' in data:
                print_success(f"Lexicon stats retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Lexicon stats returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Lexicon stats returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test lexicon stats: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_tagged_text_api():
    """Test the tagged text API endpoints."""
    print_heading("Testing Tagged Text API Endpoints")
    test_results = []
    
    # Test verse retrieval
    try:
        response = requests.get(
            f"{API_URL}/api/verses", 
            params={'translation': 'KJV', 'book': 'John', 'chapter': 3, 'verse': 16},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if 'verse_text' in data and 'John 3:16' in data.get('reference', ''):
                print_success("Verse retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Verse retrieval returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Verse retrieval returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test verse retrieval: {e}")
        test_results.append(False)
    
    # Test tagged verse retrieval
    try:
        response = requests.get(
            f"{API_URL}/api/tagged/verses", 
            params={'translation': 'KJV', 'book': 'John', 'chapter': 3, 'verse': 16},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if 'tokens' in data and isinstance(data['tokens'], list) and len(data['tokens']) > 0:
                print_success("Tagged verse retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Tagged verse retrieval returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Tagged verse retrieval returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test tagged verse retrieval: {e}")
        test_results.append(False)
    
    # Test verse search
    try:
        response = requests.get(
            f"{API_URL}/api/verses/search", 
            params={'q': 'love', 'limit': 10},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Verse search returned {len(data)} results")
                test_results.append(True)
            else:
                print_failure(f"Verse search returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Verse search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test verse search: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_morphology_api():
    """Test the morphology API endpoints."""
    print_heading("Testing Morphology API Endpoints")
    test_results = []
    
    # Test Hebrew morphology
    try:
        response = requests.get(f"{API_URL}/api/morphology/hebrew", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Hebrew morphology retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Hebrew morphology returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Hebrew morphology returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew morphology: {e}")
        test_results.append(False)
    
    # Test Greek morphology
    try:
        response = requests.get(f"{API_URL}/api/morphology/greek", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Greek morphology retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Greek morphology returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Greek morphology returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Greek morphology: {e}")
        test_results.append(False)
    
    # Test Hebrew morphology code
    try:
        response = requests.get(f"{API_URL}/api/morphology/hebrew/Ncmsc", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'code' in data and data['code'] == 'Ncmsc':
                print_success(f"Hebrew morphology code retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Hebrew morphology code returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Hebrew morphology code returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew morphology code: {e}")
        test_results.append(False)
    
    # Test Greek morphology code
    try:
        response = requests.get(f"{API_URL}/api/morphology/greek/V-PAI-3S", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'code' in data and data['code'] == 'V-PAI-3S':
                print_success(f"Greek morphology code retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Greek morphology code returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Greek morphology code returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Greek morphology code: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_proper_names_api():
    """Test the proper names API endpoints."""
    print_heading("Testing Proper Names API Endpoints")
    test_results = []
    
    # Test proper names list
    try:
        response = requests.get(f"{API_URL}/api/names", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Proper names list retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Proper names list returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Proper names list returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test proper names list: {e}")
        test_results.append(False)
    
    # Test proper name search
    try:
        response = requests.get(
            f"{API_URL}/api/names/search", 
            params={'q': 'David', 'type': 'name'},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Proper name search returned {len(data)} results")
                test_results.append(True)
            else:
                print_failure(f"Proper name search returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Proper name search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test proper name search: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_cross_language_api():
    """Test the cross-language API endpoints."""
    print_heading("Testing Cross-Language API Endpoints")
    test_results = []
    
    # Test cross-language terms
    try:
        response = requests.get(f"{API_URL}/api/cross_language/terms", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_success(f"Cross-language terms retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Cross-language terms returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Cross-language terms returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test cross-language terms: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_external_resources_api():
    """Test the external resources API endpoints."""
    print_heading("Testing External Resources API Endpoints")
    test_results = []
    
    # Test external resources for a verse
    try:
        response = requests.get(
            f"{API_URL}/api/external_resources/verse", 
            params={'book': 'John', 'chapter': 3, 'verse': 16},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'resources' in data:
                print_success(f"External resources for verse retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"External resources for verse returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"External resources for verse returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test external resources for verse: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_theological_terms_api():
    """Test the theological terms API endpoints."""
    print_heading("Testing Theological Terms API Endpoints")
    test_results = []
    
    # Test theological terms report
    try:
        response = requests.get(f"{API_URL}/api/theological_terms_report", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Theological terms report retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Theological terms report returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Theological terms report returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test theological terms report: {e}")
        test_results.append(False)
    
    # Test Hebrew critical terms validation
    try:
        response = requests.get(f"{API_URL}/api/lexicon/hebrew/validate_critical_terms", timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Hebrew critical terms validation retrieval successful")
                test_results.append(True)
            else:
                print_failure(f"Hebrew critical terms validation returned unexpected data: {data}")
                test_results.append(False)
        else:
            print_failure(f"Hebrew critical terms validation returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew critical terms validation: {e}")
        test_results.append(False)
    
    return all(test_results)

def run_all_api_tests():
    """Run all API integration tests."""
    print_heading("Running All API Integration Tests")
    
    # Check if API is running
    api_health = test_api_health()
    if not api_health:
        print_failure("API server is not running. Aborting tests.")
        return False
    
    # Run all the tests
    results = {
        "API Health": api_health,
        "Lexicon API": test_lexicon_api(),
        "Tagged Text API": test_tagged_text_api(),
        "Morphology API": test_morphology_api(),
        "Proper Names API": test_proper_names_api(),
        "Cross-Language API": test_cross_language_api(),
        "External Resources API": test_external_resources_api(),
        "Theological Terms API": test_theological_terms_api()
    }
    
    # Print summary
    print_heading("API Test Results Summary")
    all_passed = True
    for test, result in results.items():
        if result:
            print_success(f"{test}: PASSED")
        else:
            print_failure(f"{test}: FAILED")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_api_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 