# Parser Strictness Guidelines

## Strictness Levels

When designing ETL parsers for the BibleScholarProject, three strictness levels should be available:

1. **Strict Mode** - Used for development and initial validation:
   - Throws exceptions for any formatting issues
   - No recovery from malformed input
   - Ideal for catching issues early in the development process
   - Use with test data that should be perfect

2. **Tolerant Mode** - Default mode for production use:
   - Attempts to recover from minor formatting issues
   - Logs warnings for problematic but recoverable inputs
   - Makes reasonable assumptions about data intent
   - Preferred for most ETL processes

3. **Permissive Mode** - Use only for data recovery:
   - Accepts almost any input format
   - Makes best-effort guesses for malformed data
   - Logs errors but continues processing
   - Use only when recovering damaged or poorly formatted data

## Implementation Pattern

Each parser should implement the strictness parameter:

```python
class BibleDataParser:
    """Parser for Bible data files."""
    
    def __init__(self, strictness="tolerant"):
        """
        Initialize parser with strictness level.
        
        Args:
            strictness: One of "strict", "tolerant", or "permissive"
        """
        if strictness not in ["strict", "tolerant", "permissive"]:
            raise ValueError("Strictness must be one of: strict, tolerant, permissive")
        
        self.strictness = strictness
        
    def parse_line(self, line):
        """Parse a line of data based on strictness level."""
        try:
            # Common parsing logic
            result = self._common_parse(line)
            return result
        except Exception as e:
            if self.strictness == "strict":
                # Re-raise any exception in strict mode
                raise
            elif self.strictness == "tolerant":
                # Log warning and try recovery in tolerant mode
                logger.warning(f"Error parsing line, attempting recovery: {e}")
                return self._recover_parse(line)
            else:  # permissive
                # Log error and make best guess in permissive mode
                logger.error(f"Error parsing line, making best guess: {e}")
                return self._best_guess_parse(line)
```

## Strictness Level Usage Guidelines

### When to Use Each Level

- **Strict**: 
  - During initial development
  - When validating gold-standard data
  - In test environments for data validation
  - When creating new parsers

- **Tolerant**:
  - In production environments
  - For most ETL processes
  - When processing external data sources
  - Default mode for most operations

- **Permissive**:
  - For data recovery operations
  - When migrating legacy data
  - When dealing with potentially corrupt files
  - As a last resort when other modes fail

### Configuration

Parsers should be configurable via:

1. Constructor parameter
2. Environment variable (e.g., `ETL_PARSER_STRICTNESS`)
3. Configuration file

Example:
```python
def get_parser_strictness():
    """Get parser strictness from environment or default to tolerant."""
    return os.environ.get("ETL_PARSER_STRICTNESS", "tolerant")

parser = BibleDataParser(strictness=get_parser_strictness())
```

## Logging Requirements

Each strictness level has specific logging requirements:

1. **Strict**:
   - Log errors before raising exceptions
   - Include detailed information about the expected format

2. **Tolerant**:
   - Log warnings for recoverable issues
   - Include information about the recovery action taken
   - Log statistics about recovery attempts

3. **Permissive**:
   - Log errors for all issues
   - Log detailed information about guesses made
   - Provide summary statistics about successful/failed parses

## Update History

- **2025-04-15**: Added configuration examples
- **2025-03-10**: Added logging requirements
- **2025-02-01**: Initial version created 