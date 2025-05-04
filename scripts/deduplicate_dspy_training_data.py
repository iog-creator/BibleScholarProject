#!/usr/bin/env python3
"""
Deduplicate DSPy training data files by (context, labels) pair.
"""
import os
import json
import glob

DATA_DIR = 'data/processed/dspy_training_data/'

def deduplicate_file(file_path):
    seen = set()
    deduped_lines = []
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                key = (obj.get('context'), json.dumps(obj.get('labels', None), sort_keys=True))
                if key not in seen:
                    seen.add(key)
                    deduped_lines.append(line.rstrip())
            except Exception:
                continue
    with open(file_path, 'w', encoding='utf-8') as f:
        for l in deduped_lines:
            f.write(l + '\n')
    return len(deduped_lines)

def main():
    files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))
    for file_path in files:
        before = sum(1 for _ in open(file_path, encoding='utf-8'))
        after = deduplicate_file(file_path)
        print(f"{file_path}: {before} -> {after} unique examples")

if __name__ == '__main__':
    main() 