from bs4 import BeautifulSoup


def parsing(res):
    soup = BeautifulSoup(res.text, 'html.parser')
    h1 = (soup.find(["h1"]))
    h1 = h1.text[:255] if h1 else ""
    title = soup.find(["title"])
    title = title.text[:255] if title else ""
    description = (soup.find("meta", {"name": "description"}))
    description = description["content"][:255] if description else ""
    return h1, title, description
