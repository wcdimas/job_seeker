import re
from bs4 import BeautifulSoup
import os

try:
    with open("e:/job_seeker/data/debug_page.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('div', class_=re.compile(r'artdeco-pagination'))
    if pagination:
        print("Pagination found!")
        pages = pagination.find_all('li')
        print(f"Pages: {len(pages)}")
    else:
        print("No pagination found.")
except Exception as e:
    print(f"Error: {e}")
