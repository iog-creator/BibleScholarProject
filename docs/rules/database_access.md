# Database Access Rules

## Connection Management

Always use the connection utility from the database module:

```python
from src.database.connection import get_db_connection

def my_function():
    conn = get_db_connection()
    try:
        # Use connection
        pass
    finally:
        if conn:
            conn.close()
```

## Connection Types

The system supports two types of database connections:

1. **Direct psycopg Connection** - Used for raw SQL operations
2. **SQLAlchemy ConnectionFairy** - Used with SQLAlchemy ORM

All database access code must support both connection types for maximum flexibility:

```python
def perform_database_operation(conn):
    """
    Perform database operation using either connection type.
    
    Args:
        conn: Either a psycopg2 connection or SQLAlchemy ConnectionFairy
    """
    # Check if it's a SQLAlchemy connection
    is_sqlalchemy = hasattr(conn, 'connection')
    
    try:
        if is_sqlalchemy:
            cursor = conn.connection.cursor()
        else:
            cursor = conn.cursor()
            
        # Perform operations with cursor
        cursor.execute("SELECT * FROM table")
        
        # Explicitly commit if using direct psycopg2 connection
        if not is_sqlalchemy:
            conn.commit()
    finally:
        cursor.close()
```

## Transaction Management

1. For direct psycopg connections, always use explicit transaction management:
   ```python
   try:
       # Perform operations
       conn.commit()
   except Exception as e:
       conn.rollback()
       raise
   ```

2. For SQLAlchemy connections, respect the existing transaction:
   ```python
   # SQLAlchemy manages transactions for us
   session.add(new_object)
   # session.commit() should be called by the caller
   ```

## Connection Configuration

1. Always load database configuration from environment variables
2. Use a .env file for local development
3. Set reasonable timeouts and connection limits

Example:
```python
def get_db_connection_from_env():
    """Get database connection using environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "bible_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=30  # 30 second timeout
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None
```

## Error Handling

Always use consistent error handling patterns with database operations:

```python
def safe_execute(conn, query, params=None):
    """Execute a query safely with proper error handling."""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Exception as e:
        logger.error(f"Database error for query {query}: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
```

## Connection Pooling

For production deployments, use connection pooling:

```python
from psycopg2 import pool

# Create a thread-safe connection pool
connection_pool = pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

def get_connection_from_pool():
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def return_connection_to_pool(conn):
    connection_pool.putconn(conn)
```

## Testing Database Code

When testing database code:

1. Use a dedicated test database or schema
2. Implement proper test fixtures
3. Wrap tests in transactions and roll back after each test
4. Use pytest fixtures for database setup and teardown

Example:
```python
@pytest.fixture
def test_db_connection():
    """Fixture for database testing with transaction rollback."""
    conn = get_test_db_connection()
    try:
        yield conn
        # Always rollback after test
        conn.rollback()
    finally:
        conn.close()

def test_database_function(test_db_connection):
    # Test using the connection
    result = my_database_function(test_db_connection)
    assert result is not None
```

## Update History

- **2025-05-05**: Added support for both connection types
- **2025-04-10**: Added connection pooling guidance
- **2025-03-15**: Added transaction management rules
- **2025-02-01**: Initial version created 