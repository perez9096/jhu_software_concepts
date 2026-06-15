Architecture
============

Overview
--------

The application is divided into three layers:

1. Web Layer
2. ETL Layer
3. Database Layer

Web Layer
---------

Implemented in ``query_data.py``.

Responsibilities:

* Serve the Flask web application
* Handle Pull Data requests
* Handle Update Analysis requests
* Query PostgreSQL for statistics
* Fall back to JSONL data when necessary

ETL Layer
---------

Implemented by:

* ``scraper.py``
* ``run_scrape_and_standardize.py``
* ``load_data.py``

Responsibilities:

* Scrape Grad Cafe survey data
* Standardize records using the local LLM
* Transform scraped data into database-ready rows
* Load data into PostgreSQL

Database Layer
--------------

Implemented in PostgreSQL.

The primary table is:

::

    applicants

Responsibilities:

* Store admissions records
* Enforce URL uniqueness
* Support statistical queries
* Provide persistence across application runs

Data Flow
---------

::

    Grad Cafe
         |
         v
    scraper.py
         |
         v
    applicant_data.json
         |
         v
    LLM Standardization
         |
         v
    applicant_data_llm_M4.jsonl
         |
         v
    load_data.py
         |
         v
    PostgreSQL
         |
         v
    query_data.py
         |
         v
    Flask UI