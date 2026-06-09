import argparse
import json
import os
import datetime
from typing import Any, Dict, Optional

import psycopg


def parse_date(s: Optional[str]) -> Optional[datetime.date]:
    if not s:
        return None
    s = s.strip()
    if s.lower() in ("none", "n/a", "na"):
        return None
    # Try common formats
    fmts = ["%b %d, %Y", "%b %d", "%Y-%m-%d", "%m/%d/%Y"]
    for fmt in fmts:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            if fmt == "%b %d":
                # assume current year if year missing
                dt = dt.replace(year=datetime.date.today().year)
            return dt.date()
        except Exception:
            continue
    # Last resort: try parsing trailing year
    try:
        parts = s.split()
        for p in parts:
            if p.isdigit() and len(p) == 4:
                try:
                    return datetime.datetime.strptime(p + "-01-01", "%Y-%m-%d").date()
                except Exception:
                    pass
    except Exception:
        pass
    return None


def clean_number(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s.lower() in ("none", "n/a", "na", ""):
        return None
    try:
        return float(s)
    except Exception:
        # try to extract numeric part
        import re

        m = re.search(r"[0-9]+(?:\.[0-9]+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None


def map_row(applicant: Dict[str, Any]) -> Dict[str, Any]:
    prog = applicant.get("Program Name") or applicant.get("program") or applicant.get("program_name")
    comments = applicant.get("Comments")
    date_added = parse_date(applicant.get("Date of Information Added to Grad Cafe") or applicant.get("date_added"))
    url = applicant.get("URL") or applicant.get("url")
    status = applicant.get("Applicant Status") or applicant.get("applicant_status")
    term = applicant.get("Semester and Year of Program Start") or applicant.get("semester_year")
    us_or_international = applicant.get("International or American Student")
    gpa = clean_number(applicant.get("GPA"))
    gre = clean_number(applicant.get("GRE Score"))
    gre_v = clean_number(applicant.get("GRE V Score"))
    gre_aw = clean_number(applicant.get("GRE AW"))
    degree = applicant.get("Masters or PhD")
    llm_prog = applicant.get("llm-generated-program") or applicant.get("llm_generated_program")
    llm_uni = applicant.get("llm-generated-university") or applicant.get("llm_generated_university")

    return {
        "program": prog,
        "comments": None if (comments is None or str(comments).strip().lower() in ("none", "")) else comments,
        "date_added": date_added,
        "url": url,
        "status": status,
        "term": term,
        "us_or_international": us_or_international,
        "gpa": gpa,
        "gre": gre,
        "gre_v": gre_v,
        "gre_aw": gre_aw,
        "degree": degree,
        "llm_generated_program": llm_prog,
        "llm_generated_university": llm_uni,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="small_output.json", help="Input JSON file (list of rows)")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit to number of rows to load")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    infile = args.file
    if not os.path.isabs(infile):
        candidate = os.path.join(script_dir, infile)
        if os.path.exists(candidate):
            infile = candidate
        else:
            infile = os.path.join(os.getcwd(), infile)

    with open(infile, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if args.limit:
        rows = rows[: args.limit]

    # Default local Postgres connection for one-command execution
    DB_NAME = os.getenv("PGDATABASE", "studentCourses")
    DB_USER = os.getenv("PGUSER", "postgres")
    DB_PASS = os.getenv("PGPASSWORD", "postgres")
    DB_HOST = os.getenv("PGHOST", "localhost")
    DB_PORT = os.getenv("PGPORT", "5432")

    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )

    create_sql = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id SERIAL PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT UNIQUE,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa DOUBLE PRECISION,
        gre DOUBLE PRECISION,
        gre_v DOUBLE PRECISION,
        gre_aw DOUBLE PRECISION,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """

    upsert_sql = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term, us_or_international, gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university
    ) VALUES (
        %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s, %(term)s, %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s, %(degree)s, %(llm_generated_program)s, %(llm_generated_university)s
    ) ON CONFLICT (url) DO UPDATE SET
        program = EXCLUDED.program,
        comments = EXCLUDED.comments,
        date_added = EXCLUDED.date_added,
        status = EXCLUDED.status,
        term = EXCLUDED.term,
        us_or_international = EXCLUDED.us_or_international,
        gpa = EXCLUDED.gpa,
        gre = EXCLUDED.gre,
        gre_v = EXCLUDED.gre_v,
        gre_aw = EXCLUDED.gre_aw,
        degree = EXCLUDED.degree,
        llm_generated_program = EXCLUDED.llm_generated_program,
        llm_generated_university = EXCLUDED.llm_generated_university;
    """

    with conn.cursor() as cur:
        cur.execute(create_sql)
        cur.execute(
            "DELETE FROM applicants a USING applicants b WHERE a.url = b.url AND a.ctid < b.ctid;"
        )
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS applicants_url_idx ON applicants (url);")

        for raw in rows:
            mapped = map_row(raw)
            # psycopg accepts python date objects directly
            cur.execute(upsert_sql, mapped)

        # Outputing first row to see an example of the loaded data
        cur.execute("SELECT * FROM applicants LIMIT 1;")
        rowsprint = cur.fetchall()
        for row in rowsprint:
            print(row)
        
        # 1. How many entries do I have in my databse who have applied for Fall 2026 and got accepted.
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE term = %s AND status = %s;
                """, ('Fall 2026', 'Accepted'))
        count_result = cur.fetchone()
        print(f"Number of accepted applicants for Fall 2026: {count_result[0]}")

    conn.commit()
    conn.close()

    print(f"Loaded {len(rows)} rows into applicants table.")


if __name__ == "__main__":
    main()
