# handling all edge cases (helpers) 

import json
import subprocess
from unittest.mock import patch
import sys
from pathlib import Path
import datetime
import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import load_data
import query_data

pytestmark = pytest.mark.helpers


def test_parse_date_extra_formats():
    assert load_data.parse_date("2026-06-09") == datetime.date(2026, 6, 9)
    assert load_data.parse_date("06/09/2026") == datetime.date(2026, 6, 9)
    assert load_data.parse_date("Fall 2026") == datetime.date(2026, 1, 1)
    assert load_data.parse_date("not a date") is None


def test_clean_number_extra_cases():
    assert load_data.clean_number("GPA 3.75") == 3.75
    assert load_data.clean_number("abc") is None


def test_get_first_applicant_dict_none():
    class Cur:
        def execute(self, sql):
            pass
        def fetchone(self):
            return None

    assert load_data.get_first_applicant_dict(Cur()) is None

def test_get_first_applicant_dict_returns_dict():
    class Cur:
        def execute(self, sql):
            pass

        def fetchone(self):
            return (
                "Computer Science",
                "Johns Hopkins University",
                "https://example.com",
                "Accepted",
                "Fall 2026",
                "Masters",
            )

    result = load_data.get_first_applicant_dict(Cur())

    assert result == {
        "program": "Computer Science",
        "university": "Johns Hopkins University",
        "url": "https://example.com",
        "status": "Accepted",
        "term": "Fall 2026",
        "degree": "Masters",
    }

def test_query_parse_number_and_normalize():
    assert query_data.parse_number("GRE 165") == 165.0
    assert query_data.parse_number("bad") is None
    assert query_data.normalize_text(None) == ""
    assert query_data.normalize_text("  hello ") == "hello"


def test_status_message_branches():
    query_data._update_scrape_status(True, "running")
    assert "Pull Data is running" in query_data.get_scrape_status_message()

    query_data._update_scrape_status(False, "done")
    assert query_data.get_scrape_status_message() == "done"


def test_compute_stats_from_jsonl_empty():
    stats = query_data.compute_stats_from_jsonl([])
    assert stats["fall2026_entries_count"] == 0
    assert stats["international_pct"] is None

def test_load_applicants_from_jsonl_missing_file():
    assert query_data.load_applicants_from_jsonl("does_not_exist.jsonl") == []


def test_load_applicants_from_jsonl_reads_file(tmp_path):
    data_file = tmp_path / "sample.jsonl"
    data_file.write_text(json.dumps({
        "Program Name": "Computer Science",
        "University": "Johns Hopkins University",
        "Applicant Status": "Accepted",
        "Semester and Year of Program Start": "Fall 2026",
        "International or American Student": "American",
        "GPA": "3.9",
        "GRE Score": "165",
        "GRE V Score": "160",
        "GRE AW": "4.5",
        "Masters or PhD": "Masters",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Johns Hopkins University",
    }) + "\n")

    rows = query_data.load_applicants_from_jsonl(str(data_file))

    assert len(rows) == 1
    assert rows[0]["program"] == "Computer Science"
    assert rows[0]["university"] == "Johns Hopkins University"
    assert rows[0]["gpa"] == 3.9


def test_run_scraper_failure_branch():
    failed = subprocess.CompletedProcess([], 1, stdout="", stderr="scraper failed")

    with patch.object(query_data.subprocess, "run", return_value=failed):
        query_data._run_scraper_and_load()

    assert query_data.scrape_status["running"] is False
    assert "Pull Data failed while scraping" in query_data.scrape_status["message"]


def test_run_loader_failure_branch():
    success = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
    failed = subprocess.CompletedProcess([], 1, stdout="", stderr="load failed")

    with patch.object(query_data.subprocess, "run", side_effect=[success, failed]):
        query_data._run_scraper_and_load()

    assert query_data.scrape_status["running"] is False
    assert "database load failed" in query_data.scrape_status["message"]


def test_run_scraper_success_branch():
    success = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")

    with patch.object(query_data.subprocess, "run", return_value=success):
        query_data._run_scraper_and_load()

    assert query_data.scrape_status["running"] is False
    assert "completed successfully" in query_data.scrape_status["message"]


def test_run_scraper_exception_branch():
    with patch.object(query_data.subprocess, "run", side_effect=Exception("boom")):
        query_data._run_scraper_and_load()

    assert query_data.scrape_status["running"] is False
    assert "Pull Data failed: boom" in query_data.scrape_status["message"]

def test_get_db_connection_missing_config(monkeypatch):
    monkeypatch.delenv("PGDATABASE", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    try:
        query_data.get_db_connection()
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Missing database configuration" in str(exc)

def test_query_parse_number_edge_cases():
    assert query_data.parse_number(None) is None
    assert query_data.parse_number(10) == 10.0
    assert query_data.parse_number("none") is None
    assert query_data.parse_number("n/a") is None
    assert query_data.parse_number("") is None

def test_index_falls_back_to_jsonl_when_db_fails():
    sample_rows = [
        {
            "program": "Computer Science",
            "term": "Fall 2026",
            "status": "Accepted",
            "us_or_international": "International",
            "gpa": 3.9,
            "gre": 165.0,
            "gre_v": 160.0,
            "gre_aw": 4.5,
            "university": "Johns Hopkins University",
            "degree": "Masters",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
        }
    ]

    with query_data.app.test_client() as client:
        with patch.object(query_data, "get_db_connection", side_effect=Exception("db down")), \
             patch.object(query_data, "load_applicants_from_jsonl", return_value=sample_rows):
            response = client.get("/analysis")

    assert response.status_code == 200
    page = response.data.decode("utf-8")
    assert "Database unavailable" in page
    assert "db down" in page

def test_load_parse_date_none_and_short_month_day():
    assert load_data.parse_date(None) is None
    assert load_data.parse_date("none") is None

    result = load_data.parse_date("Jun 09")
    assert result.month == 6
    assert result.day == 9


def test_load_parse_date_trailing_year_bad_parse():
    assert load_data.parse_date("Submitted 2026") == datetime.date(2026, 1, 1)


def test_load_clean_number_none_int_and_blank():
    assert load_data.clean_number(None) is None
    assert load_data.clean_number(165) == 165.0
    assert load_data.clean_number("") is None
    assert load_data.clean_number("none") is None


def test_load_clean_number_regex_failure_branch():
    assert load_data.clean_number("score abc") is None

def test_parse_date_trailing_year_inner_exception():
    assert load_data.parse_date("Submitted 0000") is None