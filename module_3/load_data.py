import argparse
import json
import os
import datetime
from typing import Any, Dict, Optional

import psycopg

# parsing date/time data fields
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

# cleaning numeric fields (GPA, GRE, etc.) to replace NULL and None.
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

# loading data from JSONL, mapping to standardized fields, and inserting into Postgres with upsert logic.
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


# Main function to load data from JSONL, map fields, and insert into Postgres with upsert logic. Also includes example queries to demonstrate loaded data.
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="small_output.json", help="Input JSONL file (list of rows)")
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
        rows = [json.loads(line) for line in f]

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
# listing all rows to be inserted/updated and then performing queries to demonstrate the loaded data.
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

        # 2. What Percentage of entries are from international students?
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE us_or_international = %s;
                """, ('International',))
        international_count = cur.fetchone()[0]

        total_count = count_result[0]
        if total_count > 0:
            percentage = (international_count / total_count) * 100
            print(f"Percentage of international students: {percentage:.2f}%")
        else:
            print("2. No entries found.")

        # 3. What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics.
        cur.execute("""
                    SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM applicants
                    WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;
                """)
        avg_result = cur.fetchone()
        print(f"Average GPA: {avg_result[0]:.2f}, Average GRE: {avg_result[1]:.2f}, Average GRE V: {avg_result[2]:.2f}, Average GRE AW: {avg_result[3]:.2f}")

        # 4. What is the average GPA of American students in the Fall 2026 term.
        cur.execute("""
                    SELECT AVG(gpa) FROM applicants
                    WHERE us_or_international = %s AND term = %s AND gpa IS NOT NULL;
                """, ('American', 'Fall 2026'))
        avg_gpa_american_fall2026 = cur.fetchone()[0]
        if avg_gpa_american_fall2026 is not None:
            print(f"Average GPA of American students in Fall 2026: {avg_gpa_american_fall2026:.2f}")
        else:
            print("4. No entries found for American students in Fall 2026 with GPA data.")

        # 5. What percent of entries for Fall 2026 are Acceptances
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE term = %s AND status = %s;
                """, ('Fall 2026', 'Accepted'))
        total_fall2026 = cur.fetchone()[0]
        if total_fall2026 > 0:
            acceptance_percentage = (count_result[0] / total_fall2026) * 100
            print(f"Percentage of acceptances for Fall 2026: {acceptance_percentage:.2f}%")
        else:
            print("5. No entries found for Fall 2026.")

        # 6. What is the average GPA of applicants who applied for Fall 2026 who are Acceptances.
        cur.execute("""
                    SELECT AVG(gpa) FROM applicants
                    WHERE term = %s AND status = %s AND gpa IS NOT NULL;
                """, ('Fall 2026', 'Accepted'))
        avg_gpa_accepted_fall2026 = cur.fetchone()[0]
        if avg_gpa_accepted_fall2026 is not None:
            print(f"Average GPA of accepted applicants for Fall 2026: {avg_gpa_accepted_fall2026:.2f}")
        else:
            print("6. No entries found for accepted applicants for Fall 2026 with GPA data.")

        # 7. How many entries are from applicants who applied to JHU for a masters degree in Computer Science
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE program ILIKE %s AND degree ILIKE %s;
                """, ('%Johns Hopkins University%', '%Masters%'))
        jhu_masters_count = cur.fetchone()[0]
        print(f"Number of applicants who applied to JHU for a masters degree in Computer Science: {jhu_masters_count}")

        # 8. How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Standford University, or Carnegie Mellon University for a PhD in Computer Science.
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE term ILIKE %s AND status ILIKE %s AND program ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND degree ILIKE %s;
                """, ('%2026%', '%Accepted%', '%Georgetown University%', '%MIT%', '%Stanford University%', '%Carnegie Mellon University%', '%PhD%'))
        top_universities_phd_accepted_2026_count = cur.fetchone()[0]
        print(f"Number of acceptances in 2026 from applicants who applied to Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science: {top_universities_phd_accepted_2026_count}")

        # 9. Does the numbers for 8. change if using LLM Generated Fields (rather than the original program and degree fields).
        cur.execute("""
                    SELECT COUNT(*) FROM applicants
                    WHERE term ILIKE %s AND status ILIKE %s AND llm_generated_university ILIKE ANY (ARRAY[%s, %s, %s, %s]) AND llm_generated_program ILIKE %s;
                """, ('%2026%', '%Accepted%', '%Georgetown University%', '%MIT%', '%Stanford University%', '%Carnegie Mellon University%', '%PhD%'))
        top_universities_phd_accepted_2026_llm_count = cur.fetchone()[0]
        print(f"Number of acceptances in 2026 from applicants who applied to Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science using LLM Generated Fields: {top_universities_phd_accepted_2026_llm_count}")



    conn.commit()
    conn.close()

    print(f"Loaded {len(rows)} rows into applicants table.")


if __name__ == "__main__":
    main()
