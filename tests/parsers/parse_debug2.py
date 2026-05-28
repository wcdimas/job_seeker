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
    
    print('Attrs of listitem:', role_listitem.attrs)
    print('Any data-urn?', len(role_listitem.find_all(attrs={'data-urn': True})))
    keys = [e.get('componentkey') for e in role_listitem.find_all(attrs={'componentkey': True})]
    print('Any componentkey?', keys)
