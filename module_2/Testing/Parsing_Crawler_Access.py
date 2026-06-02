from urllib import parse, robotparser

agent = "RP"
url = "https://www.thegradcafe.com/"

# Set up parser with website
parser = robotparser.RobotFileParser(url)
parser.set_url(parse.urljoin(url, 'robots.txt'))
parser.read()

paths = [
    "/",
    "https://www.thegradcafe.com/results/",
    "https://www.thegradcafe.com/results/935453"
]

for path in paths:
    print(f"{parser.can_fetch(agent, path), path}")

