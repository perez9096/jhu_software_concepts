Final files and brief usage — module_2

Purpose
- This file lists the final scripts, folders, and data in `module_2` and how to run the common pipelines.

Final scripts and data
- `scraper.py` — Main scraper. Runs page-by-page and saves `applicant_data.json`.
  - Quick run: `python3 module_2/scraper.py`
- `batch_scraper.py` — Batched scraping helper to collect pages in chunks and produce `applicant_data_combined.json`.
- `enhance_combined.py` — Post-process `applicant_data_combined.json` to fetch detail pages and enrich fields (supports `--limit N`).
  - Example: `python3 module_2/enhance_combined.py --limit 100`
- `applicant_data.json` — Final mapped JSON (user-facing format with normalized fields). Consider this the primary output for downstream work.
- `applicant_data_combined.json` — Combined records from batch runs (rawer, useful for reprocessing).
- `applicant_data_enhanced.json` — Output of running `enhance_combined.py` over the combined dataset.

LLM standardization
- `llm_hosting/` — Local LLM standardizer (contains `app.py`, `README.md`, and model helper files).
  - Install deps: `pip install -r module_2/llm_hosting/requirements.txt`
  - CLI mode: `python module_2/llm_hosting/app.py --file <input.json> --out output.json`
  - For testing, use the repo's `small_applicant_data_for_llm.json` or create a subset.

Other files
- `requirements.txt` — Python deps relevant to scraping/hosting (check `llm_hosting/requirements.txt` for LLM-specific deps).
- `llm_hosting-1.zip` — Archive (not required if `llm_hosting/` is present).
- `Testing/` — Additional scripts used for experiments (not part of the main pipeline).
- `__pycache__/` — Python caches (ignore).
- `README.txt` — Original notes.

Notes & recommendations
- Consider `applicant_data.json` your canonical downstream file. Keep `applicant_data_combined.json` and `applicant_data_enhanced.json` for reprocessing if needed.
- I did NOT rename or move files; if you'd like I can place `archive/` or `final/` subfolders and move unneeded files there.
- Next steps I can take on request:
  - Move experimental files into `module_2/Archive/`.
  - Commit `FINAL_FILES.md` and `enhance_combined.py` changes.
  - Run full LLM standardization on `applicant_data.json` (will be CPU-heavy).

Contact me which of the next steps you'd like me to take.
