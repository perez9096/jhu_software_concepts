# Module 3 Testing README
# Raul Perez
## Overview

This folder contains the data ingesion layer and Flask frontend application supporting the Grad Cafe applicant analytics pipeline.

The main flow is:
1. `module_3/supporting scripts/scraper.py` collects applicant records from thegradcafe.com and writes JSON output. Currently max pages set to 50 for webpage button.
2. `module_3/supporting scripts/llm_hosting/app.py` optionally standardizes program/university strings and writes enriched JSON or JSONL.
3. `module_3/load_data.py` loads that JSON into a PostgreSQL `applicants` table and prints summary statistics.
4. `module_3/query_data.py` runs a Flask web app that displays the summary metrics in a browser.

## Files

- `module_3/supporting scripts/llm_hosting/app.py` — local LLM standardizer that can process app JSON and append `llm-generated-program` and `llm-generated-university` fields.
- `module_3/supporting scripts/scraper.py` - collects applicant records from thegradcafe.com and writes JSON output.
- `module_3/supporting scripts/run_scrape_and_standardize.py` - combines processing of app.py and scraper.py as a 1-click run for obtaining applicant_data_M3.json and applicant_data_llm_M3.jsonl files.
- `load_data.py` — reads applicant JSON, maps fields, creates the `applicants` table if needed, and upserts rows into PostgreSQL.
- `query_data.py` — starts a Flask server and builds the summary dashboard from PostgreSQL.
- `applicant_data_llm_M3.jsonl` — sample JSONL used for testing with 3,000+ pages collected.
- `templates/index.html` — Flask template that renders the nine summary metric blocks.

## Flow

### 1. Scrape applicant records

The scraper in `scraper.py` generates JSON records in `applicant_data.json` by scraping the Grad Cafe survey pages.

### 2. Standardize programs and universities with LLM

`module_2/llm_hosting/app.py` can take the scraped JSON and add cleaned fields:
- `llm-generated-program`
- `llm-generated-university`

It can be run in two modes:
- `--serve` starts an HTTP standardization service at `http://127.0.0.1:8000`
- CLI mode processes a JSON input file and emits either an enriched `.json` or JSONL output

Example CLI command:
```bash
python3 module_3/supporting scripts/llm_hosting/app.py --file applicant_data_M3.json --out applicant_data_llm_M3.jsonl
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

If you want to use LLM-enriched data, pass the LLM output file instead of `applicant_data_M3.json`:
```bash
python3 module_3/load_data.py --file module_3/applicant_data_with_llm.json
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
- If PostgreSQL is unavailable, it will fall back to loading `applicant_data_llm_M3.jsonl` and compute statistics from that sample JSON.

## Run the full pipeline

From the repo root:

```bash
cd /workspaces/jhu_software_concepts
source .venv/bin/activate
sudo service postgresql start
python3 module_3/load_data.py --file module_3/supporting scripts/applicant_data_llm_M3.jsonl
export PGPASSWORD=postgres
export PGDATABASE=studentCourses
export PGUSER=postgres
export PGHOST=localhost
python3 module_3/query_data.py
```

Then open:

```text
http://127.0.0.1:8000
```

## One-line command

```bash
cd /workspaces/jhu_software_concepts && source .venv/bin/activate && sudo service postgresql start && python3 module_3/load_data.py --file module_3/applicant_data_llm_M3.jsonl && PGPASSWORD=postgres PGDATABASE=studentCourses PGUSER=postgres PGHOST=localhost nohup python3 module_3/query_data.py >/tmp/query_data.log 2>&1 &
```

## Notes

- The Flask app is a development server; use a production WSGI server for deployment.
- The PostgreSQL host is expected to be available at `localhost:5432`.
- If `psql` reports authentication issues, confirm the `postgres` user password or create a dedicated DB user.
- The sample `applicant_data_llm_M3.jsonl` file is useful for fallback and UI testing without a live database.
