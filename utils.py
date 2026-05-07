import re

def extract_isbn(soup):
    text = soup.get_text()
    # Matches 13-digit ISBNs
    match = re.search(r'(97[89][0-9]{10})', text)
    if match:
        return match.group(1)
    
    # Fallback to meta tags
    isbn_tag = soup.find("meta", attrs={"property": "book:isbn"})
    if isbn_tag:
        return isbn_tag.get("content")
        
    return "Unknown"