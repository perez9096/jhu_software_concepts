import sys
from pathlib import Path
from unittest.mock import patch
import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import query_data
from load_data import create_applicants_table, insert_applicants, get_applicant_count

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    query_data.app.config.update(TESTING=True)

    with query_data.app.test_client() as client:
        yield client


@pytest.fixture
def fake_rows():
    return [
        {
            "Program Name": "Computer Science",
            "University": "Johns Hopkins University",
            "URL": "https://example.com/1",
            "Applicant Status": "Accepted",
            "Semester and Year of Program Start": "Fall 2026",
            "International or American Student": "American",
            "GPA": 3.9,
            "GRE Score": "165",
            "GRE V Score": "160",
            "GRE AW": "4.5",
            "Masters or PhD": "Masters",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Johns Hopkins University",
        },
        {
            "Program Name": "Computer Science",
            "University": "Stanford University",
            "URL": "https://example.com/2",
            "Applicant Status": "Rejected",
            "Semester and Year of Program Start": "Fall 2026",
            "International or American Student": "International",
            "GPA": 3.7,
            "GRE Score": "160",
            "GRE V Score": "155",
            "GRE AW": "4.0",
            "Masters or PhD": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Stanford University",
        },
    ]

def fake_pull_data(rows):
    conn = query_data.get_db_connection()

    with conn.cursor() as cur:
        create_applicants_table(cur)
        insert_applicants(cur, rows)

    conn.commit()
    conn.close()

def set_test_db_env(monkeypatch):
    monkeypatch.setenv("PGDATABASE", "studentCourses")
    monkeypatch.setenv("PGUSER", "postgres")
    monkeypatch.setenv("PGPASSWORD", "postgres")
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")

def clear_db():
    conn = query_data.get_db_connection()

    with conn.cursor() as cur:
        create_applicants_table(cur)
        cur.execute("DELETE FROM applicants;")

    conn.commit()
    conn.close()


def test_end_to_end_pull_update_render(client, fake_rows, monkeypatch):
    set_test_db_env(monkeypatch)
    clear_db()

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self.target = target

        def start(self):
            self.target()

    with patch.object(
        query_data,
        "_run_scraper_and_load",
        side_effect=lambda: fake_pull_data(fake_rows),
    ), patch.object(query_data.threading, "Thread", ImmediateThread):
        response = client.post("/pull-data", follow_redirects=True)

    assert response.status_code == 200

    conn = query_data.get_db_connection()
    with conn.cursor() as cur:
        assert get_applicant_count(cur) == 2
    conn.close()

    response = client.post("/update-analysis", follow_redirects=True)
    assert response.status_code == 200

    response = client.get("/analysis")
    assert response.status_code == 200

    page = response.data.decode("utf-8")

    assert "Answer:" in page
    assert "Analysis" in page
    assert "Pull Data" in page
    assert "Update Analysis" in page
    assert ".00%" in page or ".50%" in page


def test_multiple_pulls_do_not_duplicate_rows(client, fake_rows, monkeypatch):
    set_test_db_env(monkeypatch)
    clear_db()

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self.target = target

        def start(self):
            self.target()

    with patch.object(
        query_data,
        "_run_scraper_and_load",
        side_effect=lambda: fake_pull_data(fake_rows),
    ), patch.object(query_data.threading, "Thread", ImmediateThread):
        response1 = client.post("/pull-data", follow_redirects=True)
        response2 = client.post("/pull-data", follow_redirects=True)

    assert response1.status_code == 200
    assert response2.status_code == 200

    conn = query_data.get_db_connection()
    with conn.cursor() as cur:
        assert get_applicant_count(cur) == 2
    conn.close()