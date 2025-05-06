#!/usr/bin/env python
"""
Test script for Bible QA API
"""
import requests
import json
import sys
import argparse

def test_api(context, question, url="http://localhost:5005/qa"):
    """Test the Bible QA API with a context and question."""
    # Create the request payload
    payload = {
        "context": context,
        "question": question
    }
    
    # Send the request
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            print("\nAPI Response:")
            print(json.dumps(data, indent=2))
            
            # Extract and display the answer
            if "result" in data and "answer" in data["result"]:
                print("\n🤖 Answer:", data["result"]["answer"])
            else:
                print("\nError: No answer found in the response.")
        else:
            print(f"\nError: API returned status code {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the Bible QA API")
    parser.add_argument("--context", "-c", default="In the beginning God created the heavens and the earth.",
                        help="Biblical context or verse")
    parser.add_argument("--question", "-q", default="Who created the heavens and the earth?",
                        help="Question about the context")
    parser.add_argument("--url", "-u", default="http://localhost:5005/qa",
                        help="URL of the QA API endpoint")
    
    args = parser.parse_args()
    
    # Test the API
    test_api(args.context, args.question, args.url) 