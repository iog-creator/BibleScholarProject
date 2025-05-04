# Bible Scholar Project Makefile

.PHONY: help setup install db-setup db-create etl etl-lexicons etl-texts etl-morphology etl-names etl-arabic etl-tvtms test test-unit test-integration verify run run-minimal run-debug clean optimize-db fix-hebrew-strongs process-lexicons debug-lexicon

# Load environment variables
include .env

help:
	@echo "Bible Scholar Project Commands:"
	@echo "make help              - Show this help message"
	@echo "make setup             - Set up the environment and database"
	@echo "make install           - Install Python dependencies"
	@echo "make db-setup          - Set up database schema"
	@echo "make db-create         - Create database (if it doesn't exist)"
	@echo "make etl               - Run all ETL processes"
	@echo "make etl-lexicons      - Run lexicon ETL process"
	@echo "make etl-texts         - Run Bible texts ETL process"
	@echo "make etl-morphology    - Run morphology ETL process"
	@echo "make etl-names         - Run proper names ETL process"
	@echo "make etl-arabic        - Run Arabic Bible ETL process"
	@echo "make etl-tvtms         - Run TVTMS (Versification and Markup) ETL process"
	@echo "make test              - Run all tests"
	@echo "make test-unit         - Run unit tests"
	@echo "make test-integration  - Run integration tests"
	@echo "make verify            - Verify data processing"
	@echo "make run               - Run the web application"
	@echo "make run-minimal       - Run the minimal web application"
	@echo "make run-debug         - Run the web application in debug mode"
	@echo "make clean             - Clean temporary files and __pycache__"
	@echo "make optimize-db       - Optimize the database"
	@echo "make fix-hebrew-strongs - Fix extended Hebrew Strong's IDs"
	@echo "make process-lexicons  - Process lexicons"
	@echo "make debug-lexicon     - Debug lexicon"

setup: install db-create db-setup

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -e .

db-create:
	@echo "Creating database if it doesn't exist..."
	@python -c "import psycopg2; conn = psycopg2.connect(dbname='postgres', user='$(DB_USER)', host='$(DB_HOST)', password='$(DB_PASSWORD)'); conn.autocommit = True; try: conn.cursor().execute('CREATE DATABASE $(DB_NAME)'); print('Database created.'); except Exception as e: print('Database already exists or error:', e); conn.close()"

db-setup:
	@echo "Setting up database schema..."
	@PGPASSWORD="$(DB_PASSWORD)" psql -U $(DB_USER) -h $(DB_HOST) -d $(DB_NAME) -f sql/schema.sql

etl: etl-lexicons etl-texts etl-morphology etl-names etl-arabic etl-tvtms

etl-lexicons:
	@echo "Running lexicon ETL process..."
	@python -m src.etl.etl_lexicons
	@python -m src.etl.etl_lsj_lexicon

etl-texts:
	@echo "Running Bible texts ETL process..."
	@python -m src.etl.etl_bible_texts
	@python -m src.etl.etl_hebrew_ot
	@python -m src.etl.etl_greek_nt

etl-morphology:
	@echo "Running morphology ETL process..."
	@python -m src.etl.etl_morphology_docs

etl-names:
	@echo "Running proper names ETL process..."
	@python -m src.etl.etl_proper_names

etl-arabic:
	@echo "Running Arabic Bible ETL process..."
	@python -m src.etl.etl_arabic_bible

etl-tvtms:
	@echo "Running TVTMS ETL process..."
	@python -m src.tvtms.process_tvtms

test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	@pytest tests/unit -v

test-integration:
	@echo "Running integration tests..."
	@pytest tests/integration -v

verify:
	@echo "Verifying data processing..."
	@python verify_data_processing.py

run:
	@echo "Starting web application..."
	@python src/web_app.py

run-minimal:
	@echo "Starting minimal web application..."
	@python src/web_app_minimal.py

run-debug:
	@echo "Starting web application in debug mode..."
	@python src/web_app.py --debug

# Additional targets for the removed scripts (now referencing root directory versions)
optimize-db:
	@echo "Optimizing database..."
	@python ../optimize_database.py

fix-hebrew-strongs:
	@echo "Fixing extended Hebrew Strong's IDs..."
	@python ../fix_extended_hebrew_strongs.py

process-lexicons:
	@echo "Processing lexicons..."
	@python ../process_lexicons.py

debug-lexicon:
	@echo "Debugging lexicon..."
	@python ../debug_lexicon.py

clean:
	@echo "Cleaning temporary files and __pycache__..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".coverage" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name "build" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@echo "Cleaned." 