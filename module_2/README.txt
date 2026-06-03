# jhu_software_concepts
Modern Software Concepts in Python
Module 2: Web Scraping
Created by Raul Perez
Due Date: May 31, 2026

--------------------------
PROJECT DESCRIPTION
--------------------------

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


-------------------------
FILES
-------------------------
module_1/
|
|__ README.txt
|__ requirements.txt
|__run_me.py
|__board/
    |__ __init__.py
    |__ pages.py
    |__ static/
        |__ homepage_profile_pic.jpeg
        |__ projectspage_pic.jpeg
        |__ contactinfopage_pic.jpeg
    |__ templates/
        |__ pages/
            |__ contactinfo.HTML
            |__ homepage.HTML
            |__ projectspage.HTML
        |__ _navigation.HTML
        |__ base.HTML




