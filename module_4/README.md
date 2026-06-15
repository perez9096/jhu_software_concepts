### Raul Perez
# Johns Hopkins University
# Software Concepts
# Module 4 – Testing, Database Integration, and CI

## Overview

This project extends the Grad Cafe system developed in previous modules by adding automated testing, database validation, integration testing, and continuous integration (CI) through GitHub Actions. Each push automatically installs dependencies, starts PostgreSQL, and runs the complete pytest test suite to verify that the application functions correctly.

The application loads graduate admissions data into PostgreSQL, computes analysis metrics, and displays the results through a Flask web interface.

Module 4 focuses on:

* Automated testing with Pytest
* Test coverage using pytest-cov
* Database insertion and query validation
* Flask route testing
* End-to-end integration testing
* GitHub Actions continuous integration

---

## Project Folder Structure

```text
module_4/
│
├── src/
|   |__ supporting scripts/
|   |   |__ scraper.py
|   |   |__ run_scrape_and_standardize.py
|   |   |__ llm_hosting/
|   |       |__ app.py
|   |   
|   |__ templates/
|   |   |__ base.html
|   |   |__ index.html
│   ├── load_data.py
│   └── query_data.py
│
├── tests/
│   ├── test_flask_page.py
│   ├── test_buttons.py
│   ├── test_analysis_format.py
│   ├── test_db_insert.py
│   ├── test_helpers.py
│   └── test_integration_end_to_end.py
│
├── requirements.txt
├── pytest.ini
├── coverage_summary.txt
├── actions_success.png
└── README.md

.github/
└── workflows/
    └── tests.yml
```

---

## Technologies Used

* Python 3.12
* Flask
* PostgreSQL
* Psycopg
* Pytest
* Pytest-Cov
* GitHub Actions

---

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

## Database Configuration

The application expects PostgreSQL connection information through environment variables:

```bash
export PGDATABASE=studentCourses
export PGUSER=postgres
export PGPASSWORD=postgres
export PGHOST=localhost
export PGPORT=5432
```

Start PostgreSQL:

```bash
sudo service postgresql start
```

---

## Running the Application

### Load Data

```bash
python src/load_data.py
```

This creates the applicants table if necessary and loads applicant records into PostgreSQL. A JSONL file is loaded.
- `applicant_data_llm_M3.jsonl` — JSONL used for testing.

### Run Flask Application

```bash
python src/query_data.py
```

Open:

```text
http://127.0.0.1:8000/analysis
```

---

## Testing

Run the complete test suite:

```bash
pytest
```

Generate coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Coverage achieved:

```text
100% coverage
37 tests passed
```

---

## Test Categories

The following pytest markers are used:

### web

Tests Flask route rendering and page content.

### buttons

Tests Pull Data and Update Analysis button behavior and busy-state handling.

### analysis

Tests analysis formatting, labels, and percentage rounding.

### db

Tests database inserts, constraints, and queries.

### integration

Tests complete application workflows from data pull through analysis rendering.

### helpers

Tests utility and helper functions.

---

## Continuous Integration

GitHub Actions is configured to automatically:

1. Start PostgreSQL
2. Install dependencies
3. Run the test suite
4. Verify all tests pass

Workflow file:

```text
.github/workflows/tests.yml
```

Evidence of successful execution is included in:

```text
actions_success.png
```

---

## Implemented Features

### Flask Routes

* GET /analysis
* POST /pull-data
* POST /update-analysis

### Database Features

* Applicant table creation
* Insert and update operations
* Duplicate prevention using URL uniqueness
* Query support for analysis calculations

### Analysis Features

* Fall 2026 applicant counts
* International applicant percentages
* GPA and GRE averages
* Acceptance statistics
* Computer Science admissions analysis
* LLM-standardized program and university analysis

---

