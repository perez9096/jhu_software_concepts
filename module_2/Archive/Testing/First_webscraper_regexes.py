import re

from urllib.request import urlopen

re.findall("ab*c", "ac")

re.findall("ab*c","ABC",re.IGNORECASE)

re.findall("a.c","abc")

re.findall("a.*c", "abbc")

match_results = re.search("ab*c","ABC", re.IGNORECASE)
match_results.group()

string = "Everything is <replaced> if it's in <tags>."
string = re.sub("<.*>","ELEPHANTS", string)

print(string)

## -----------------------------------------

url = "http://olympus.realpython.org/profiles/poseidon"

page = urlopen(url)

html_bytes = page.read()
html = html_bytes.decode("utf-8")

print(html)

pattern = "<title.*?>.*?</title.*?>"
match_results = re.search(pattern, html, re.IGNORECASE)

title_index = re.findall("<title.*>", html, re.IGNORECASE)
#title_index = html.find("<title>")
print(title_index)

#start_index = title_index + len("<title>")
#print(start_index)

#end_index = html.find("</title>")
#print(end_index)

title = match_results.group()
print(title)

title = re.sub("<.*?>", "", title) # Remove HTML
print(title)
