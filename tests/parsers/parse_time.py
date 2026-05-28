from bs4 import BeautifulSoup
import re

html = open('data/debug_page_posts.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
posts = soup.find_all(attrs={'data-testid': 'expandable-text-box'})
if posts:
    post = posts[0]
    parent = post
    role_listitem = None
    for _ in range(15):
        parent = parent.parent
        if parent and parent.get('role') == 'listitem':
            role_listitem = parent
            break
    
    # Let's find all text in the card that looks like a time
    texts = role_listitem.stripped_strings
    time_matches = []
    for text in texts:
        if re.search(r'^\d+[hmdwy]\s*[•·]?', text) or 'ago' in text.lower() or 'now' in text.lower():
            time_matches.append(text)
    print('Time matches:', time_matches)
