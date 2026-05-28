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

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDryRun")

class MockEmailClient:
    """A dummy email client that just prints the email instead of sending it."""
    def __init__(self, logger):
        self.logger = logger
        
    def is_configured(self):
        return True
        
    def send_application(self, to_email, subject, body, attachment_path=None):
        self.logger.info("\n" + "="*60)
        self.logger.info(" 🛑 DRY RUN MODE: MOCK EMAIL (NOT ACTUALLY SENT) 🛑 ")
        self.logger.info("="*60)
        self.logger.info(f"TO: {to_email}")
        self.logger.info(f"SUBJECT: {subject}")
        self.logger.info(f"ATTACHMENT (PDF): {attachment_path}")
        self.logger.info("BODY (HTML Format expected):")
        self.logger.info(body)
        self.logger.info("="*60 + "\n")
        
        # We return False here so the database does NOT mark it as 'APPLIED'.
        # This allows you to actually send the email later when running for real!
        return False

def test_dry_run():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    keyword = os.getenv("LINKEDIN_KEYWORD", "RPA Developer")
    
    # Load resume
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'resume.json'))
    if not os.path.exists(resume_path):
        logger.error(f"Cannot find resume.json at {resume_path}")
        return
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
        
    logger.info("Starting End-to-End DRY RUN...")
    
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
                
            # Scrape up to 10 posts for testing
            posts = scraper.search_posts(keyword=keyword, max_posts=10, date_filters=["past-24h"])
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
    mock_email = MockEmailClient(logger=logger)
    resume_builder = ResumeBuilder(logger=logger)
    
    # We use the real DB so you can see the results in your dashboard!
    db_path = 'data/jobs.db'
    db = Database(db_path)
    
    # Not clearing the table so we don't lose previous tests
    
    analyzer = PostAnalyzer(
        logger=logger,
        llm_service=llm_service,
        email_client=mock_email,
        resume_builder=resume_builder,
        resume_data=resume_data
    )
    
    # Overwrite the db in the analyzer to use our dry run db
    analyzer.db = db
    
    # 3. Analyze
    logger.info("Sending posts to LLM for analysis...")
    analyzer.analyze(posts)
    
    logger.info("Dry run complete! Check the console output above to see the mocked emails.")

if __name__ == "__main__":
    test_dry_run()
