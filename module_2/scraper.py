# scraper.py

from urllib.request import Request, urlopen
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json
import re
import time
import os

CHECKPOINT_FILE = "checkpoint.json"
OUTPUT_FILE = "applicant_data.json"


BASE_URL = "https://www.thegradcafe.com"
USER_AGENT = "RP"


# -----------------------------
# ROBOTS CHECK
# -----------------------------
def check_robots():
    rp = robotparser.RobotFileParser()
    rp.set_url(urljoin(BASE_URL, "/robots.txt"))
    rp.read()

    allowed = rp.can_fetch(USER_AGENT, "/survey")

    print("robots.txt allows /survey:", allowed)

    if not allowed:
        raise Exception("Blocked by robots.txt")


# -----------------------------
# FETCH HTML
# -----------------------------
def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=20) as res:
                return res.read().decode("utf-8")

        except Exception as e:
            print(f"Retry {i+1} failed:", e)
            time.sleep(5)

    return None


# -----------------------------
# PARSE ROW TRIPLE
# -----------------------------
def parse_row(row):
    cells = row.find_all("td")
    text = row.get_text(" ", strip=True)
    raw_text = text
    if len(cells) < 4:
        return None

    # --------------------
    # SCHOOL
    # --------------------
    university = cells[0].get_text(" ", strip=True)

    # --------------------
    # PROGRAM + DEGREE
    # --------------------
    program_degree = cells[1].get_text(" ", strip=True)
    parts = program_degree.split()
    if len(parts) == 2:
        program_name = parts[0].strip()
        degree = parts[1].strip()
    else:
        program_name = program_degree
        degree = None

    # --------------------
    # DATE ADDED
    # --------------------
    date_added = cells[2].get_text(" ", strip=True)

    # semester_year will be extracted from combined text below (after detail page fetch)
    semester_year = None

    # --------------------
    # STATUS + GRE + GPA + ETC
    # --------------------
    status_block = cells[3].get_text(" ", strip=True)

    status = None
    if "Accepted" in status_block:
        status = "Accepted"
    elif "Rejected" in status_block:
        status = "Rejected"
    elif "Wait" in status_block:
        status = "Waitlisted"

    # --------------------
    # URL
    # --------------------
    link = row.find("a", href=True)
    url = BASE_URL + link["href"] if link else None

    # Try to fetch the detail page for this result (many fields like GPA appear there)
    detail_text = ""
    if url:
        detail_html = fetch(url)
        if detail_html:
            try:
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                detail_text = detail_soup.get_text(" ", strip=True)
            except Exception:
                detail_text = detail_html

            # Attempt structured extraction from the detail page (preferred)
            try:
                # Undergrad GPA
                if detail_soup:
                    dt = detail_soup.find(lambda t: t.name == 'dt' and 'Undergrad GPA' in t.get_text())
                    if dt:
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            ddval = dd.get_text(" ", strip=True)
                            if ddval and 'Not provided' not in ddval:
                                m = re.search(r'([0-9]+(?:\.[0-9]+)?)', ddval)
                                if m:
                                    try:
                                        gpa = float(m.group(1))
                                    except Exception:
                                        gpa = m.group(1)

                    # GRE Verbal
                    dtv = detail_soup.find(lambda t: t.name == 'dt' and 'GRE Verbal' in t.get_text())
                    if dtv:
                        ddv = dtv.find_next_sibling('dd')
                        if ddv:
                            v = re.search(r'(\d{2,3})', ddv.get_text(" ", strip=True))
                            if v:
                                gre_v = v.group(1)

                    # Analytical Writing
                    dta = detail_soup.find(lambda t: t.name == 'dt' and ('Analytical Writing' in t.get_text() or 'Writing' in t.get_text()))
                    if dta:
                        dda = dta.find_next_sibling('dd')
                        if dda:
                            aw = re.search(r'([0-9]+(?:\.[0-9]+)?)', dda.get_text(" ", strip=True))
                            if aw:
                                gre_aw = aw.group(1)
            except Exception:
                pass

    # Combine row text and detail page text for more reliable extraction
    search_text = f"{text} {detail_text}" if detail_text else text

    # --------------------
    # SEMESTER YEAR (extract after we have detail page)
    # --------------------
    semester_match = re.search(r"\b(Fall|Spring|Summer|Winter)\s+\d{4}\b", search_text, re.IGNORECASE)
    if semester_match:
        semester_year = semester_match.group(0)

    # --------------------
    # GRE / GPA extraction (more robust)
    # --------------------
    gpa = None
    # Look for explicit 'GPA' labels first (handles 'GPA: 3.85', 'GPA 3.85/4.00', etc.)
    gpa_match = re.search(r"GPA[:\s]*([0-9]+(?:\.[0-9]+)?)(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?", search_text, re.IGNORECASE)
    if gpa_match:
        try:
            gpa = float(gpa_match.group(1))
        except Exception:
            gpa = gpa_match.group(1)

    # If no explicit GPA label, try to capture common ratio formats like '3.85/4.0'
    if gpa is None:
        ratio_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*/\s*4(?:\.0+)?\b", search_text)
        if ratio_match:
            try:
                gpa = float(ratio_match.group(1))
            except Exception:
                gpa = ratio_match.group(1)

    # GRE Verbal (handles variants like 'GRE V: 159', 'GRE Verbal 159')
    gre_v = None
    gre_v_match = re.search(r"GRE\s*V[:\s]*?(\d{2,3})", search_text, re.IGNORECASE)
    if gre_v_match:
        gre_v = gre_v_match.group(1)

    # Try alternative label 'GRE Verbal'
    if gre_v is None:
        gre_v_match2 = re.search(r"GRE\s*(?:Verbal)[:\s]*?(\d{2,3})", search_text, re.IGNORECASE)
        if gre_v_match2:
            gre_v = gre_v_match2.group(1)

    # try generic 'V:' pattern (e.g., 'V: 160')
    if gre_v is None:
        v_generic = re.search(r"\bV[:\s]*(\d{2,3})\b", search_text)
        if v_generic:
            gre_v = v_generic.group(1)

    # GRE Analytical Writing (handles 'GRE AW: 4.0' and 'Analytical Writing')
    gre_aw = None
    gre_aw_match = re.search(r"GRE\s*AW[:\s]*?([0-9]+(?:\.[0-9]+)?)", search_text, re.IGNORECASE)
    if gre_aw_match:
        gre_aw = gre_aw_match.group(1)

    if gre_aw is None:
        aw_match2 = re.search(r"Analytical Writing[:\s]*([0-9]+(?:\.[0-9]+)?)", search_text, re.IGNORECASE)
        if aw_match2:
            gre_aw = aw_match2.group(1)

    # also accept 'AW: 4.0' shorthand
    if gre_aw is None:
        aw_generic = re.search(r"\bAW[:\s]*([0-9]+(?:\.[0-9]+)?)\b", search_text)
        if aw_generic:
            gre_aw = aw_generic.group(1)

    # capture GRE Quant and Verbal components if present
    gre_q = None
    q_match = re.search(r"\bQ[:\s]*(\d{2,3})\b", search_text)
    if q_match:
        gre_q = q_match.group(1)

    # --------------------
    # GRE total score (do not fabricate — only capture explicit totals)
    # --------------------
    gre_score = None
    # look for patterns like 'GRE General 320' or 'GRE: 320' or '320 (V: 160 Q: 160)'
    gre_total_match = re.search(r"\bGRE(?:\s*General)?[:\s]*?(\d{3})\b", search_text, re.IGNORECASE)
    if gre_total_match:
        gre_score = gre_total_match.group(1)
    else:
        # try pattern like '320 (V: 160' -> capture leading 3-digit number followed by parenthesis
        gre_alt = re.search(r"\b(\d{3})\s*\(.*?V[:\s]*(\d{2,3})", search_text)
        if gre_alt:
            gre_score = gre_alt.group(1)

    # If total not provided but V and Q components exist, compute total
    try:
        if gre_score is None:
            if gre_v and gre_q:
                gre_score = str(int(gre_v) + int(gre_q))
    except Exception:
        pass

    gre_score = None  # do NOT fabricate total score

    # --------------------
    # DATES
    # --------------------
    acc_date = re.search(r"Accepted on ([A-Za-z]{3}\s+\d{1,2})", status_block)
    rej_date = re.search(r"Rejected on ([A-Za-z]{3}\s+\d{1,2})", status_block)

    # --------------------
    # TYPE
    # --------------------
    applicant_type = None
    if "International" in status_block:
        applicant_type = "International"
    elif "American" in status_block:
        applicant_type = "American"
    elif "Other" in status_block:
        applicant_type = "Other"

    return {
        "university": university,
        "program_name": program_name,
        "degree": degree,
        "date_added": date_added,
        "url": url,
        "applicant_status": status,
        "acceptance_date": acc_date.group(1) if acc_date else None,
        "rejection_date": rej_date.group(1) if rej_date else None,
        "semester_year": semester_year,
        "international": applicant_type,
        "gre_score": gre_score,
        "gre_v_score": gre_v,
        "gre_aw": gre_aw,
        "gpa": gpa,
        "comments": None,
        "raw_text": status_block
    }

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"page": 1, "data": []}

def save_checkpoint(page, data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"page": page, "data": data}, f)
        
# -----------------------------
# SCRAPER CORE
# -----------------------------
def scrape_data(max_pages=1000):

    check_robots()

    results = []

    for page in range(1, max_pages + 1):

        url = f"{BASE_URL}/survey?page={page}"

        print(f"Scraping page {page}")

        html = fetch(url)
        if html is None:
            print("Skipping page", page)
            continue

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tr:has(td)")  # skip header

        for row in rows:
            record = parse_row(row)
            if record:
                results.append(record)

        print("Total collected:", len(results))

        # polite scraping
        time.sleep(3)

        if len(results) >= 30000:
            print("Reached 30,000 records")
            break

        if "No results found" in html:
            print("Stopping - no more data")
            break

        try:

            if html is None:
                print("Skipping page due to repeated failure:", page)
                continue

            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(" ", strip=True).lower()

            if "cloudflare" in page_text and "attention required" in page_text:
                print("Possible block detected. Retrying page...")

                time.sleep(10)

                if html is None:
                    print("Confirmed blocked after retry. Stopping.")
                    break

                soup = BeautifulSoup(html, "html.parser")
                page_text = soup.get_text(" ", strip=True).lower()

                if "cloudflare" in page_text and "attention required" in page_text:
                    print("Still blocked after retry. Stopping.")
                    break

        except Exception as e:
            print("Request failed:", e)
            time.sleep(5)
            continue

    return results


# -----------------------------
# SAVE / LOAD
# -----------------------------
def save_data(data, filename="applicant_data.json"):
    # Map records to requested output format and replace None with 'none'
    out = []
    for rec in data:
        def val(key):
            v = rec.get(key)
            return "none" if v is None else v

        mapped = {
            "Program Name": val("program_name"),
            "University": val("university"),
            "Comments": val("comments"),
            "Date of Information Added to Grad Cafe": val("date_added"),
            "URL": val("url"),
            "Applicant Status": val("applicant_status"),
            "Accepted": val("acceptance_date"),
            "Rejected": val("rejection_date"),
            "Semester and Year of Program Start": val("semester_year"),
            "International or American Student": val("international"),
            "GRE Score": val("gre_score"),
            "GRE V Score": val("gre_v_score"),
            "Masters or PhD": val("degree"),
            "GPA": val("gpa"),
            "GRE AW": val("gre_aw"),
        }

        out.append(mapped)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def load_data(filename="applicant_data.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    data = scrape_data(max_pages=5)

    out_path = os.path.join(os.path.dirname(__file__), "applicant_data.json")
    save_data(data, filename=out_path)

    print("Saved:", len(data), "records ->", out_path)