from setuptools import setup, find_packages

setup(
    name="tvtms",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.2.0",
        "psycopg[binary]>=3.2.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
) 