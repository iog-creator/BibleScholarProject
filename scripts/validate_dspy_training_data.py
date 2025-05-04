#!/usr/bin/env python3
"""
Validate DSPy training data files for schema and JSON correctness.
"""
import os
import json
import glob

DATA_DIR = 'data/processed/dspy_training_data/'
REQUIRED_FIELDS = ['context', 'labels']

def validate_file(file_path):
    errors = []
    with open(file_path, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
            except Exception as e:
                errors.append(f"Line {i}: Invalid JSON: {e}")
                continue
            for field in REQUIRED_FIELDS:
                if field not in obj:
                    errors.append(f"Line {i}: Missing required field: {field}")
    return errors

def main():
    files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))
    total_errors = 0
    for file_path in files:
        errors = validate_file(file_path)
        if errors:
            print(f"Errors in {file_path}:")
            for err in errors:
                print(f"  {err}")
            total_errors += len(errors)
        else:
            print(f"{file_path}: OK")
    if total_errors == 0:
        print("All DSPy training data files are valid.")
    else:
        print(f"Total errors: {total_errors}")

if __name__ == '__main__':
    main() 