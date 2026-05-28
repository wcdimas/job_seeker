import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


class LinkedInScraper:
    def __init__(self, logger, headless=False):
        """
        Initializes the LinkedInScraper with a Chrome webdriver.
        """
        self.logger = logger
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        # Add options to make it look less like a bot
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Save Chrome profile to avoid logging in every time
        import os
        profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'chrome_profile'))
        options.add_argument(f"--user-data-dir={profile_path}")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def initialize(self, email=None, password=None) -> bool:
        """
        Navigates to the LinkedIn login page and waits for the user to log in manually,
        unless credentials are provided via .env.
        Returns True if login happened automatically (or session already active),
        Returns False if manual login was required.
        """
        self.logger.info("Navigating to LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        
        # Quick check if already logged in (e.g., from Chrome Profile)
        time.sleep(3)
        if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
            self.logger.info("Already logged in via active session.")
            return True
            
        automatic_login_success = False
        
        if email and password:
            self.logger.info("Attempting automatic login using credentials from .env...")
            try:
                # Wait for any username input to be present in the DOM
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete*='username'], input#username, input#session_key, input[type='email'], input[type='text']"))
                )
                
                # Find all potential username inputs and pick the visible one
                username_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[autocomplete*='username'], input#username, input#session_key, input[type='email'], input[type='text']")
                username_input = None
                for un in username_inputs:
                    if un.is_displayed() and un.is_enabled():
                        username_input = un
                        break
                        
                if not username_input:
                    raise Exception("Visible username input not found")
                
                # Find all potential password inputs and pick the visible one
                password_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[autocomplete*='password'], input#password, input#session_password, input[type='password']")
                password_input = None
                for pw in password_inputs:
                    if pw.is_displayed():
                        password_input = pw
                        break
                
                if not password_input:
                    raise Exception("Visible password input not found")
                
                username_input.clear()
                username_input.send_keys(email)
                
                password_input.clear()
                password_input.send_keys(password)
                password_input.send_keys(Keys.RETURN)
                
                self.logger.info("Credentials submitted.")
                
                # Wait for feed URL quickly to confirm automatic login worked
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "feed" in driver.current_url or "jobs" in driver.current_url
                )
                self.logger.info("Automatic login successful.")
                automatic_login_success = True
            except Exception as e:
                self.logger.error(f"Failed during automatic login: {e}")
                self.logger.info("Please complete login manually.")
        else:
            self.logger.info("No credentials found in .env.")
            self.logger.info("Please log in manually in the opened browser window.")
            
        if not automatic_login_success:
            self.logger.info("Waiting for the feed page to load to confirm manual login... (Timeout is 5 minutes)")
            # Wait until the URL changes to the feed or a reasonable timeout
            WebDriverWait(self.driver, 300).until(
                lambda driver: "feed" in driver.current_url or "jobs" in driver.current_url
            )
            self.logger.info("Manual login confirmed!")
            
        return automatic_login_success

    def search_posts(self, keyword, max_posts=None, date_filters=None, max_hours=None):
        """
        Searches for posts containing the keyword.
        date_filters: e.g. ["past-24h", "past-week", "past-month"]
        max_hours: integer, if provided, skips posts older than this limit.
        max_posts: integer, if provided, limits the number of posts scraped.
        """
        self._max_hours = max_hours
        self.logger.info(f"Searching for posts with keyword: {keyword}")
        
        import urllib.parse
        import json
        
        base_url = "https://www.linkedin.com/search/results/content/"
        query_params = {
            "keywords": keyword,
            "origin": "FACETED_SEARCH"
        }
        
        if date_filters:
            self.logger.info(f"Applying date filters: {date_filters}")
            query_params["datePosted"] = json.dumps(date_filters)
            
        query_params["sortBy"] = json.dumps(["date_posted"])
            
        search_url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
        self.driver.get(search_url)
        
        # Wait for the results to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-results-container, ul.reusable-search__entity-result-list, div.scaffold-layout__main, div.feed-shared-update-v2"))
            )
        except Exception:
            self.logger.warning("Could not clearly identify search results container, continuing anyway...")
            time.sleep(5) # Fallback wait
        
        posts_data = []
        last_posts_count = 0
        
        while max_posts is None or len(posts_data) < max_posts:
            # Wait for posts to load
            time.sleep(3)
            
            # Click all "more" buttons to expand truncated posts before parsing
            try:
                # Use contains(., 'text') to match nested spans, and check common classes
                more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'more') or contains(., 'mais') or contains(@class, 'see-more')]")
                for btn in more_buttons:
                    try:
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(0.1)
                    except Exception:
                        pass
                if more_buttons:
                    time.sleep(1)
            except Exception:
                pass
            
            # Parse page source with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            import re
            
            # LinkedIn often uses 'update-components-text' for the body of the post in search results
            # But recent versions use data-testid="expandable-text-box" for the post text
            post_elements = soup.find_all(attrs={'data-testid': 'expandable-text-box'})
            
            if not post_elements:
                post_elements = soup.find_all('div', class_=re.compile(r'update-components-text'))
            
            # Fallback to general post containers
            if not post_elements:
                 post_elements = soup.find_all('div', class_=re.compile(r'feed-shared-update-v2'))
                 
            # Second fallback to search result containers
            if not post_elements:
                 post_elements = soup.find_all('li', class_=re.compile(r'reusable-search__result-container'))
                 
            if not post_elements and len(posts_data) == 0:
                # Dump HTML for debugging
                with open("data/debug_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.logger.warning("Found 0 potential posts. Saved HTML to data/debug_page.html for inspection.")
            
            for post in post_elements:
                if max_posts is not None and len(posts_data) >= max_posts:
                    break
                    
                # Extract text
                text_content = post.get_text(separator=' ', strip=True)
                
                # Filter out empty or very short elements that might be false positives
                if len(text_content) < 10:
                    continue
                    
                # Extract post URL and Author Profile
                post_url = None
                author_profile = None
                
                # Traverse up to find the main card container (feed-shared-update-v2 or reusable-search__result-container)
                card_container = post
                for _ in range(10): # Go up to 10 levels up
                    if card_container.parent:
                        card_container = card_container.parent
                        if card_container.get('role') == 'listitem' or any(c in str(card_container.get('class', [])) for c in ['feed-shared-update-v2', 'reusable-search__result-container', 'search-results-container']):
                            break
                            
                links = card_container.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if not author_profile and ('/in/' in href or '/company/' in href):
                        author_profile = href.split('?')[0] # Remove query params
                    if not post_url and ('urn:li:activity:' in href or '/posts/' in href or '/feed/update/' in href):
                        post_url = href.split('?')[0]
                        
                # Fallback: Many LinkedIn feed cards have the post URN in the 'data-urn' attribute
                if not post_url:
                    data_urn = card_container.get('data-urn') or card_container.get('data-id')
                    if not data_urn:
                        # Try finding any element with data-urn inside the card
                        urn_elem = card_container.find(attrs={"data-urn": True})
                        if urn_elem:
                            data_urn = urn_elem.get('data-urn')
                            
                    if not data_urn:
                        # Bulletproof fallback: regex search the raw HTML of the card for the activity URN or shareId
                        import re
                        raw_html = str(card_container)
                        
                        urn_match = re.search(r'urn:li:activity:(\d+)', raw_html)
                        if urn_match:
                            data_urn = urn_match.group(0)
                        else:
                            # Search for shareId=123456789 or activityId=123456789 which are used in new LinkedIn layouts
                            id_match = re.search(r'(?:shareId|activityId|urn:li:share:)=(\d+)', raw_html)
                            if id_match:
                                data_urn = f"urn:li:activity:{id_match.group(1)}"
                            
                    if data_urn:
                        # Ensure it's just the ID if it contains urn:li:activity:
                        urn_id = data_urn.split(':')[-1] if ':' in data_urn else data_urn
                        post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{urn_id}/"
                        
                    if not post_url and author_profile:
                        # The Ultimate Fallback: if LinkedIn completely stripped the URN, point to the author's recent activity
                        post_url = author_profile.rstrip('/') + "/recent-activity/all/"
                        self.logger.info("Used recent-activity fallback for post URL.")
                    elif not post_url:
                        self.logger.warning(f"Could not find data-urn. Card attrs: {card_container.attrs}")
                        # Dump this specific card's HTML so Antigravity can read it and fix the parser
                        debug_file = f"data/debug_card_{int(time.time())}.html"
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(raw_html)
                        self.logger.warning(f"Dumped unparseable card HTML to {debug_file} for inspection.")
                
                # Extract post time
                post_time_str = ""
                for text in card_container.stripped_strings:
                    if re.search(r'^\d+[hmdwy]\s*[•·\ufffd]?', text) or 'ago' in text.lower() or 'now' in text.lower():
                        post_time_str = text.split('•')[0].split('\ufffd')[0].strip()
                        break
                        
                # Time filtering logic
                if getattr(self, '_max_hours', None) is not None and post_time_str:
                    match = re.search(r'(\d+)([hmdwy])', post_time_str.lower())
                    if match:
                        val = int(match.group(1))
                        unit = match.group(2)
                        
                        skip_post = False
                        if unit in ['d', 'w', 'y']:
                            skip_post = True
                        elif unit == 'h' and val > self._max_hours:
                            skip_post = True
                            
                        if skip_post:
                            self.logger.info(f"Encountered a post from {post_time_str} which is older than max_hours ({self._max_hours}h). Stopping search.")
                            return posts_data
                            
                    elif 'now' not in post_time_str.lower():
                        # Unknown format, we keep it just in case
                        pass
                
                # Check for duplicates (basic check)
                if not any(p['text'] == text_content for p in posts_data):
                    posts_data.append({
                        'keyword': keyword,
                        'text': text_content,
                        'post_url': post_url,
                        'author_profile': author_profile,
                        'post_time': post_time_str,
                        'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            self.logger.info(f"Collected {len(posts_data)} posts so far...")
            
            if max_posts is not None and len(posts_data) >= max_posts:
                self.logger.info("Reached target max_posts. Stopping scroll.")
                break
            
            # Scroll incrementally to trigger lazy loading of posts
            scroll_increment = 800
            for _ in range(6):
                self.driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
                time.sleep(1.5)
            # One final scroll to absolute bottom to force trigger
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check if we found any new posts in this iteration
            # If len(posts_data) hasn't changed since the start of the loop iteration, we hit the bottom of the page
            if len(posts_data) == last_posts_count:
                self.logger.info("No new posts loaded after scrolling. Reached the end of the infinite scroll results.")
                break
            
            last_posts_count = len(posts_data)
            
        return posts_data

    def close(self):
        """
        Closes the webdriver.
        """
        self.driver.quit()
