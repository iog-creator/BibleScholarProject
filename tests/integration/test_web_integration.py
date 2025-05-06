#!/usr/bin/env python
"""
Integration test script specifically for testing BibleScholarProject web pages.
This script tests the web interface functionality and integration with the API.
"""

import requests
import sys
import time
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# Configuration
WEB_PORT = 5001
HOST = 'localhost'
WEB_URL = f'http://{HOST}:{WEB_PORT}'
API_URL = f'http://{HOST}:5000'
WEB_TIMEOUT = 10  # Web timeout in seconds

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

def test_web_health():
    """Test the web app health endpoint."""
    print_heading("Testing Web App Health Endpoint")
    try:
        response = requests.get(f"{WEB_URL}/health", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            print_success(f"Web app health endpoint is working")
            return True
        else:
            print_failure(f"Web app health endpoint returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to connect to web app: {e}")
        return False

def test_home_page():
    """Test the home page."""
    print_heading("Testing Home Page")
    test_results = []
    
    try:
        response = requests.get(f"{WEB_URL}/", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for basic elements on the home page
            title = soup.title.string if soup.title else None
            if title and "Bible Scholar" in title:
                print_success(f"Home page has correct title: {title}")
                test_results.append(True)
            else:
                print_failure(f"Home page has incorrect or missing title")
                test_results.append(False)
            
            # Check for statistics section
            stats_section = soup.find(id="stats") or soup.find(class_="stats")
            if stats_section:
                print_success("Home page has statistics section")
                test_results.append(True)
            else:
                print_failure("Home page is missing statistics section")
                test_results.append(False)
            
            # Check for navigation links
            nav = soup.find('nav')
            if nav and nav.find_all('a'):
                print_success(f"Home page has navigation with {len(nav.find_all('a'))} links")
                test_results.append(True)
            else:
                print_failure("Home page is missing navigation or links")
                test_results.append(False)
        else:
            print_failure(f"Home page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test home page: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_search_page():
    """Test the search page functionality."""
    print_heading("Testing Search Page")
    test_results = []
    
    # Test empty search page load
    try:
        response = requests.get(f"{WEB_URL}/search", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for search form
            search_form = soup.find('form')
            if search_form and search_form.find('input', {'name': 'q'}):
                print_success("Search page has search form")
                test_results.append(True)
            else:
                print_failure("Search page is missing search form")
                test_results.append(False)
            
            # Check for search type options
            search_types = soup.find_all('input', {'name': 'type'})
            if search_types and len(search_types) >= 3:  # At least lexicon, verse, and name search types
                print_success(f"Search page has {len(search_types)} search type options")
                test_results.append(True)
            else:
                print_failure("Search page is missing search type options")
                test_results.append(False)
        else:
            print_failure(f"Search page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test search page load: {e}")
        test_results.append(False)
    
    # Test lexicon search
    try:
        response = requests.get(
            f"{WEB_URL}/search", 
            params={'q': 'love', 'type': 'lexicon'},
            timeout=WEB_TIMEOUT
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for search results
            results = soup.find_all(class_="result") or soup.find_all(class_="search-result")
            if results and len(results) > 0:
                print_success(f"Lexicon search returned {len(results)} visible results")
                test_results.append(True)
            else:
                print_failure("Lexicon search returned no visible results")
                test_results.append(False)
        else:
            print_failure(f"Lexicon search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test lexicon search: {e}")
        test_results.append(False)
    
    # Test verse search
    try:
        response = requests.get(
            f"{WEB_URL}/search", 
            params={'q': 'love', 'type': 'verse'},
            timeout=WEB_TIMEOUT
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for search results
            results = soup.find_all(class_="result") or soup.find_all(class_="search-result")
            if results and len(results) > 0:
                print_success(f"Verse search returned {len(results)} visible results")
                test_results.append(True)
            else:
                print_failure("Verse search returned no visible results")
                test_results.append(False)
        else:
            print_failure(f"Verse search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test verse search: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_lexicon_pages():
    """Test the lexicon entry pages."""
    print_heading("Testing Lexicon Pages")
    test_results = []
    
    # Test Hebrew lexicon entry
    try:
        response = requests.get(f"{WEB_URL}/lexicon/hebrew/H7225", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for lexicon entry content
            strongs_id = soup.find(string="H7225") or soup.find(string=lambda t: "H7225" in t)
            if strongs_id:
                print_success("Hebrew lexicon entry has correct Strong's ID")
                test_results.append(True)
            else:
                print_failure("Hebrew lexicon entry is missing Strong's ID")
                test_results.append(False)
            
            # Check for transliteration and gloss
            transliteration = soup.find(class_="transliteration") or soup.find(string=lambda t: "reshiyth" in t.lower() if t else False)
            if transliteration:
                print_success("Hebrew lexicon entry has transliteration")
                test_results.append(True)
            else:
                print_failure("Hebrew lexicon entry is missing transliteration")
                test_results.append(False)
        else:
            print_failure(f"Hebrew lexicon entry returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew lexicon entry: {e}")
        test_results.append(False)
    
    # Test Greek lexicon entry
    try:
        response = requests.get(f"{WEB_URL}/lexicon/greek/G25", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for lexicon entry content
            strongs_id = soup.find(string="G25") or soup.find(string=lambda t: "G25" in t)
            if strongs_id:
                print_success("Greek lexicon entry has correct Strong's ID")
                test_results.append(True)
            else:
                print_failure("Greek lexicon entry is missing Strong's ID")
                test_results.append(False)
            
            # Check for transliteration and gloss
            transliteration = soup.find(class_="transliteration") or soup.find(string=lambda t: "agapao" in t.lower() if t else False)
            if transliteration:
                print_success("Greek lexicon entry has transliteration")
                test_results.append(True)
            else:
                print_failure("Greek lexicon entry is missing transliteration")
                test_results.append(False)
        else:
            print_failure(f"Greek lexicon entry returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Greek lexicon entry: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_bible_pages():
    """Test the Bible verse pages."""
    print_heading("Testing Bible Verse Pages")
    test_results = []
    
    # Test KJV verse page
    try:
        response = requests.get(f"{WEB_URL}/bible/John/3/16", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for verse text
            verse_text = soup.find(class_="verse-text") or soup.find(id="verse-text")
            if verse_text and "God" in verse_text.text and "loved" in verse_text.text:
                print_success("KJV verse page has verse text")
                test_results.append(True)
            else:
                print_failure("KJV verse page is missing verse text or has incorrect content")
                test_results.append(False)
            
            # Check for verse reference
            reference = soup.find(class_="reference") or soup.find(string=lambda t: "John 3:16" in t if t else False)
            if reference:
                print_success("KJV verse page has verse reference")
                test_results.append(True)
            else:
                print_failure("KJV verse page is missing verse reference")
                test_results.append(False)
        else:
            print_failure(f"KJV verse page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test KJV verse page: {e}")
        test_results.append(False)
    
    # Test verse navigation
    try:
        response = requests.get(f"{WEB_URL}/bible/John/3/16", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for navigation links (previous, next verse)
            prev_verse = soup.find('a', string=lambda t: "Previous" in t if t else False) or soup.find('a', title=lambda t: "Previous" in t if t else False)
            next_verse = soup.find('a', string=lambda t: "Next" in t if t else False) or soup.find('a', title=lambda t: "Next" in t if t else False)
            
            if prev_verse and next_verse:
                print_success("Verse page has navigation links")
                test_results.append(True)
            else:
                print_failure("Verse page is missing navigation links")
                test_results.append(False)
        else:
            print_failure(f"Verse navigation check returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test verse navigation: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_morphology_pages():
    """Test the morphology pages."""
    print_heading("Testing Morphology Pages")
    test_results = []
    
    # Test morphology home page
    try:
        response = requests.get(f"{WEB_URL}/morphology", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for morphology content
            heading = soup.find('h1') or soup.find('h2')
            if heading and "Morphology" in heading.text:
                print_success("Morphology home page has correct heading")
                test_results.append(True)
            else:
                print_failure("Morphology home page is missing heading")
                test_results.append(False)
            
            # Check for links to Hebrew and Greek morphology
            hebrew_link = soup.find('a', href=lambda h: "/morphology/hebrew" in h if h else False)
            greek_link = soup.find('a', href=lambda h: "/morphology/greek" in h if h else False)
            
            if hebrew_link and greek_link:
                print_success("Morphology home page has links to Hebrew and Greek morphology")
                test_results.append(True)
            else:
                print_failure("Morphology home page is missing language links")
                test_results.append(False)
        else:
            print_failure(f"Morphology home page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test morphology home page: {e}")
        test_results.append(False)
    
    # Test Hebrew morphology code page
    try:
        response = requests.get(f"{WEB_URL}/morphology/hebrew/Ncmsc", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for morphology code
            code = soup.find(string="Ncmsc") or soup.find(string=lambda t: "Ncmsc" in t if t else False)
            if code:
                print_success("Hebrew morphology code page has correct code")
                test_results.append(True)
            else:
                print_failure("Hebrew morphology code page is missing code")
                test_results.append(False)
            
            # Check for description
            description = soup.find(class_="description") or soup.find(id="description")
            if description:
                print_success("Hebrew morphology code page has description")
                test_results.append(True)
            else:
                print_failure("Hebrew morphology code page is missing description")
                test_results.append(False)
        else:
            print_failure(f"Hebrew morphology code page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test Hebrew morphology code page: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_proper_names_pages():
    """Test the proper names pages."""
    print_heading("Testing Proper Names Pages")
    test_results = []
    
    # Test proper names home page
    try:
        response = requests.get(f"{WEB_URL}/names", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for proper names content
            heading = soup.find('h1') or soup.find('h2')
            if heading and "Names" in heading.text:
                print_success("Proper names home page has correct heading")
                test_results.append(True)
            else:
                print_failure("Proper names home page is missing heading")
                test_results.append(False)
            
            # Check for search form
            search_form = soup.find('form')
            if search_form and search_form.find('input', {'name': 'q'}):
                print_success("Proper names home page has search form")
                test_results.append(True)
            else:
                print_failure("Proper names home page is missing search form")
                test_results.append(False)
        else:
            print_failure(f"Proper names home page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test proper names home page: {e}")
        test_results.append(False)
    
    # Test proper names search
    try:
        response = requests.get(
            f"{WEB_URL}/names/search", 
            params={'q': 'David', 'type': 'name'},
            timeout=WEB_TIMEOUT
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for search results
            results = soup.find_all(class_="result") or soup.find_all(class_="search-result")
            if results and len(results) > 0:
                print_success(f"Proper names search returned {len(results)} visible results")
                test_results.append(True)
            else:
                print_failure("Proper names search returned no visible results")
                test_results.append(False)
            
            # Check for David in results
            david_result = soup.find(string=lambda t: "David" in t if t else False)
            if david_result:
                print_success("Proper names search has result containing 'David'")
                test_results.append(True)
            else:
                print_failure("Proper names search is missing result for 'David'")
                test_results.append(False)
        else:
            print_failure(f"Proper names search returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test proper names search: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_theological_reports_page():
    """Test the theological reports page."""
    print_heading("Testing Theological Reports Page")
    test_results = []
    
    try:
        response = requests.get(f"{WEB_URL}/theological_terms_report", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for theological terms content
            heading = soup.find('h1') or soup.find('h2')
            if heading and "Theological Terms" in heading.text:
                print_success("Theological terms report page has correct heading")
                test_results.append(True)
            else:
                print_failure("Theological terms report page is missing heading")
                test_results.append(False)
            
            # Check for table of results
            table = soup.find('table')
            if table and table.find_all('tr'):
                print_success(f"Theological terms report page has table with {len(table.find_all('tr')) - 1} terms")
                test_results.append(True)
            else:
                print_failure("Theological terms report page is missing table or has no rows")
                test_results.append(False)
        else:
            print_failure(f"Theological terms report page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test theological terms report page: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_cross_language_page():
    """Test the cross-language page."""
    print_heading("Testing Cross-Language Page")
    test_results = []
    
    try:
        response = requests.get(f"{WEB_URL}/cross_language", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for cross-language content
            heading = soup.find('h1') or soup.find('h2')
            if heading and "Cross-Language" in heading.text:
                print_success("Cross-language page has correct heading")
                test_results.append(True)
            else:
                print_failure("Cross-language page is missing heading")
                test_results.append(False)
            
            # Check for table of mappings
            table = soup.find('table')
            if table and table.find_all('tr'):
                print_success(f"Cross-language page has table with {len(table.find_all('tr')) - 1} mappings")
                test_results.append(True)
            else:
                print_failure("Cross-language page is missing table or has no rows")
                test_results.append(False)
        else:
            print_failure(f"Cross-language page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test cross-language page: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_verse_resources_page():
    """Test the verse resources page."""
    print_heading("Testing Verse Resources Page")
    test_results = []
    
    try:
        response = requests.get(f"{WEB_URL}/verse-resources/John/3/16", timeout=WEB_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for verse text
            verse_text = soup.find(class_="verse-text") or soup.find(id="verse-text")
            if verse_text and "God" in verse_text.text and "loved" in verse_text.text:
                print_success("Verse resources page has verse text")
                test_results.append(True)
            else:
                print_failure("Verse resources page is missing verse text or has incorrect content")
                test_results.append(False)
            
            # Check for resources section
            resources = soup.find(id="resources") or soup.find(class_="resources")
            if resources:
                print_success("Verse resources page has resources section")
                test_results.append(True)
            else:
                print_failure("Verse resources page is missing resources section")
                test_results.append(False)
        else:
            print_failure(f"Verse resources page returned status code {response.status_code}")
            test_results.append(False)
    except requests.exceptions.RequestException as e:
        print_failure(f"Failed to test verse resources page: {e}")
        test_results.append(False)
    
    return all(test_results)

def run_all_web_tests():
    """Run all web page integration tests."""
    print_heading("Running All Web Page Integration Tests")
    
    # Check if web app is running
    web_health = test_web_health()
    if not web_health:
        print_failure("Web app is not running. Aborting tests.")
        return False
    
    # Run all the tests
    results = {
        "Web Health": web_health,
        "Home Page": test_home_page(),
        "Search Page": test_search_page(),
        "Lexicon Pages": test_lexicon_pages(),
        "Bible Pages": test_bible_pages(),
        "Morphology Pages": test_morphology_pages(),
        "Proper Names Pages": test_proper_names_pages(),
        "Theological Reports Page": test_theological_reports_page(),
        "Cross-Language Page": test_cross_language_page(),
        "Verse Resources Page": test_verse_resources_page()
    }
    
    # Print summary
    print_heading("Web Test Results Summary")
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
        success = run_all_web_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 