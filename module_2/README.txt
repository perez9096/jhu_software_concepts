# jhu_software_concepts
Modern Software Concepts in Python
Module 2: Web Scraping
Created by Raul Perez
Due Date: May 31, 2026

---------------------------------
PROJECT DESCRIPTION AND APPROACH
---------------------------------

This project collects graduate admissions data from https://www.thegradcafe.com and stores the information as structured JSON data for later analysis.
The scraper.py checks for and ensures we follow the website's robots.txt rules before collecting any information and only accesses publicly available admissions results pages.
The final output is a JSON file named applicant_data.json containing applicant admission records and associated metadata.
The collected data is intended for use in later modules where the records will be cleaned and standardized using a locally hosted language model.

- APPROACH:
    - Robots.txt Verification
    Before scraping begins, the program checks The Grad Cafe robots.txt file using Python's urllib.robotparser module.
    The scraper verifies that access to the /survey endpoint is permitted before any requests are made. If robots.txt blocks access, the scraper terminates immediately.
    Implementation:
        check_robots()
        Uses RobotFileParser
        Verifies permission for /survey

    - URL Construction and Management
    The scraper uses Python's urllib package to construct and manage URLs.
    Admissions records are retrieved from paginated survey pages:
        https://www.thegradcafe.com/survey?page=N
        where N represents the page number.
    The scraper automatically increments the page number and continues gathering records until either:
        30,000 records are collected
        no additional pages exist the website blocks requests
        a Cloudflare protection page is encountered
    Implementation:
        scrape_data()
        URL generation through formatted strings

    - Requesting Web Pages
        The scraper retrieves HTML using:
            urllib.request.Request
            urllib.request.urlopen
        A custom User-Agent string (RP) is supplied with every request.
        To avoid excessive traffic and to comply with assignment requirements, the scraper:
            waits between requests
            retries failed requests
            stops if repeated failures occur
        Implementation:
            fetch()

    - HTML Parsing
        The HTML returned from each survey page is parsed using BeautifulSoup.
        Inspection of the page structure showed that applicant records are stored as repeating groups of three table rows:
            Summary row
            Metadata row
            Comment row
        Example:
            Row 1:
                University
                Program
                Degree
                Date Added
                Decision
            Row 2:
                Acceptance/Rejection information
                GPA
                GRE information
                Applicant type
                Semester
            Row 3:
                Applicant comments
                The scraper processes records in groups of three rows and converts each group into a dictionary.

        Implementation:
            parse_triplet()
            BeautifulSoup find_all("tr")

    - Data Extraction
        The scraper extracts the following fields whenever available:
            Program Name
            University
            Comments
            Applicant Status
            Semester and Year
            Degree Type
            GPA
            GRE Verbal Score
            GRE Analytical Writing Score
        Regular expressions are used to locate GPA and GRE values.
        Implementation:
            Python re module
            BeautifulSoup text extraction

    - Raw Data Preservation
        For reproducibility and traceability, each record contains a raw_text field.
        This field stores the original extracted text used to generate the structured record.
        No original applicant information is removed.
    
    - Handling Missing Data
        Many Grad Cafe entries do not contain every possible field.
        When information is unavailable, the scraper stores:
            None
        This ensures consistent JSON structure across all records.

    - JSON Storage
        After scraping is complete, all records are stored in:
            applicant_data.json
        The file is written using Python's JSON library with UTF-8 encoding and formatted indentation.
        Implementation:
            save_data()

    - Data Loading
        Previously saved data can be reloaded through:
            load_data()
        This allows future cleaning and analysis steps without re-scraping the website.

    - Blocking and Rate-Limit Detection
        The scraper attempts to detect:
            Cloudflare protection pages
            request failures
            connection interruptions
        If a block is detected, the scraper pauses and retries once. If the block persists, scraping stops.
        This behavior ensures compliance with the assignment requirement to stop scraping when blocked or rate-limited.

-------------------------
FILES
-------------------------
Main scraping program.
Functions:
    check_robots()
    fetch()
    parse_triplet()
    scrape_data()
    save_data()
    load_data()
    applicant_data.json
        Generated admissions data.
    requirements.txt
        Python dependencies required to recreate the environment.
    screenshot.jpg
        Screenshot showing robots.txt verification.

module_2/
|
|__ README.txt
|__ requirements.txt
|__scraper.py
|__llm_hosting/
    |__ README.md
    |__ app.py
    |__ canon_programs.txt
    |__ canon_universities.txt

--------------------
REQUIREMENTS
--------------------
Python Version:
Python 3.10+
Packages:
beautifulsoup4
Standard Library Modules:
    urllib
    json
    re
    time
    os

----------------
KNOWN BUGS
----------------
Program and University Separation
    This version uses simple string splitting to identify the university and program fields. Some issues were seen early on.
    Because university names and program names vary significantly in length, some entries may not be separated perfectly.
Example:
"University of California Berkeley Computer Science"
may not always split correctly into:
    University
    Program
Run-time errors
    Experienced issues with reaching 30000 data entries.

In the next phase of the project, the provided local language model will be used to standardize and clean university and program names using canonical institution lists and fuzzy matching.



