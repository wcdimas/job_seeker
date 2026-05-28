import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.job_seeker.linkedin_scraper import LinkedInScraper
from src.job_seeker.db import Database
from src.job_seeker.analyzer import PostAnalyzer
from src.job_seeker.llm_service import LLMService
from src.job_seeker.resume_builder import ResumeBuilder
from src.job_seeker.emailer import EmailClient

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestEmailSelf")

class EmailSelfWrapper:
    """Wraps the real EmailClient to force all emails to be sent to your own inbox."""
    def __init__(self, real_client, target_email, logger):
        self.client = real_client
        self.target_email = target_email
        self.logger = logger
        
    def is_configured(self):
        return self.client.is_configured()
        
    def send_application(self, to_email, subject, body, attachment_path=None):
        self.logger.info("\n" + "="*60)
        self.logger.info(f" 🎯 INTERCEPTED EMAIL TARGET: {to_email} -> REDIRECTING TO {self.target_email} 🎯 ")
        self.logger.info("="*60)
        
        # Prepend a notice to the body so you know who it was originally meant for
        notice = f"<p style='color:red;'><b>[TEST RUN]</b> This email was originally drafted for <b>{to_email}</b>.</p><hr>"
        new_body = notice + body
        
        return self.client.send_application(
            to_email=self.target_email, 
            subject=f"[TEST] {subject}", 
            body=new_body, 
            attachment_path=attachment_path
        )

def test_email_self():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    keyword = os.getenv("LINKEDIN_KEYWORD", "RPA Developer")
    
    # We will send the test email to your LINKEDIN_EMAIL account
    target_email = email
    
    # Load resume
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'resume.json'))
    if not os.path.exists(resume_path):
        logger.error(f"Cannot find resume.json at {resume_path}")
        return
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
        
    logger.info("Starting Full Run (Redirecting emails to yourself)...")
    
    # Initialize the REAL EmailClient
    real_email_client = EmailClient(logger=logger)
    
    # Check authentication FIRST before scraping, because it requires interactive login!
    if not real_email_client.authenticate_if_needed():
        logger.error("You must complete the Microsoft Graph authentication first. Follow the console link.")
        return
    
    wrapped_email_client = EmailSelfWrapper(real_email_client, target_email, logger)
    
    # 1. Start Scraper
    scraper = LinkedInScraper(logger=logger, headless=False)
    posts = []
    try:
        if email and password:
            auto_login = scraper.initialize(email, password)
            if auto_login:
                logger.info("Automatic login succeeded! Proceeding with scraping.")
            else:
                logger.info("Manual login was required, but succeeded. Proceeding with scraping.")
                
            # Scrape up to 5 posts for testing
            posts = scraper.search_posts(keyword=keyword, max_posts=15, date_filters=["past-24h"])
            logger.info(f"Scraped {len(posts)} posts.")
        else:
            logger.error("No LinkedIn credentials, cannot scrape.")
    except Exception as e:
        logger.error(f"Scraper error: {e}")
    finally:
        scraper.close()
        
    if not posts:
        logger.info("No posts to analyze. Exiting.")
        return
        
    # 2. Initialize Services for Analysis
    llm_service = LLMService(logger=logger, resume_data=resume_data)
    resume_builder = ResumeBuilder(logger=logger)
    
    db_path = 'data/jobs.db'
    db = Database(db_path)
    
    analyzer = PostAnalyzer(
        logger=logger,
        llm_service=llm_service,
        email_client=wrapped_email_client,
        resume_builder=resume_builder,
        resume_data=resume_data
    )
    
    analyzer.db = db
    
    # 3. Analyze
    logger.info("Sending posts to LLM for analysis and emailing matches...")
    analyzer.analyze(posts)
    
    logger.info("Test complete!")

if __name__ == "__main__":
    test_email_self()
