"""
Utilities for handling DSPy deprecation warnings.
"""
import warnings
import contextlib


@contextlib.contextmanager
def suppress_dspy_deprecation_warnings():
    """
    Context manager to suppress DSPy 2.5 deprecation warnings.
    
    Use this when calling DSPy modules that trigger deprecation warnings,
    but only if you're not ready to migrate to the new API yet.
    
    Example:
        ```python
        from src.utils.dspy_warnings import suppress_dspy_deprecation_warnings
        
        # This will suppress the GPT3 client deprecation warnings
        with suppress_dspy_deprecation_warnings():
            result = dspy_module(context=context, question=question)
        ```
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", 
            message="In DSPy 2.5, all LM clients except `dspy.LM` are deprecated"
        )
        warnings.filterwarnings(
            "ignore",
            message="You are using the client GPT3, which will be removed in DSPy 2.6"
        )
        yield


def patch_dspy_warnings():
    """
    Globally patch DSPy to suppress all deprecation warnings.
    
    Note: This is not recommended for development as it hides messages about
    API changes that you'll need to address eventually. Use only in production
    or when absolutely necessary.
    
    Example:
        ```python
        from src.utils.dspy_warnings import patch_dspy_warnings
        
        # Call at the start of your application
        patch_dspy_warnings()
        
        # Now all DSPy deprecation warnings will be suppressed
        ```
    """
    warnings.filterwarnings(
        "ignore", 
        message="In DSPy 2.5, all LM clients except `dspy.LM` are deprecated"
    )
    warnings.filterwarnings(
        "ignore",
        message="You are using the client GPT3, which will be removed in DSPy 2.6"
    ) 