from urllib.request import Request
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
import json
import time

class GradCafeScraper:

    def __init__(self):
        self.base = "https://www.thegradcafe.com/"
        self.data = []

        # robots.txt check
        rp = robotparser.RobotFileParser()
        rp.set_url(urljoin(self.base, "robots.txt"))
        rp.read()

        if not rp.can_fetch("RP", "/results/"):
            raise Exception("Blocked by robots.txt")

        # Selenium setup
        self.driver = webdriver.Chrome()

    def scrape_data(self, pages=5):
        for page in range(1, pages + 1):
            url = f"https://www.thegradcafe.com/results/?page={page}"

            self.driver.get(url)
            time.sleep(3)  # allowed: wait for rendering

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            self._parse_page(soup)

    def _parse_page(self, soup):
        rows = soup.find_all("div")

        for r in rows:
            text = r.get_text(" ", strip=True)

            if any(x in text for x in ["Accepted", "Rejected", "Waitlisted"]):
                self.data.append({
                    "raw_text": text
                })

    def save_data(self, filename="applicant_data.json"):
        with open(filename, "w") as f:
            json.dump(self.data, f, indent=2)

    def load_data(self, filename):
        with open(filename, "r") as f:
            return json.load(f)


if __name__ == "__main__":
    scraper = GradCafeScraper()
    scraper.scrape_data(pages=10)  # scale this to 30k later
    scraper.save_data()