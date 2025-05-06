"""
DSPy Programs Package for BibleScholarProject

This package contains DSPy-powered modules for Bible research and analysis.
"""

# Import modules for easy access
from .huggingface_integration import (
    configure_huggingface_model,
    configure_teacher_model,
    configure_local_student_model,
    BibleQAModule,
    BibleQASignature,
    load_training_data,
    train_and_compile_model,
    save_models,
    TEACHER_MODELS,
    TARGET_MODELS
) 