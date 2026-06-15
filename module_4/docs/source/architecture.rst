# Architecture

## Overview

The Grad Cafe application is organized into three layers:

1. Web Layer
2. ETL Layer
3. Database Layer

Each layer has a specific responsibility and communicates with the next layer to collect, process, store, and analyze graduate admissions data.

## Web Layer

Implemented in:

* `query_data.py`

Responsibilities:

* Serve the Flask web application
* Render admissions statistics and analysis
* Handle Pull Data requests from users
* Handle Update Analysis requests
* Query PostgreSQL for current statistics
* Fall back to local JSONL data if the database is unavailable
* Launch the ETL pipeline when new data is requested

## ETL Layer

Implemented by:

* `scraper.py`
* `run_scrape_and_standardize.py`
* `llm_hosting/app.py`
* `load_data.py`

Responsibilities:

* Scrape admissions survey data from Grad Cafe
* Resume scraping using checkpoint files
* Standardize university and program names using a local LLM
* Transform scraped records into a structured format
* Load processed applicant records into PostgreSQL

## ETL Workflow

The ETL process is coordinated by `run_scrape_and_standardize.py`.

The workflow performs the following steps:

1. Execute `scraper.py` to collect Grad Cafe survey data.
2. Save raw results to `applicant_data.json`.
3. Execute `llm_hosting/app.py` to standardize university and program names.
4. Save standardized results to `applicant_data_llm_M4.jsonl`.
5. Execute `load_data.py` to insert records into PostgreSQL.

## Database Layer

Implemented in:

* PostgreSQL

Primary Table:

::

```
applicants
```

Responsibilities:

* Store applicant admissions records
* Prevent duplicate records through URL uniqueness
* Support aggregate analysis queries
* Persist data across application runs
* Serve as the primary source of statistics for the web application

## Data Flow

::

```
Grad Cafe
     |
     v
  scraper.py
     |
     v
applicant_data.json
     |
     v
run_scrape_and_standardize.py
     |
     v
llm_hosting/app.py
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
```

## Fallback Flow

If PostgreSQL is unavailable, `query_data.py` falls back to reading data from:

::

```
applicant_data_llm_M3.jsonl
```

This ensures that analysis pages can still be displayed even when the database cannot be reached.
