#!/usr/bin/env python3
"""
Setup script for the BibleScholarProject package.
"""

from setuptools import setup, find_packages

setup(
    name="BibleScholarProject",
    version="1.2.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=0.19.0",
        "requests>=2.26.0",
        "matplotlib>=3.4.0",
        "pandas>=1.3.0",
        "pytest>=6.2.5",
    ],
    entry_points={
        "console_scripts": [
            "fix-hebrew-strongs=src.etl.fix_hebrew_strongs_ids:main",
            "init-bible-db=scripts.init_database:main",
            "check-db-schema=check_db_schema:main",
            "verify-data=verify_data_processing:main",
        ],
    },
) 