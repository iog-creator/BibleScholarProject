#!/usr/bin/env python
"""
Main test runner for BibleScholarProject integration tests.
This script runs both API and web page tests.
"""

import sys
import subprocess
import os
import signal
import time
import argparse
from datetime import datetime

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'

# Configuration
API_PORT = 5000
WEB_PORT = 5001
HOST = 'localhost'
API_URL = f'http://{HOST}:{API_PORT}'
WEB_URL = f'http://{HOST}:{WEB_PORT}'

def print_heading(text, color=YELLOW):
    """Print a heading for test sections."""
    print(f"\n{color}{'=' * 80}\n{text}\n{'=' * 80}{RESET}")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_failure(text):
    """Print a failure message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def start_api_server():
    """Start the API server."""
    print_info("Starting API server...")
    try:
        api_process = subprocess.Popen(
            ["python", "-m", "flask", "run", "--port", str(API_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "FLASK_APP": "src.api.lexicon_api"}
        )
        # Wait a moment for the server to start
        time.sleep(3)
        print_success("API server started")
        return api_process
    except Exception as e:
        print_failure(f"Failed to start API server: {e}")
        return None

def start_web_server():
    """Start the web server."""
    print_info("Starting web server...")
    try:
        web_process = subprocess.Popen(
            ["python", "-m", "flask", "run", "--port", str(WEB_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "FLASK_APP": "src.web_app"}
        )
        # Wait a moment for the server to start
        time.sleep(3)
        print_success("Web server started")
        return web_process
    except Exception as e:
        print_failure(f"Failed to start web server: {e}")
        return None

def stop_server(process, name="Server"):
    """Stop a server process."""
    if process:
        print_info(f"Stopping {name}...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print_success(f"{name} stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning(f"{name} killed")
        except Exception as e:
            print_failure(f"Error stopping {name}: {e}")

def run_api_tests():
    """Run API tests."""
    print_heading("Running API Tests", CYAN)
    try:
        result = subprocess.run(
            ["python", "tests/integration/test_api_integration.py"],
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print_failure(f"Error running API tests: {e}")
        return False

def run_web_tests():
    """Run web tests."""
    print_heading("Running Web Tests", MAGENTA)
    try:
        result = subprocess.run(
            ["python", "tests/integration/test_web_integration.py"],
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print_failure(f"Error running web tests: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run BibleScholarProject integration tests")
    parser.add_argument("--api-only", action="store_true", help="Run only API tests")
    parser.add_argument("--web-only", action="store_true", help="Run only web tests")
    parser.add_argument("--no-server", action="store_true", help="Don't start/stop servers (assume they're already running)")
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Determine which tests to run
    run_api = not args.web_only
    run_web = not args.api_only
    
    # Start servers if needed
    api_process = None
    web_process = None
    
    if not args.no_server:
        if run_api:
            api_process = start_api_server()
            if not api_process:
                print_failure("Failed to start API server. Aborting tests.")
                return 1
                
        if run_web:
            web_process = start_web_server()
            if not web_process:
                if api_process:
                    stop_server(api_process, "API server")
                print_failure("Failed to start web server. Aborting tests.")
                return 1
    
    # Track test results
    results = {}
    
    try:
        # Run tests
        if run_api:
            api_success = run_api_tests()
            results["API Tests"] = api_success
        
        if run_web:
            web_success = run_web_tests()
            results["Web Tests"] = web_success
            
        # Print summary
        print_heading("Test Results Summary")
        all_passed = True
        for test, result in results.items():
            if result:
                print_success(f"{test}: PASSED")
            else:
                print_failure(f"{test}: FAILED")
                all_passed = False
        
        # Return appropriate exit code
        return 0 if all_passed else 1
    
    finally:
        # Stop servers
        if not args.no_server:
            if web_process:
                stop_server(web_process, "Web server")
            if api_process:
                stop_server(api_process, "API server")

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 