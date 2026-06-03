from urllib.request import Request, urlopen
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json
import re

BASE_URL = "https://www.thegradcafe.com/"
SURVEY_URL = "https://www.thegradcafe.com/survey"


def check_robots():
    rp = robotparser.RobotFileParser()
    rp.set_url(urljoin(BASE_URL, "robots.txt"))
    rp.read()

    allowed = rp.can_fetch("RP", "/survey")

    print(f"Robots allowed: {allowed}")

    if not allowed:
        raise Exception("robots.txt disallows scraping /survey")


def scrape_data():
    req = Request(
        SURVEY_URL,
        headers={"User-Agent": "RP"}
    )

    with urlopen(req) as response:
        html = response.read().decode("utf-8")

    return html


def parse_entries(html):
    soup = BeautifulSoup(html, "html.parser")

    records = []

    for tag in soup.find_all():
        text = tag.get_text(" ", strip=True)

        if not text:
            continue

        if any(status in text for status in
               ["Accepted", "Rejected", "Waitlisted"]):

            record = _parse_entry(text)

            if record:
                records.append(record)

    return records


def _parse_entry(text):
    record = {
        "program_name": None,
        "university": None,
        "comments": None,
        "date_added": None,
        "url": None,
        "status": None,
        "acceptance_date": None,
        "rejection_date": None,
        "semester_year": None,
        "international": None,
        "gre_score": None,
        "gre_v_score": None,
        "degree": None,
        "gpa": None,
        "gre_aw": None,

        # required for traceability
        "raw_text": text
    }

    # status
    if "Accepted" in text:
        record["status"] = "Accepted"

    elif "Rejected" in text:
        record["status"] = "Rejected"

    elif "Waitlisted" in text:
        record["status"] = "Waitlisted"

    # GPA
    gpa_match = re.search(
        r'GPA[:\s]*([0-4]\.\d+)',
        text,
        re.IGNORECASE
    )

    if gpa_match:
        record["gpa"] = gpa_match.group(1)

    # GRE verbal
    gre_v_match = re.search(
        r'GRE\s*V[:\s]*([0-9]{2,3})',
        text,
        re.IGNORECASE
    )

    if gre_v_match:
        record["gre_v_score"] = gre_v_match.group(1)

    # GRE AW
    aw_match = re.search(
        r'AW[:\s]*([0-6](?:\.[0-9])?)',
        text,
        re.IGNORECASE
    )

    if aw_match:
        record["gre_aw"] = aw_match.group(1)

    # degree
    if "PhD" in text:
        record["degree"] = "PhD"

    elif "Master" in text or "MS" in text:
        record["degree"] = "Masters"

    # keep entire text as comments for now
    record["comments"] = text

    return record


def save_data(data):
    with open("applicant_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_data():
    with open("applicant_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    check_robots()

    html = scrape_data()

    records = parse_entries(html)

    print(f"Extracted {len(records)} candidate records")

    save_data(records)

    print("Saved applicant_data.json")
    soup = BeautifulSoup(html, "html.parser")

    # Find the first occurrence of Western University
    matches = soup.find_all(
        string=lambda s: s and "Western University" in s
    )

    m = matches[0]

    row = m.parent

    while row and row.name != "tr":
        row = row.parent

    print(row.prettify())
    url = "https://www.thegradcafe.com/result/1020297"
    print(soup.get_text(" ", strip=True)[:5000])

    rows = soup.find_all("tr")

    for i in range(1, 10):
        print(f"\nROW {i}")
        print(rows[i].get_text(" ", strip=True))

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "page=" in href:
            print(href)


if __name__ == "__main__":
    main()

