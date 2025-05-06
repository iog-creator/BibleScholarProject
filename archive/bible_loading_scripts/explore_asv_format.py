#!/usr/bin/env python
"""
Script to explore the format of the ASV Bible JSON data.
"""

import requests
import json

# ASV Bible source URL - direct from GitHub repository
ASV_JSON_URL = "https://raw.githubusercontent.com/bibleapi/bibleapi-bibles-json/master/asv.json"

def main():
    """Explore the format of the ASV Bible JSON file."""
    print(f"Downloading ASV Bible from {ASV_JSON_URL}")
    
    try:
        response = requests.get(ASV_JSON_URL)
        response.raise_for_status()
        
        # Get the raw content
        content = response.text
        
        # Try to parse as JSON
        try:
            data = json.loads(content)
            print(f"Successfully parsed as JSON")
            
            # Analyze the data structure
            if isinstance(data, list):
                print(f"Data is a list with {len(data)} items")
                if data:
                    print(f"First item type: {type(data[0])}")
                    print(f"First item: {data[0]}")
            elif isinstance(data, dict):
                print(f"Data is a dictionary with {len(data.keys())} keys")
                print(f"Keys: {', '.join(data.keys())}")
                
                # Explore resultset if available
                if 'resultset' in data:
                    resultset = data['resultset']
                    print(f"Resultset type: {type(resultset)}")
                    
                    if isinstance(resultset, list):
                        print(f"Resultset is a list with {len(resultset)} items")
                        if resultset:
                            print(f"First resultset item type: {type(resultset[0])}")
                            print(f"First resultset item: {resultset[0]}")
                    elif isinstance(resultset, dict):
                        print(f"Resultset is a dictionary with {len(resultset.keys())} keys")
                        print(f"Resultset keys: {', '.join(resultset.keys())}")
                        
                        # Explore row if available
                        if 'row' in resultset:
                            row = resultset['row']
                            print(f"Row type: {type(row)}")
                            
                            if isinstance(row, list):
                                print(f"Row is a list with {len(row)} items")
                                if row:
                                    print(f"First row item type: {type(row[0])}")
                                    
                                    # If item is a dict, show its keys
                                    if isinstance(row[0], dict):
                                        print(f"Keys in first row item: {', '.join(row[0].keys())}")
                                        
                                        # Show a few verse examples
                                        for i in range(min(3, len(row))):
                                            print(f"\nVerse {i+1}:")
                                            for key, value in row[i].items():
                                                print(f"  {key}: {value}")
                            elif isinstance(row, dict):
                                print(f"Row is a dictionary with {len(row.keys())} keys")
                                print(f"Row keys: {', '.join(row.keys())}")
            else:
                print(f"Data is of type {type(data)}")
            
            # Count total verses
            try:
                if 'resultset' in data and 'row' in data['resultset'] and isinstance(data['resultset']['row'], list):
                    total_verses = len(data['resultset']['row'])
                    print(f"\nTotal verses in ASV Bible: {total_verses}")
                    
                    # Count verses by book
                    book_counts = {}
                    for verse in data['resultset']['row']:
                        book = verse.get('book', 'Unknown')
                        if book not in book_counts:
                            book_counts[book] = 0
                        book_counts[book] += 1
                    
                    print("\nVerses by book:")
                    for book, count in sorted(book_counts.items()):
                        print(f"  {book}: {count}")
            except Exception as e:
                print(f"Error counting verses: {e}")
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            
            # Print first part of content to see format
            print("First 200 characters of content:")
            print(content[:200])
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading ASV Bible: {e}")

if __name__ == "__main__":
    main() 