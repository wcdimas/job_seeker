from bs4 import BeautifulSoup

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
    
    buttons = role_listitem.find_all('button')
    print('Buttons in first post:')
    for b in buttons:
        print(f'- aria-label: {b.get("aria-label")}, text: {b.get_text(strip=True)[:30]}')
