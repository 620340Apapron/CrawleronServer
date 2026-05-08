import re
# utils.py
def extract_isbn(soup):
    import re
    text = soup.get_text()
    # หา ISBN-13 (เริ่มด้วย 978 หรือ 979) หรือ ISBN-10
    match = re.search(r'(97[89][0-9]{10}|[0-9]{9}[0-9X])', text)
    if match:
        return match.group(1)
    
    # สำรอง: หาจาก Meta Tags
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "") or meta.get("name", "")
        if "isbn" in prop.lower():
            content = meta.get("content")
            if content: return re.sub(r'\D', '', content)
            
    return "Unknown"