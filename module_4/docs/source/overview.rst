Overview & Setup
================

Purpose
-------

This project collects graduate admissions data from Grad Cafe, stores the
results in PostgreSQL, and provides a Flask web application that displays
summary statistics and analysis.

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
    ├── tests/
    ├── docs/
    └── requirements.txt

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