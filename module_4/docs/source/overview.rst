Overview & Setup
================

Purpose
-------

This project extends the Grad Cafe system developed in previous modules by adding automated testing, database validation, integration testing, and continuous integration (CI) through GitHub Actions.
Each push automatically installs dependencies, starts PostgreSQL, and runs the complete pytest test suite to verify that the application functions correctly.
The application loads graduate admissions data into PostgreSQL, computes analysis metrics, and displays the results through a Flask web interface.


The application supports:

* Pulling new data from Grad Cafe
* Loading data into PostgreSQL
* Computing admissions statistics
* Viewing analysis through a web interface
* Falling back to a JSONL dataset if the database is unavailable


Project Structure
-----------------

::

    module_4/
    ├── src/
    │   ├── query_data.py
    │   ├── load_data.py
    │   ├── applicant_data_llm_M3.jsonl
    │   └── templates/
    |   |   |__ base.html
    |   |   |__ index.html
    |   |__ supporting scripts/
    |       |__ scraper.py
    |       |__ run_scrape_and_standardize.py
    |       |__ llm_hosting/
    |           |__ app.py
    ├── tests/
    │   ├── test_flask_page.py
    │   ├── test_buttons.py
    │   ├── test_analysis_format.py
    │   ├── test_db_insert.py
    │   ├── test_helpers.py
    │   └── test_integration_end_to_end.py
    ├── docs/
    │   ├── build/
    │   ├── source/
    │   ├── make.bat
    │   ├── Makefile
    └── requirements.txt
    ├── pytest.ini
    ├── coverage_summary.txt
    ├── actions_success.png
    └── README.md

Running the Application
-----------------------

Start PostgreSQL:

::

    sudo service postgresql start

Run the Flask application:

::

    python src/query_data.py

Open a browser and visit:

::

    http://localhost:8000

Environment Variables
---------------------

The application supports the following database configuration variables:

::

    PGDATABASE
    PGUSER
    PGPASSWORD
    PGHOST
    PGPORT

Example:

::

    export PGDATABASE=studentCourses
    export PGUSER=postgres
    export PGPASSWORD=postgres

Running Tests
-------------

Run the full test suite:
::

    pytest

Run tests with coverage:
::
    pytest --cov=src

Run tests by marker:
::

    pytest -m "web or buttons or analysis or db or integration or helpers"