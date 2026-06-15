import sys
from pathlib import Path
import pytest
import psycopg

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from load_data import create_applicants_table, insert_applicants, get_applicant_count

pytestmark = pytest.mark.db


@pytest.fixture
def db_conn():
    conn = psycopg.connect(
        dbname="studentCourses",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432",
    )

    with conn.cursor() as cur:
        create_applicants_table(cur)
        cur.execute("DELETE FROM applicants;")
        conn.commit()

    yield conn

    with conn.cursor() as cur:
        cur.execute("DELETE FROM applicants;")
        conn.commit()

    conn.close()


def sample_row():
    return {
        "Program Name": "Computer Science",
        "University": "Johns Hopkins University",
        "Comments": "none",
        "Date of Information Added to Grad Cafe": "Jun 09, 2026",
        "URL": "https://example.com/test-row-1",
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
    }

# Database writes - test insert on pull
def test_insert_on_pull_adds_rows(db_conn):
    with db_conn.cursor() as cur:
        assert get_applicant_count(cur) == 0

        insert_applicants(cur, [sample_row()])
        db_conn.commit()

        assert get_applicant_count(cur) == 1


def test_insert_required_fields_not_null(db_conn):
    with db_conn.cursor() as cur:
        insert_applicants(cur, [sample_row()])
        db_conn.commit()

        cur.execute("""
            SELECT program, university, url, status
            FROM applicants
            WHERE url = %s;
        """, ("https://example.com/test-row-1",))

        row = cur.fetchone()

        assert row[0] is not None
        assert row[1] is not None
        assert row[2] is not None
        assert row[3] is not None


def test_duplicate_rows_do_not_create_duplicates(db_conn):
    row = sample_row()

    with db_conn.cursor() as cur:
        insert_applicants(cur, [row])
        insert_applicants(cur, [row])
        db_conn.commit()

        assert get_applicant_count(cur) == 1


def test_simple_query_returns_expected_keys(db_conn):
    with db_conn.cursor() as cur:
        insert_applicants(cur, [sample_row()])
        db_conn.commit()

        cur.execute("""
            SELECT program, university, status, term, degree
            FROM applicants
            LIMIT 1;
        """)

        result = cur.fetchone()

        data = {
            "program": result[0],
            "university": result[1],
            "status": result[2],
            "term": result[3],
            "degree": result[4],
        }

        assert set(data.keys()) == {
            "program",
            "university",
            "status",
            "term",
            "degree",
        }