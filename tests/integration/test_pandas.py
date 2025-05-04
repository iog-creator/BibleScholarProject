"""
Integration tests for pandas functionality in TVTMS processing.
"""

import pytest
import pandas as pd
import numpy as np
from tvtms.parser import TVTMSParser

def test_pandas_dataframe_creation(parser, sample_tvtms_file):
    """Test creation of pandas DataFrame from TVTMS file."""
    # Parse file
    mappings, rules, docs = parser.parse_file(sample_tvtms_file)
    
    # Convert mappings to DataFrame
    df = pd.DataFrame([{
        'source_tradition': m.source_tradition,
        'target_tradition': m.target_tradition,
        'source_book': m.source_book,
        'source_chapter': m.source_chapter,
        'source_verse': m.source_verse,
        'source_subverse': m.source_subverse,
        'manuscript_marker': m.manuscript_marker,
        'target_book': m.target_book,
        'target_chapter': m.target_chapter,
        'target_verse': m.target_verse,
        'target_subverse': m.target_subverse,
        'mapping_type': m.mapping_type,
        'category': m.category,
        'notes': m.notes,
        'source_range_note': m.source_range_note,
        'target_range_note': m.target_range_note
    } for m in mappings])
    
    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(col in df.columns for col in [
        'source_tradition', 'target_tradition', 'source_book', 'source_chapter',
        'source_verse', 'source_subverse', 'manuscript_marker', 'target_book',
        'target_chapter', 'target_verse', 'target_subverse', 'mapping_type',
        'category', 'notes', 'source_range_note', 'target_range_note'
    ])
    
    # Check data types
    assert df['source_chapter'].dtype in (np.int32, np.int64)
    assert df['source_verse'].dtype in (np.int32, np.int64)
    assert df['target_chapter'].dtype in (np.int32, np.int64)
    assert df['target_verse'].dtype in (np.int32, np.int64)
    assert df['source_tradition'].dtype == object
    assert df['category'].dtype == object

def test_pandas_data_filtering(parser, sample_tvtms_file):
    """Test filtering and transformation of pandas DataFrame."""
    mappings, rules, docs = parser.parse_file(sample_tvtms_file)
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'source_tradition': m.source_tradition,
        'source_book': m.source_book,
        'source_chapter': m.source_chapter,
        'source_verse': m.source_verse,
        'category': m.category
    } for m in mappings])
    
    # Filter by category
    opt_mappings = df[df['category'] == 'Opt']
    nec_mappings = df[df['category'] == 'Nec']
    
    # Verify filtering
    assert len(opt_mappings) + len(nec_mappings) <= len(df)
    assert all(m == 'Opt' for m in opt_mappings['category'])
    assert all(m == 'Nec' for m in nec_mappings['category'])

def test_pandas_groupby_operations(parser, sample_tvtms_file):
    """Test groupby operations on pandas DataFrame."""
    mappings, rules, docs = parser.parse_file(sample_tvtms_file)
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'source_tradition': m.source_tradition,
        'source_book': m.source_book,
        'mapping_type': m.mapping_type,
        'category': m.category
    } for m in mappings])
    
    # Group by tradition and category
    grouped = df.groupby(['source_tradition', 'category']).size().reset_index(name='count')
    
    # Verify grouping
    assert isinstance(grouped, pd.DataFrame)
    assert 'count' in grouped.columns
    assert grouped['count'].sum() == len(df)

def test_pandas_merge_operations(parser, sample_tvtms_file):
    """Test merging operations with pandas DataFrames."""
    mappings, rules, docs = parser.parse_file(sample_tvtms_file)
    
    # Create mappings DataFrame
    mappings_df = pd.DataFrame([{
        'source_tradition': m.source_tradition,
        'source_book': m.source_book,
        'category': m.category
    } for m in mappings])
    
    # Create rules DataFrame
    rules_df = pd.DataFrame([{
        'tradition': r.applies_to[0] if r.applies_to else None,
        'rule_type': r.rule_type,
        'content': r.content
    } for r in rules])
    
    # Merge DataFrames
    if not rules_df.empty and not mappings_df.empty:
        merged = pd.merge(
            mappings_df,
            rules_df,
            left_on='source_tradition',
            right_on='tradition',
            how='left'
        )
        
        # Verify merge
        assert len(merged) >= len(mappings_df)
        assert 'rule_type' in merged.columns
        assert 'content' in merged.columns

def test_pandas_null_handling(parser, sample_tvtms_file):
    """Test handling of null values in pandas DataFrame."""
    mappings, rules, docs = parser.parse_file(sample_tvtms_file)
    
    # Create DataFrame with potential null values
    df = pd.DataFrame([{
        'source_tradition': m.source_tradition,
        'source_subverse': m.source_subverse,
        'manuscript_marker': m.manuscript_marker,
        'target_subverse': m.target_subverse,
        'notes': m.notes
    } for m in mappings])
    
    # Replace empty strings with NaN
    df = df.replace('', np.nan)
    
    # Verify null handling
    assert df['source_subverse'].isna().any()  # Should have some null values
    assert df['manuscript_marker'].isna().any()  # Should have some null values
    
    # Fill nulls with default values
    filled_df = df.fillna({
        'source_subverse': 'none',
        'manuscript_marker': 'none',
        'target_subverse': 'none',
        'notes': ''
    })
    
    # Verify filling
    assert not filled_df.isna().any().any()  # No null values should remain 