# Pandas DataFrame Handling Guidelines

## Overview

This document provides guidelines for using pandas DataFrames in the BibleScholarProject. Following these standards ensures consistent data handling and helps prevent common issues.

## Type Enforcement

### Always Enforce Explicit Types

Always enforce specific data types for DataFrame columns:

```python
df = df.astype({
    'strongs_id': 'str', 
    'verse_id': 'int',
    'position': 'int',
    'word': 'str',
    'chapter_num': 'int',
    'verse_num': 'int'
})
```

### Type Guidelines by Column Type

- **ID Columns**: Always use `int` for numeric IDs
- **Text Fields**: Always use `str` for text, never `object`
- **Flags**: Use `bool` for boolean flags
- **Dates**: Use `datetime64[ns]` for date fields
- **Floating Point**: Use `float` for numeric values that require decimals
- **Categorical**: Use `category` for fields with limited distinct values

### Type Validation Before Database Operations

Before inserting DataFrame data into the database, always validate types:

```python
def validate_df_types(df, expected_types):
    """Validate DataFrame column types against expected types."""
    for col, expected_type in expected_types.items():
        if col not in df.columns:
            raise ValueError(f"Missing expected column: {col}")
        
        if df[col].dtype != expected_type:
            raise TypeError(f"Column {col} has type {df[col].dtype}, expected {expected_type}")
    
    return True

# Before database insertion
validate_df_types(words_df, {
    'verse_id': 'int64',
    'strongs_id': 'str',
    'word': 'str'
})
```

## Null Handling

### Always Handle NULL/NaN Values Explicitly

Always check for and handle NULL/NaN values explicitly:

```python
# Replace NaN with None for database compatibility
df = df.where(pd.notnull(df), None)

# Or for specific columns
df['strongs_id'] = df['strongs_id'].fillna('')
```

### Database Compatibility

1. Replace pandas `NaN` with Python `None` for database operations:
   ```python
   # Convert NaN to None for database compatibility
   df = df.replace({np.nan: None})
   ```

2. For string columns, decide between empty string and NULL:
   ```python
   # Use empty string for optional text
   df['notes'] = df['notes'].fillna('')
   
   # Use None for truly absent values
   df['reference_id'] = df['reference_id'].replace({np.nan: None})
   ```

3. Document the NULL handling approach for each DataFrame:
   ```python
   # NULL handling for hebrew_words DataFrame:
   # - strongs_id: None if truly missing
   # - grammar_code: Empty string if missing
   # - word: Cannot be NULL
   ```

## Performance Optimization

### Memory Efficiency

For large DataFrames, use memory-efficient types:

```python
# Use categories for columns with limited distinct values
df['book_name'] = df['book_name'].astype('category')
df['strongs_id'] = df['strongs_id'].astype('category')

# Use smaller integer types when possible
df['position'] = df['position'].astype('int16')
```

### Batch Processing

Process large datasets in batches:

```python
def process_in_batches(df, batch_size=10000):
    """Process a DataFrame in batches to avoid memory issues."""
    results = []
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].copy()
        
        # Process batch
        processed_batch = process_batch(batch)
        
        # Append results
        results.append(processed_batch)
    
    # Combine results
    return pd.concat(results, ignore_index=True)
```

## Data Validation

### Required Validation Checks

Implement these validation checks for all DataFrames:

1. **Schema Validation**:
   ```python
   required_columns = ['verse_id', 'word', 'strongs_id', 'position']
   missing_columns = [col for col in required_columns if col not in df.columns]
   if missing_columns:
       raise ValueError(f"Missing required columns: {missing_columns}")
   ```

2. **Range Validation**:
   ```python
   # Validate numeric ranges
   invalid_positions = df[~df['position'].between(1, 500)]
   if not invalid_positions.empty:
       raise ValueError(f"Found {len(invalid_positions)} records with invalid positions")
   ```

3. **Uniqueness Validation**:
   ```python
   # Check for duplicate keys
   duplicates = df[df.duplicated(['verse_id', 'position'], keep=False)]
   if not duplicates.empty:
       raise ValueError(f"Found {len(duplicates)} duplicate records")
   ```

### Data Quality Logging

Always log data quality metrics:

```python
def log_dataframe_stats(df, name):
    """Log key statistics about a DataFrame."""
    logger.info(f"DataFrame {name}: {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"Column dtypes: {df.dtypes}")
    
    # Missing value stats
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if not missing_cols.empty:
        logger.info(f"Missing values: {missing_cols}")
    
    # Sample data
    if len(df) > 0:
        logger.debug(f"Sample data: {df.head(2)}")
```

## Update History

- **2025-05-05**: Added batch processing guidelines
- **2025-04-10**: Added memory optimization techniques
- **2025-03-01**: Added data validation requirements
- **2025-02-01**: Initial version created 