import re

def extract_isbn(soup):

    meta = soup.find("meta", {"property": "book:isbn"})
    if meta:
        return meta.get("content")

    isbn_tag = soup.find(attrs={"itemprop": "isbn"})
    if isbn_tag:
        return isbn_tag.text.strip()

    text = soup.get_text()

    match = re.search(r'97[89][-\s]?\d[-\s]?\d{2,5}[-\s]?\d{2,7}[-\s]?\d', text)

    if match:
        return match.group().replace("-", "").replace(" ", "")

    return "Unknown"