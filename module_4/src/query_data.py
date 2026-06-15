import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import psycopg
from flask import Flask, render_template, request, redirect, url_for

# Setting Flask
SCRIPT_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(SCRIPT_DIR / "templates")
)
scrape_status = {
    "running": False,
    "message": None,
    "started_at": None,
    "finished_at": None,
}
status_lock = threading.Lock()

# connecting to Postgres using environment variables for configuration, with defaults for local development.

def get_db_connection():
    dbname = os.getenv("PGDATABASE") or os.getenv("DB_NAME")
    user = os.getenv("PGUSER") or os.getenv("DB_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")
    host = os.getenv("PGHOST") or os.getenv("DB_HOST") or "localhost"
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"

    required = {
        "PGDATABASE or DB_NAME": dbname,
        "PGUSER or DB_USER": user,
        "PGPASSWORD or DB_PASSWORD": password,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise RuntimeError(
            f"Missing database configuration: {', '.join(missing)}"
        )

    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

# Status check!
def is_scrape_running():
    with status_lock:
        return scrape_status["running"]

# For buttons and status messages on the frontend.
def get_scrape_status_message():
    with status_lock:
        if scrape_status["running"]:
            elapsed = datetime.now() - scrape_status["started_at"]

            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)

            return (
                f"Pull Data is running ({minutes}m {seconds}s elapsed). "
                "Analysis will refresh once the current data update completes."
            )

        if scrape_status["finished_at"]:
            return scrape_status["message"]

        return scrape_status["message"]

# For button state and status updates when starting/stopping the scraper and loading process.
def _update_scrape_status(running, message=None):
    with status_lock:
        scrape_status["running"] = running
        scrape_status["message"] = message
        now = datetime.now()
        if running:
            scrape_status["started_at"] = now
            scrape_status["finished_at"] = None
        else:
            scrape_status["finished_at"] = now

# parsing numeric fields like GPA and GRE scores, handling various formats and cleaning the data for analysis.
def parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.lower() in ("none", "n/a", "na", ""):
        return None
    try:
        return float(text)
    except ValueError:
        match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
        if match:
            return float(match.group(0))
    return None

# for output
def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()

# Loading data from JSONL, mapping to standardized fields, and inserting into Postgres with upsert logic. Also includes example queries to demonstrate loaded data.
def load_applicants_from_jsonl(filename="applicant_data_llm_M3.jsonl"):
    path = SCRIPT_DIR / filename
    if not path.exists():
        path = Path(os.getcwd()) / filename

    if not path.exists():
        return []

    raw_rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_rows.append(json.loads(line))

    applicants = []
    for row in raw_rows:
        applicants.append({
            "program": normalize_text(row.get("Program Name") or row.get("program") or row.get("program_name")),
            "term": normalize_text(row.get("Semester and Year of Program Start") or row.get("semester_year")),
            "status": normalize_text(row.get("Applicant Status") or row.get("applicant_status")),
            "us_or_international": normalize_text(row.get("International or American Student")),
            "gpa": parse_number(row.get("GPA")),
            "gre": parse_number(row.get("GRE Score")),
            "gre_v": parse_number(row.get("GRE V Score")),
            "gre_aw": parse_number(row.get("GRE AW")),
            "university": normalize_text(row.get("University") or row.get("university")),
            "degree": normalize_text(row.get("Masters or PhD") or row.get("degree")),
            "llm_generated_program": normalize_text(row.get("llm-generated-program") or row.get("llm_generated_program")),
            "llm_generated_university": normalize_text(row.get("llm-generated-university") or row.get("llm_generated_university")),
        })

    return applicants


def compute_stats_from_jsonl(applicants):
    # 1. How many entries do you have in your database who have applied for Fall 2026
    Fall2026entries_count = sum(
        1
        for row in applicants
        if row["term"] == "Fall 2026"
    )
    # 2. What Percentage of entries are from international students?
    international_count = sum(
        1 for row in applicants if row["us_or_international"] == "International"
    )
    total_count = Fall2026entries_count
    international_pct = (international_count / total_count * 100) if international_count > 0 else None
    # 3. What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics
    rows_with_any_metric = [
        row
        for row in applicants
        if row["gpa"] is not None or row["gre"] is not None or row["gre_v"] is not None or row["gre_aw"] is not None
    ]
    avg_gpa = (
        sum(row["gpa"] for row in rows_with_any_metric if row["gpa"] is not None) / len(rows_with_any_metric)
        if rows_with_any_metric
        else None
    )
    avg_gre = (
        sum(row["gre"] for row in rows_with_any_metric if row["gre"] is not None) / len(rows_with_any_metric)
        if rows_with_any_metric
        else None
    )
    avg_gre_v = (
        sum(row["gre_v"] for row in rows_with_any_metric if row["gre_v"] is not None) / len(rows_with_any_metric)
        if rows_with_any_metric
        else None
    )
    avg_gre_aw = (
        sum(row["gre_aw"] for row in rows_with_any_metric if row["gre_aw"] is not None) / len(rows_with_any_metric)
        if rows_with_any_metric
        else None
    )
    # 4. What is the average GPA of American students in the Fall 2026 term.
    american_fall2026 = [
        row["gpa"]
        for row in applicants
        if row["us_or_international"] == "American" and row["term"] == "Fall 2026" and row["gpa"] is not None
    ]
    avg_gpa_american_fall2026 = (
        sum(american_fall2026) / len(american_fall2026) if american_fall2026 else None
    )
    # 5. What percent of entries for Fall 2026 are Acceptances
    acceptance_count = sum(
        1
        for row in applicants
        if row["term"] == "Fall 2026" and row["status"] == "Accepted"
    )
    total_fall2026 = Fall2026entries_count
    acceptance_percentage = (acceptance_count / total_fall2026 * 100) if acceptance_count > 0 else None
    # 6. What is the average GPA of applicants who applied for Fall 2026 who are Acceptances
    accepted_fall2026_gpas = [
        row["gpa"]
        for row in applicants
        if row["term"] == "Fall 2026" and row["status"] == "Accepted" and row["gpa"] is not None
    ]
    avg_gpa_accepted_fall2026 = (
        sum(accepted_fall2026_gpas) / len(accepted_fall2026_gpas) if accepted_fall2026_gpas else None
    )
    # 7. How many entries are from applicants who applied to JHU for a masters degree in Computer Science
    jhu_masters_count = sum(
        1
        for row in applicants
        if "%johns hopkins university%" in f"%{row['university'].lower()}%" and "%masters%" in f"%{row['degree'].lower()}%" and "%computer science%" in f"%{row['program'].lower()}%"
    )

    # 8. How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Standford University, or Carnegie Mellon University for a PhD in Computer Science.
    top_universities = [
        "%georgetown university%",
        "%mit%",
        "%stanford university%",
        "%carnegie mellon university%",
    ]
    top_universities_phd_accepted_2026_count = sum(
        1
        for row in applicants
        if "%2026%" in f"%{row['term'].lower()}%"
        and "%accepted%" in f"%{row['status'].lower()}%"
        and any(univ.strip('%') in row["program"].lower() for univ in top_universities)
        and "%phd%" in row["degree"].lower()
        and "%computer science%" in f"%{row['program'].lower()}%"
    )
    # 9. Does the numbers for 8. change if using LLM Generated Fields (rather than the original university and degree fields).
    top_universities_phd_accepted_2026_llm_count = sum(
        1
        for row in applicants
        if "%2026%" in f"%{row['term'].lower()}%"
        and "%accepted%" in f"%{row['status'].lower()}%"
        and any(univ.strip('%') in row["llm_generated_university"].lower() for univ in top_universities) 
        and "%phd%" in row["llm_generated_program"].lower()
        and "%computer science%" in f"%{row['program'].lower()}%"
    )

    return {
        "fall2026_entries_count": Fall2026entries_count,
        "international_pct": international_pct,
        "avg_gpa": avg_gpa,
        "avg_gre": avg_gre,
        "avg_gre_v": avg_gre_v,
        "avg_gre_aw": avg_gre_aw,
        "avg_gpa_american_fall2026": avg_gpa_american_fall2026,
        "acceptance_percentage": acceptance_percentage,
        "avg_gpa_accepted_fall2026": avg_gpa_accepted_fall2026,
        "jhu_masters_count": jhu_masters_count,
        "top_universities_phd_accepted_2026_count": top_universities_phd_accepted_2026_count,
        "top_universities_phd_accepted_2026_llm_count": top_universities_phd_accepted_2026_llm_count,
    }


def get_stats_from_db(cur):
    # 1. How many entries do you have in your database who have applied for Fall 2026. 
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = %s;",
        ("Fall 2026",),
    )
    Fall2026entries_count = cur.fetchone()[0]

    # 2. What Percentage of entries are from international students?
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE us_or_international = %s;",
        ("International",),
    )
    international_count = cur.fetchone()[0]

    total_count = Fall2026entries_count
    international_pct = (international_count / total_count * 100) if international_count > 0 else None

    # 3. What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics.
    cur.execute(
        "SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM applicants WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;"
    )
    avg_result = cur.fetchone() or (None, None, None, None)

    # 4. What is the average GPA of American students in the Fall 2026 term.
    cur.execute(
        "SELECT AVG(gpa) FROM applicants WHERE us_or_international = %s AND term = %s AND gpa IS NOT NULL;",
        ("American", "Fall 2026"),
    )
    avg_gpa_american_fall2026 = cur.fetchone()[0]

    # 5. What percent of entries for Fall 2026 are Acceptances
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = %s AND status = %s;",
        ("Fall 2026", "Accepted"),
    )
    accepted_fall2026 = cur.fetchone()[0]
    acceptance_percentage = (accepted_fall2026 / Fall2026entries_count * 100) if Fall2026entries_count > 0 else None

    # 6. What is the average GPA of applicants who applied for Fall 2026 who are Acceptances.
    cur.execute(
        "SELECT AVG(gpa) FROM applicants WHERE term = %s AND status = %s AND gpa IS NOT NULL;",
        ("Fall 2026", "Accepted"),
    )
    avg_gpa_accepted_fall2026 = cur.fetchone()[0]

    # 7. How many entries are from applicants who applied to JHU for a masters degree in Computer Science.
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE university ILIKE %s AND degree ILIKE %s AND program ILIKE %s;",
        ("%Johns Hopkins University%", "%Masters%", "%Computer Science%"),
    )
    jhu_masters_count = cur.fetchone()[0]

    # 8. How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Standford University, or Carnegie Mellon University for a PhD in Computer Science.
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term ILIKE %s AND status ILIKE %s AND university ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND degree ILIKE %s AND program ILIKE %s;",
        ("%2026%", "%Accepted%", "%Georgetown University%", "%MIT%", "%Stanford University%", "%Carnegie Mellon University%", "%PhD%", "%Computer Science%"),
    )
    top_universities_phd_accepted_2026_count = cur.fetchone()[0]

    # 9. Does the numbers for 8. change if using LLM Generated Fields (rather than the original university and degree fields).
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term ILIKE %s AND status ILIKE %s AND llm_generated_university ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND degree ILIKE %s AND llm_generated_program ILIKE %s;",
        ("%2026%", "%Accepted%", "%Georgetown University%", "%MIT%", "%Stanford University%", "%Carnegie Mellon University%", "%PhD%", "%Computer Science%"),
    )
    top_universities_phd_accepted_2026_llm_count = cur.fetchone()[0]

    return {
        "fall2026_entries_count": Fall2026entries_count,
        "international_pct": international_pct,
        "avg_gpa": avg_result[0],
        "avg_gre": avg_result[1],
        "avg_gre_v": avg_result[2],
        "avg_gre_aw": avg_result[3],
        "avg_gpa_american_fall2026": avg_gpa_american_fall2026,
        "acceptance_percentage": acceptance_percentage,
        "avg_gpa_accepted_fall2026": avg_gpa_accepted_fall2026,
        "jhu_masters_count": jhu_masters_count,
        "top_universities_phd_accepted_2026_count": top_universities_phd_accepted_2026_count,
        "top_universities_phd_accepted_2026_llm_count": top_universities_phd_accepted_2026_llm_count,
    }

# Pulling data once clicked by button
def _run_scraper_and_load():
    _update_scrape_status(True, "Pull Data started.")

    support_dir = SCRIPT_DIR / "supporting scripts"
    runner_path = support_dir / "run_scrape_and_standardize.py"
    load_path = SCRIPT_DIR / "load_data.py"

    llm_output = SCRIPT_DIR / "applicant_data_llm_M4.jsonl"

    try:
        runner_cmd = [
            sys.executable,
            str(runner_path),
            "--pages",
            "2",
            "--llm-out",
            str(llm_output),
        ]

        result = subprocess.run(
            runner_cmd,
            cwd=str(support_dir),
            text=True,
        )

        if result.returncode != 0:
            _update_scrape_status(
                False,
                "Pull Data failed while scraping/standardizing. "
                f"Error: {result.stderr.strip() or result.stdout.strip()}"
            )
            return

        if not llm_output.exists(): # pragma: no cover
            _update_scrape_status(
                False,
                f"Pull Data failed: expected LLM output was not created at {llm_output}"
            )
            return

        load_cmd = [
            sys.executable,
            str(load_path),
            "--file",
            str(llm_output),
        ]

        result = subprocess.run(
            load_cmd,
            cwd=str(SCRIPT_DIR),
            text=True,
        )

        if result.returncode != 0:
            _update_scrape_status(
                False,
                "Pull Data finished scraping/standardizing, but database load failed. "
                f"Error: {result.stderr.strip() or result.stdout.strip()}"
            )
            return

        _update_scrape_status(
            False,
            "Pull Data completed successfully. The database is now up to date."
        )

    except Exception as exc:
        _update_scrape_status(False, f"Pull Data failed: {exc}")

@app.route('/pull-data', methods=['POST'])
def pull_data():
    print("DEBUG: /pull-data route was hit", flush=True)
    if is_scrape_running():
        return "A Pull Data request is already running.", 409

    thread = threading.Thread(target=_run_scraper_and_load, daemon=True)
    thread.start()

    return redirect(url_for(
        'index',
        message='Pull Data started. The scraper is now running and will update the database when complete.'
    ))

@app.route('/update-analysis', methods=['POST'])
def update_analysis():
    if is_scrape_running():
        return "Cannot update analysis while Pull Data is running.", 409

    return redirect(url_for(
        'index',
        message='Analysis refreshed with the latest database content.'
    ))

@app.route('/')
def index():
    stats = {}
    db_error = None
    source = "database"

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            stats = get_stats_from_db(cur)
        conn.close()
    except Exception as exc:
        db_error = str(exc)
        source = "jsonl"
        rows = load_applicants_from_jsonl()
        stats = compute_stats_from_jsonl(rows)

    status_message = request.args.get("message")
    scrape_message = get_scrape_status_message()
    return render_template(
        'index.html',
        stats=stats,
        db_error=db_error,
        source=source,
        status_message=status_message,
        scrape_running=is_scrape_running(),
        scrape_message=scrape_message,
    )

@app.route('/analysis')
def analysis():
    return index()

if __name__ == '__main__': # pragma: no cover
    app.run(host='0.0.0.0', port=8000)

    