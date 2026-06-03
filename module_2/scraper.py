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
def parse_triplet(summary, metadata, comments):

    summary_text = summary.get_text(" ", strip=True)
    metadata_text = metadata.get_text(" ", strip=True)
    comments_text = comments.get_text(" ", strip=True)

    # ---- university + program extraction
    parts = summary_text.split()

    university = " ".join(parts[:-3]) if len(parts) > 3 else None
    program_name = parts[-3] if len(parts) >= 3 else None
    degree = parts[-2] if len(parts) >= 2 else None

    # ---- status
    status = None
    if "Accepted" in summary_text:
        status = "Accepted"
    elif "Rejected" in summary_text:
        status = "Rejected"
    elif "Wait" in summary_text:
        status = "Waitlisted"

    # ---- metadata extraction
    gpa = re.search(r"GPA\s+([0-9.]+)", metadata_text)
    gpa = gpa.group(1) if gpa else None

    gre_v = re.search(r"GRE V\s+(\d+)", metadata_text)
    gre_v = gre_v.group(1) if gre_v else None

    gre_aw = re.search(r"GRE AW\s+([0-9.]+)", metadata_text)
    gre_aw = gre_aw.group(1) if gre_aw else None

    semester = re.search(r"(Fall|Spring)\s+\d{4}", metadata_text)
    semester = semester.group(0) if semester else None

    applicant_type = None
    if "International" in metadata_text:
        applicant_type = "International"
    elif "American" in metadata_text:
        applicant_type = "American"
    elif "Other" in metadata_text:
        applicant_type = "Other"

    return {
        "program_name": program_name,
        "university": university,
        "comments": comments_text,
        "date_added": None,
        "url": None,
        "applicant_status": status,
        "acceptance_date": None,
        "rejection_date": None,
        "semester_year": semester,
        "international": applicant_type,
        "gre_score": None,
        "gre_v_score": gre_v,
        "degree": degree,
        "gpa": gpa,
        "gre_aw": gre_aw,
        "raw_text": summary_text + " | " + metadata_text + " | " + comments_text
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
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all("tr")[1:]  # skip header

        for i in range(0, len(rows), 3):

            if i + 2 >= len(rows):
                break

            record = parse_triplet(
                rows[i],
                rows[i + 1],
                rows[i + 2]
            )

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
            html = fetch(url)

            if html is None:
                print("Skipping page due to repeated failure:", page)
                continue

            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(" ", strip=True).lower()

            if "cloudflare" in page_text and "attention required" in page_text:
                print("Possible block detected. Retrying page...")

                time.sleep(10)

                html = fetch(url)

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
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_data(filename="applicant_data.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    data = scrape_data(max_pages=50)

    save_data(data)

    print("Saved:", len(data), "records")