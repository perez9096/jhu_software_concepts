from bs4 import BeautifulSoup
from urllib.request import urlopen

# A list of all applicant results
url = "https://www.thegradcafe.com/results/"

# Open Web Page
page = urlopen(url)
html = page.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

# Get the Page Title
# image1, image2 = soup.find_all("img")


