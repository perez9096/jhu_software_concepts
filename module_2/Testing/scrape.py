from urllib.request import Request, urlopen
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

base = "https://www.thegradcafe.com/"

# robots.txt check
parser = robotparser.RobotFileParser()
parser.set_url(urljoin(base, "robots.txt"))
parser.read()

if not parser.can_fetch("RP", "/results/"):
    raise Exception("robots.txt disallows scraping /results/")

# request page
url = "https://www.thegradcafe.com/"

req = Request(url, headers={"User-Agent": "RP"})

with urlopen(req) as response:
    html = response.read().decode("utf-8")

# (optional) parse
soup = BeautifulSoup(html, "html.parser")

# save RAW HTML (best for LLM pipeline)
data = {
    "url": url,
    "html": html
}

with open("applicant_data.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved raw HTML to applicant_data.json")