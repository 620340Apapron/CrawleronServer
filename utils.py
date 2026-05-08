# utils.py
import re

def extract_isbn(soup):

    meta_tags = [
        {"property": "book:isbn"},
        {"property": "og:isbn"},
        {"name": "isbn"},
        {"name": "twitter:data1"} 
    ]
    for tag in meta_tags:
        found = soup.find("meta", attrs=tag)
        if found and found.get("content"):
            isbn = re.sub(r'\D', '', found.get("content"))
            if len(isbn) >= 10: return isbn


    text = soup.get_text()
    match = re.search(r'(97[89][0-9]{10})', text) # หา ISBN-13
    if match:
        return match.group(1)
        
    return "Unknown"