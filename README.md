# Bible Scholar Project

A comprehensive Bible study tool providing access to original language lexicons, theological terms, and Bible text comparison across translations.

## Features

- Access to Hebrew and Greek lexicons with Strong's IDs
- Bible text browsing and search across multiple translations 
- Theological term analysis and cross-language comparison
- Text-verse-to-morphology-state (TVTMS) mapping for textual variants
- Morphology analysis for Hebrew and Greek words
- API for programmatic access to Bible data
- Web interface for interactive Bible study
- DSPy training data collection for AI model training

## Components

- **Database**: PostgreSQL database with Bible verses, lexicons, and morphology
- **ETL Pipeline**: Data processing for importing and transforming Bible data
- **API**: RESTful API for programmatic access to Bible data
- **Web Interface**: Interactive web interface for Bible study
- **DSPy Collection**: System for generating training data for AI models

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Poetry (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BibleScholarProject.git
cd BibleScholarProject
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# Or with Poetry
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Set up the database:
```bash
make db-setup
```

5. Load data:
```bash
make etl
```

## Usage

### Running the Application

Start the API and web server:
```bash
python start_servers.py
# Or with Make
make run-all
```

This will start:
- API server on http://localhost:5000
- Web server on http://localhost:5001

You can also start individual servers:
```bash
# Start only the API server
python start_servers.py --api-only

# Start only the web server
python start_servers.py --web-only

# Customize ports
python start_servers.py --api-port 8000 --web-port 8001
```

The servers use Flask applications configured as:
- API: `src.api.lexicon_api:app`
- Web: `src.web_app`

### API Usage

Access the API endpoints:

```bash
# Get Hebrew lexicon entry
curl http://localhost:5000/api/lexicon/hebrew/H7225

# Search lexicon
curl http://localhost:5000/api/lexicon/search?q=beginning&lang=hebrew

# Get morphology info
curl http://localhost:5000/api/morphology/hebrew/Ncmsc
```

See the [API documentation](docs/API_REFERENCE.md) for more details.

### Web Interface

Access the web interface at http://localhost:5001:

- `/`: Home page with search
- `/lexicon/hebrew/{strongs_id}`: Hebrew lexicon entry
- `/lexicon/greek/{strongs_id}`: Greek lexicon entry
- `/bible/{book}/{chapter}/{verse}`: Bible verse
- `/search?q={term}`: Search Bible and lexicons
- `/morphology/{lang}/{code}`: Morphology details

### DSPy Training Data Collection

The project includes a sophisticated system for generating training data for AI models:

```bash
# Check DSPy training data status
make dspy-status

# Refresh DSPy training data
make dspy-refresh

# Enhance training data with additional examples
make dspy-enhance

# Log user interactions as training data
make dspy-log-interactions
```

See the [DSPy Training documentation](docs/DSPY_TRAINING.md) for more details.

## Development

### Project Structure

```
BibleScholarProject/
├── data/                    # Data files
│   ├── processed/           # Processed data files
│   │   └── dspy_training_data/ # DSPy training datasets
│   └── raw/                 # Raw data files
├── docs/                    # Documentation
├── scripts/                 # Scripts for data processing and utilities
├── src/                     # Source code
│   ├── api/                 # API endpoints
│   ├── database/            # Database access
│   ├── etl/                 # ETL pipeline
│   │   ├── morphology/      # Morphology processing
│   │   └── names/           # Name entity processing
│   ├── tvtms/               # Text-verse-to-morphology-state mapping
│   └── utils/               # Utility functions
│       └── dspy_collector.py # DSPy collection system
├── templates/               # Web templates
└── tests/                   # Tests
    ├── integration/         # Integration tests
    └── unit/                # Unit tests
```

### Testing

Run the tests:
```bash
make test
```

### Adding New Translations

To add a new Bible translation:
```bash
python load_public_domain_bibles.py --translation={TRANSLATION_CODE}
```

This will automatically trigger DSPy training data collection.

## Workspace Organization

The project workspace has been organized for better clarity:

- **Root Directory**: Contains only essential files needed for day-to-day development
- **archive/**: Storage for older, less frequently used files
  - **bible_loading_scripts/**: Deprecated Bible loading scripts (superseded by load_public_domain_bibles.py)
  - **logs/**: Log files from various processes
  - **tmp_files/**: Temporary files and scripts
  - **tests/**: Older test files for reference
- **tests/**: Contains all test files organized by type (unit, integration)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.