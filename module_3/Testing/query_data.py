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

app = Flask(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

scrape_status = {
    "running": False,
    "message": None,
    "started_at": None,
    "finished_at": None,
}
status_lock = threading.Lock()


def get_db_connection():
    dbname = os.getenv("PGDATABASE", os.getenv("DB_NAME", "studentCourses"))
    user = os.getenv("PGUSER", os.getenv("DB_USER", "postgres"))
    password = os.getenv("PGPASSWORD", os.getenv("DB_PASSWORD", "postgres"))
    host = os.getenv("PGHOST", os.getenv("DB_HOST", "localhost"))
    port = os.getenv("PGPORT", os.getenv("DB_PORT", "5432"))

    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def is_scrape_running():
    with status_lock:
        return scrape_status["running"]


def get_scrape_status_message():
    with status_lock:
        if scrape_status["running"]:
            return (
                f"Pull Data is running since {scrape_status['started_at']:%Y-%m-%d %H:%M:%S}. "
                "Analysis will refresh once the current data update completes."
            )
        if scrape_status["finished_at"]:
            return scrape_status["message"]
        return scrape_status["message"]


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


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def load_applicants_from_json(filename="applicant_data_llm_M3.jsonl"):
    path = SCRIPT_DIR / filename
    if not path.exists():
        path = Path(os.getcwd()) / filename

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw_rows = json.load(f)

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
            "degree": normalize_text(row.get("Masters or PhD") or row.get("degree")),
            "llm_generated_program": normalize_text(row.get("llm-generated-program") or row.get("llm_generated_program")),
            "llm_generated_university": normalize_text(row.get("llm-generated-university") or row.get("llm_generated_university")),
        })

    return applicants


def compute_stats_from_json(applicants):
    accepted_count = sum(
        1
        for row in applicants
        if row["term"] == "Fall 2026" and row["status"] == "Accepted"
    )
    international_count = sum(
        1 for row in applicants if row["us_or_international"] == "International"
    )
    total_count = accepted_count
    international_pct = (international_count / total_count * 100) if total_count > 0 else None

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

    american_fall2026 = [
        row["gpa"]
        for row in applicants
        if row["us_or_international"] == "American" and row["term"] == "Fall 2026" and row["gpa"] is not None
    ]
    avg_gpa_american_fall2026 = (
        sum(american_fall2026) / len(american_fall2026) if american_fall2026 else None
    )

    total_fall2026 = accepted_count
    acceptance_percentage = (accepted_count / total_fall2026 * 100) if total_fall2026 > 0 else None

    accepted_fall2026_gpas = [
        row["gpa"]
        for row in applicants
        if row["term"] == "Fall 2026" and row["status"] == "Accepted" and row["gpa"] is not None
    ]
    avg_gpa_accepted_fall2026 = (
        sum(accepted_fall2026_gpas) / len(accepted_fall2026_gpas) if accepted_fall2026_gpas else None
    )

    jhu_masters_count = sum(
        1
        for row in applicants
        if "%johns hopkins university%" in f"%{row['program'].lower()}%" and "%masters%" in f"%{row['degree'].lower()}%"
    )

    top_universities = [
        "%georgetown university%",
        "%mit%",
        "%stanford university%",
        "%carnegie mellon university%",
    ]
    top_universities_phd_accepted_2026_count = sum(
        1
        for row in applicants
        if "%2022%" in f"%{row['term'].lower()}%"
        and "%accepted%" in f"%{row['status'].lower()}%"
        and any(univ.strip('%') in row["program"].lower() for univ in top_universities)
        and "%phd%" in row["degree"].lower()
    )
    top_universities_phd_accepted_2026_llm_count = sum(
        1
        for row in applicants
        if "%2026%" in f"%{row['term'].lower()}%"
        and "%accepted%" in f"%{row['status'].lower()}%"
        and any(univ.strip('%') in row["llm_generated_university"].lower() for univ in top_universities)
        and "%phd%" in row["llm_generated_program"].lower()
    )

    return {
        "accepted_fall2026_count": accepted_count,
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
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = %s AND status = %s;",
        ("Fall 2026", "Accepted"),
    )
    accepted_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE us_or_international = %s;",
        ("International",),
    )
    international_count = cur.fetchone()[0]

    total_count = accepted_count
    international_pct = (international_count / total_count * 100) if total_count > 0 else None

    cur.execute(
        "SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM applicants WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;"
    )
    avg_result = cur.fetchone() or (None, None, None, None)

    cur.execute(
        "SELECT AVG(gpa) FROM applicants WHERE us_or_international = %s AND term = %s AND gpa IS NOT NULL;",
        ("American", "Fall 2026"),
    )
    avg_gpa_american_fall2026 = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = %s AND status = %s;",
        ("Fall 2026", "Accepted"),
    )
    total_fall2026 = cur.fetchone()[0]
    acceptance_percentage = (accepted_count / total_fall2026 * 100) if total_fall2026 > 0 else None

    cur.execute(
        "SELECT AVG(gpa) FROM applicants WHERE term = %s AND status = %s AND gpa IS NOT NULL;",
        ("Fall 2026", "Accepted"),
    )
    avg_gpa_accepted_fall2026 = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE program ILIKE %s AND degree ILIKE %s;",
        ("%Johns Hopkins University%", "%Masters%"),
    )
    jhu_masters_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term ILIKE %s AND status ILIKE %s AND program ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND degree ILIKE %s;",
        ("%2026%", "%Accepted%", "%Georgetown University%", "%MIT%", "%Stanford University%", "%Carnegie Mellon University%", "%PhD%"),
    )
    top_universities_phd_accepted_2026_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term ILIKE %s AND status ILIKE %s AND llm_generated_university ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND llm_generated_program ILIKE %s;",
        ("%2026%", "%Accepted%", "%Georgetown University%", "%MIT%", "%Stanford University%", "%Carnegie Mellon University%", "%PhD%"),
    )
    top_universities_phd_accepted_2026_llm_count = cur.fetchone()[0]

    return {
        "accepted_fall2026_count": accepted_count,
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


def _run_scraper_and_load():
    _update_scrape_status(True, "Pull Data started.")
    scraper_path = REPO_ROOT / "module_2" / "scraper.py"
    load_path = SCRIPT_DIR / "load_data.py"
    output_json = REPO_ROOT / "module_2" / "applicant_data.json"
    checkpoint_json = REPO_ROOT / "module_2" / "checkpoint.json"

    try:
        scraper_cmd = [
            sys.executable,
            str(scraper_path),
            "--resume",
            "--out",
            str(output_json),
            "--checkpoint",
            str(checkpoint_json),
        ]
        result = subprocess.run(
            scraper_cmd,
            cwd=str(REPO_ROOT / "module_2"),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            message = (
                "Pull Data failed while scraping. "
                f"Error: {result.stderr.strip() or result.stdout.strip()}"
            )
            _update_scrape_status(False, message)
            return

        load_cmd = [
            sys.executable,
            str(load_path),
            "--file",
            str(output_json),
        ]
        result = subprocess.run(
            load_cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            message = (
                "Pull Data finished scraping, but database load failed. "
                f"Error: {result.stderr.strip() or result.stdout.strip()}"
            )
            _update_scrape_status(False, message)
            return

        _update_scrape_status(False, "Pull Data completed successfully. The database is now up to date.")
    except Exception as exc:
        _update_scrape_status(False, f"Pull Data failed: {exc}")


@app.route('/pull-data', methods=['POST'])
def pull_data():
    if is_scrape_running():
        return redirect(url_for('index', message='A Pull Data request is already running. Please wait until it finishes.'))

    thread = threading.Thread(target=_run_scraper_and_load, daemon=True)
    thread.start()
    return redirect(url_for('index', message='Pull Data started. The scraper is now running and will update the database when complete.'))


@app.route('/update-analysis', methods=['POST'])
def update_analysis():
    if is_scrape_running():
        return redirect(url_for('index', message='Cannot update analysis while Pull Data is running. Please wait.'))
    return redirect(url_for('index', message='Analysis refreshed with the latest database content.'))


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
        source = "json"
        rows = load_applicants_from_json()
        stats = compute_stats_from_json(rows)

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

    