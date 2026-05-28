from bs4 import BeautifulSoup
import re

html = open('data/debug_page_posts.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
posts = soup.find_all(attrs={'data-testid': 'expandable-text-box'})
print(f'Found {len(posts)} posts')
if posts:
    post = posts[0]
    parent = post
    role_listitem = None
    for _ in range(15):
        parent = parent.parent
        if parent and parent.get('role') == 'listitem':
            role_listitem = parent
            break
    print('Found listitem?', bool(role_listitem))
    links = role_listitem.find_all('a', href=True) if role_listitem else []
    print('Links found in listitem:')
    for l in links:
        print(' -', l['href'])
