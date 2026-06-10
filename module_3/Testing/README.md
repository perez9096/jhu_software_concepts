# Module 3 Testing README

## Overview

This folder contains the database ingestion and Flask frontend components for the Grad Cafe applicant analytics pipeline.

The main flow is:
1. `module_2/scraper.py` collects applicant records from thegradcafe.com and writes JSON output.
2. `module_2/llm_hosting/app.py` optionally standardizes program/university strings and writes enriched JSON or JSONL.
3. `module_3/Testing/load_data.py` loads that JSON into a PostgreSQL `applicants` table and prints summary statistics.
4. `module_3/Testing/query_data.py` runs a Flask web app that displays the summary metrics in a browser.

## Files

- `module_2/llm_hosting/app.py` — local LLM standardizer that can process app JSON and append `llm-generated-program` and `llm-generated-university` fields.
- `load_data.py` — reads applicant JSON, maps fields, creates the `applicants` table if needed, and upserts rows into PostgreSQL.
- `query_data.py` — starts a Flask server and builds the summary dashboard from PostgreSQL.
- `small_output.json` — sample JSON used for fallback and testing.
- `templates/index.html` — Flask template that renders the nine summary metric blocks.
- `database.db` — unrelated local SQLite file; the current web app uses PostgreSQL.

## Flow

### 1. Scrape applicant records

The scraper in `module_2/scraper.py` generates JSON records in `module_2/applicant_data.json` by scraping the Grad Cafe survey pages.

### 2. Standardize programs and universities with LLM

`module_2/llm_hosting/app.py` can take the scraped JSON and add cleaned fields:
- `llm-generated-program`
- `llm-generated-university`

It can be run in two modes:
- `--serve` starts an HTTP standardization service at `http://127.0.0.1:8000`
- CLI mode processes a JSON input file and emits either an enriched `.json` or JSONL output

Example CLI command:
```bash
python3 module_2/llm_hosting/app.py --file module_2/applicant_data.json --out module_2/applicant_data_with_llm.json
```

### 3. Load JSON into PostgreSQL

`load_data.py` does the following:
- Reads JSON rows from the specified file.
- Normalizes fields such as `Program Name`, `GPA`, `GRE Score`, `Semester and Year of Program Start`, and LLM-generated fields.
- Connects to PostgreSQL using environment variables, defaulting to:
  - `PGDATABASE=studentCourses`
  - `PGUSER=postgres`
  - `PGPASSWORD=postgres`
  - `PGHOST=localhost`
  - `PGPORT=5432`
- Creates an `applicants` table if it does not exist.
- Inserts or updates rows using `ON CONFLICT (url) DO UPDATE`.
- Prints the same summary counts and averages that the web page displays.

If you want to use LLM-enriched data, pass the LLM output file instead of `module_2/applicant_data.json`:
```bash
python3 module_3/Testing/load_data.py --file module_2/applicant_data_with_llm.json
```

### 3. Serve the web page

`query_data.py` does the following:
- Connects to PostgreSQL with the same environment variable defaults.
- Runs queries to compute the nine summary metrics:
  1. Accepted applicants for Fall 2026
  2. Percentage of international students
  3. Average GPA, GRE, GRE V, GRE AW for available metrics
  4. Average GPA of American students in Fall 2026
  5. Acceptance percentage for Fall 2026
  6. Average GPA of accepted applicants for Fall 2026
  7. Applicants to JHU for a masters degree in Computer Science
  8. 2026 acceptances to Georgetown, MIT, Stanford, or CMU for a PhD in Computer Science
  9. The same query using LLM-generated program/university fields
- Renders these results in `templates/index.html`.
- If PostgreSQL is unavailable, it will fall back to loading `small_output.json` and compute statistics from that sample JSON.

## Run the full pipeline

From the repo root:

```bash
cd /workspaces/jhu_software_concepts
source .venv/bin/activate
sudo service postgresql start
python3 module_3/Testing/load_data.py --file module_2/applicant_data.json
export PGPASSWORD=postgres
export PGDATABASE=studentCourses
export PGUSER=postgres
export PGHOST=localhost
python3 module_3/Testing/query_data.py
```

Then open:

```text
http://127.0.0.1:8080
```

## One-line command

```bash
cd /workspaces/jhu_software_concepts && source .venv/bin/activate && sudo service postgresql start && python3 module_3/Testing/load_data.py --file module_2/applicant_data.json && PGPASSWORD=postgres PGDATABASE=studentCourses PGUSER=postgres PGHOST=localhost nohup python3 module_3/Testing/query_data.py >/tmp/query_data.log 2>&1 &
```

## Notes

- The Flask app is a development server; use a production WSGI server for deployment.
- The PostgreSQL host is expected to be available at `localhost:5432`.
- If `psql` reports authentication issues, confirm the `postgres` user password or create a dedicated DB user.
- The sample `small_output.json` file is useful for fallback and UI testing without a live database.
