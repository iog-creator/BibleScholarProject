#!/usr/bin/env python
"""
Integration test script for BibleScholarProject.
Tests the connectivity between API server and web app.
"""

import requests
import time
import sys
import subprocess
import threading
import json
import os
import signal
from datetime import datetime

# Configuration
API_PORT = 5000
WEB_PORT = 5001
HOST = 'localhost'
API_URL = f'http://{HOST}:{API_PORT}'
WEB_URL = f'http://{HOST}:{WEB_PORT}'
API_TIMEOUT = 5  # API timeout in seconds
WEB_TIMEOUT = 15  # Web timeout in seconds

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

def test_api_connection():
    """Test basic API connectivity."""
    print_heading("Testing API Server Connection")
    try:
        response = requests.get(f"{API_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print_success(f"API server is running on {API_URL}")
            return True
        else:
            print_failure(f"API server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to connect to API server: {e}")
        return False

def test_web_connection():
    """Test basic web app connectivity."""
    print_heading("Testing Web App Connection")
    try:
        response = requests.get(f"{WEB_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print_success(f"Web app is running on {WEB_URL}")
            return True
        else:
            print_failure(f"Web app returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to connect to web app: {e}")
        return False

def test_theological_terms_report():
    """Test the theological terms report endpoint."""
    print_heading("Testing Theological Terms Report")
    try:
        # Test the API endpoint
        api_response = requests.get(f"{API_URL}/api/theological_terms_report", timeout=API_TIMEOUT)
        if api_response.status_code == 200:
            data = api_response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"API theological terms report returned {len(data)} terms")
            else:
                print_failure(f"API theological terms report returned unexpected data: {data}")
                return False
        else:
            print_failure(f"API theological terms report returned status code {api_response.status_code}")
            return False

        # Test the web endpoint
        web_response = requests.get(f"{WEB_URL}/theological_terms_report", timeout=WEB_TIMEOUT)
        if web_response.status_code == 200:
            if "Theological Terms Frequency Report" in web_response.text:
                print_success("Web theological terms report page loaded successfully")
            else:
                print_failure("Web theological terms report page content is incorrect")
                return False
        else:
            print_failure(f"Web theological terms report returned status code {web_response.status_code}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test theological terms report: {e}")
        return False

def test_critical_terms_validation():
    """Test the Hebrew critical terms validation endpoint."""
    print_heading("Testing Critical Terms Validation")
    try:
        # Test the API endpoint
        api_response = requests.get(f"{API_URL}/api/lexicon/hebrew/validate_critical_terms", timeout=API_TIMEOUT)
        if api_response.status_code == 200:
            data = api_response.json()
            if isinstance(data, list) and len(data) > 0:
                print_success(f"API critical terms validation returned {len(data)} terms")
            else:
                print_failure(f"API critical terms validation returned unexpected data: {data}")
                return False
        else:
            print_failure(f"API critical terms validation returned status code {api_response.status_code}")
            return False

        # Test the web endpoint
        web_response = requests.get(f"{WEB_URL}/hebrew_terms_validation", timeout=WEB_TIMEOUT)
        if web_response.status_code == 200:
            if "Hebrew Critical Terms Validation" in web_response.text:
                print_success("Web critical terms validation page loaded successfully")
            else:
                print_failure("Web critical terms validation page content is incorrect")
                return False
        else:
            print_failure(f"Web critical terms validation returned status code {web_response.status_code}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test critical terms validation: {e}")
        return False

def test_cross_language_terms():
    """Test the cross-language term mappings endpoint."""
    print_heading("Testing Cross-Language Term Mappings")
    try:
        # Test the API endpoint
        api_response = requests.get(f"{API_URL}/api/cross_language/terms", timeout=API_TIMEOUT)
        if api_response.status_code == 200:
            data = api_response.json()
            if isinstance(data, list):
                print_success(f"API cross-language term mappings returned {len(data)} mappings")
            else:
                print_failure(f"API cross-language term mappings returned unexpected data: {data}")
                return False
        else:
            print_failure(f"API cross-language term mappings returned status code {api_response.status_code}")
            return False

        # Test the web endpoint
        web_response = requests.get(f"{WEB_URL}/cross_language", timeout=WEB_TIMEOUT)
        if web_response.status_code == 200:
            if "Cross-Language Term Mappings" in web_response.text:
                print_success("Web cross-language term mappings page loaded successfully")
            else:
                print_failure("Web cross-language term mappings page content is incorrect")
                return False
        else:
            print_failure(f"Web cross-language term mappings returned status code {web_response.status_code}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test cross-language term mappings: {e}")
        return False

def test_esv_bible_integration():
    """Test the ESV Bible integration."""
    print_heading("Testing ESV Bible Integration")
    try:
        # Test the API endpoint for ESV verse retrieval
        api_response = requests.get(f"{API_URL}/api/verses?translation=ESV&book=John&chapter=3&verse=16", timeout=API_TIMEOUT)
        if api_response.status_code == 200:
            data = api_response.json()
            if isinstance(data, dict) and 'verse_text' in data:
                print_success(f"API ESV verse retrieval successful: {data['verse_text'][:30]}...")
            else:
                print_failure(f"API ESV verse retrieval returned unexpected data: {data}")
                return False
        else:
            print_failure(f"API ESV verse retrieval returned status code {api_response.status_code}")
            return False

        # Test the API endpoint for ESV Bible statistics
        api_response = requests.get(f"{API_URL}/api/stats/bible?translation=ESV", timeout=API_TIMEOUT)
        if api_response.status_code == 200:
            data = api_response.json()
            if isinstance(data, dict) and 'verse_count' in data:
                print_success(f"API ESV statistics returned {data['verse_count']} verses")
                
                # Verify we have at least 23,000 verses (ESV should have around 31,000)
                if data['verse_count'] < 23000:
                    print_failure(f"ESV verse count seems too low: {data['verse_count']}")
                    return False
            else:
                print_failure(f"API ESV statistics returned unexpected data: {data}")
                return False
        else:
            print_failure(f"API ESV statistics returned status code {api_response.status_code}")
            return False

        # Test the web interface for ESV Bible access
        web_response = requests.get(f"{WEB_URL}/bible?translation=ESV&book=John&chapter=3", timeout=WEB_TIMEOUT)
        if web_response.status_code == 200:
            if "ESV" in web_response.text and "John 3" in web_response.text:
                print_success("Web ESV Bible access page loaded successfully")
            else:
                print_failure("Web ESV Bible access page content is incorrect")
                return False
        else:
            print_failure(f"Web ESV Bible access returned status code {web_response.status_code}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test ESV Bible integration: {e}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print_heading("Running All Integration Tests")
    
    results = {
        "api_connection": test_api_connection(),
        "web_connection": test_web_connection()
    }
    
    # Only run further tests if basic connectivity is established
    if results["api_connection"] and results["web_connection"]:
        results["theological_terms"] = test_theological_terms_report()
        results["critical_terms"] = test_critical_terms_validation()
        results["cross_language"] = test_cross_language_terms()
        results["esv_bible"] = test_esv_bible_integration()
    
    # Print summary
    print_heading("Test Results Summary")
    for test, result in results.items():
        if result:
            print_success(f"{test}: PASSED")
        else:
            print_failure(f"{test}: FAILED")
    
    # Return overall success
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 