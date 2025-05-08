#!/usr/bin/env python
"""
Script to start both the API and web servers for the BibleScholarProject.
"""

import os
import subprocess
import sys
import time
import signal
import argparse

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

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

def start_api_server(port):
    """Start the API server."""
    print_info(f"Starting API server on port {port}...")
    try:
        env = os.environ.copy()
        env["FLASK_APP"] = "src.api.lexicon_api:app"
        api_process = subprocess.Popen(
            ["python", "-m", "flask", "run", "--port", str(port)],
            env=env
        )
        time.sleep(2)  # Give the server a moment to start
        print_success(f"API server started on http://localhost:{port}")
        return api_process
    except Exception as e:
        print_failure(f"Failed to start API server: {e}")
        return None

def start_web_server(port):
    """Start the web server."""
    print_info(f"Starting web server on port {port}...")
    try:
        env = os.environ.copy()
        env["FLASK_APP"] = "src.web_app"
        web_process = subprocess.Popen(
            ["python", "-m", "flask", "run", "--port", str(port)],
            env=env
        )
        time.sleep(2)  # Give the server a moment to start
        print_success(f"Web server started on http://localhost:{port}")
        return web_process
    except Exception as e:
        print_failure(f"Failed to start web server: {e}")
        return None

def start_dspy_search_demo(port=5060):
    """Start the DSPy-enhanced semantic search demo."""
    print_info(f"Starting DSPy semantic search demo on port {port}...")
    try:
        env = os.environ.copy()
        env["DSPY_DEMO_PORT"] = str(port)
        demo_process = subprocess.Popen(
            ["python", "-m", "src.utils.dspy_search_demo"],
            env=env
        )
        time.sleep(2)  # Give the server a moment to start
        print_success(f"DSPy semantic search demo started on http://localhost:{port}")
        return demo_process
    except Exception as e:
        print_failure(f"Failed to start DSPy semantic search demo: {e}")
        return None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start API and web servers for BibleScholarProject")
    parser.add_argument("--api-port", type=int, default=5000, help="Port for the API server (default: 5000)")
    parser.add_argument("--web-port", type=int, default=5001, help="Port for the web server (default: 5001)")
    parser.add_argument("--dspy-port", type=int, default=5060, help="Port for the DSPy semantic search demo (default: 5060)")
    parser.add_argument("--api-only", action="store_true", help="Start only the API server")
    parser.add_argument("--web-only", action="store_true", help="Start only the web server")
    parser.add_argument("--dspy-only", action="store_true", help="Start only the DSPy semantic search demo")
    return parser.parse_args()

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop servers gracefully."""
    print_info("\nStopping servers...")
    for process in running_processes:
        if process:
            process.terminate()
    sys.exit(0)

def main():
    """Main function."""
    args = parse_args()
    
    global running_processes
    running_processes = []
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Determine which servers to start
    if args.api_only or args.web_only or args.dspy_only:
        start_api = args.api_only
        start_web = args.web_only
        start_dspy = args.dspy_only
    else:
        # If no specific server was requested, start all
        start_api = True
        start_web = True
        start_dspy = True
    
    # Start the servers
    if start_api:
        api_process = start_api_server(args.api_port)
        if api_process:
            running_processes.append(api_process)
        else:
            print_failure("Failed to start API server.")
            if not (start_web or start_dspy):
                return 1
    
    if start_web:
        web_process = start_web_server(args.web_port)
        if web_process:
            running_processes.append(web_process)
        else:
            print_failure("Failed to start web server.")
            if not (start_api or start_dspy) and not running_processes:
                return 1
    
    if start_dspy:
        dspy_process = start_dspy_search_demo(args.dspy_port)
        if dspy_process:
            running_processes.append(dspy_process)
        else:
            print_failure("Failed to start DSPy semantic search demo.")
            if not (start_api or start_web) and not running_processes:
                return 1
    
    if running_processes:
        # Print a summary of running servers
        print_info("\nRunning servers:")
        if start_api:
            print_info(f" - API server: http://localhost:{args.api_port}")
        if start_web:
            print_info(f" - Web server: http://localhost:{args.web_port}")
        if start_dspy:
            print_info(f" - DSPy semantic search demo: http://localhost:{args.dspy_port}")
        
        print_info("\nPress Ctrl+C to stop all servers.")
        try:
            # Wait for processes to finish
            for process in running_processes:
                process.wait()
        except KeyboardInterrupt:
            print_info("\nStopping servers...")
            for process in running_processes:
                if process:
                    process.terminate()
    else:
        print_failure("No servers were started.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_info("\nStopping servers...")
        # The signal handler should take care of cleanup
        sys.exit(0)
    except Exception as e:
        print_failure(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 