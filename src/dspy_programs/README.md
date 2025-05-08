---
title: DSPy Programs
description: Python modules implementing DSPy programs for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../../README_DSPY.md
  - ../../README_DSPY_SEMANTIC_SEARCH.md
  - ../../docs/features/dspy_usage.md
  - ../../docs/guides/dspy_training_guide.md
---
# DSPy Programs

This directory contains Python modules implementing DSPy programs for the BibleScholarProject.

## Overview

DSPy is a framework for programming with foundation models. These modules implement:

1. Bible question-answering programs
2. Semantic search programs
3. DSPy training and optimization pipelines
4. Integration with Bible data sources

## Module Structure

- **`bible_qa.py`**: Core Bible question-answering DSPy program
- **`semantic_search.py`**: Vector-based semantic search DSPy program
- **`dspy_optimizers.py`**: Custom optimizers for BibleScholarProject
- **`training_utilities.py`**: Utilities for training and evaluation

## Usage

These programs are used by other components in the system, particularly:

1. Bible QA API endpoints
2. Command-line training utilities
3. Semantic search interfaces

## Cross-References
- [DSPy Documentation](../../README_DSPY.md)
- [DSPy Semantic Search](../../README_DSPY_SEMANTIC_SEARCH.md)
- [DSPy Usage Guide](../../docs/features/dspy_usage.md)
- [DSPy Training Guide](../../docs/guides/dspy_training_guide.md) 