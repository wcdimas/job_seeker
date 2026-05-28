import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.job_seeker.linkedin_scraper import LinkedInScraper
from src.job_seeker.db import Database
from src.job_seeker.analyzer import PostAnalyzer

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestScraper")

def test_scraper():
    # Load env
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    keyword = os.getenv("LINKEDIN_KEYWORD", "RPA Developer")
    
    if not email or not password:
        logger.error("LINKEDIN_EMAIL or LINKEDIN_PASSWORD not found in .env")
        return
        
    logger.info("Starting Scraper (Headless mode)...")
    # You can change headless=False if you want to watch the magic happen!
    scraper = LinkedInScraper(logger=logger, headless=False)
    
    try:
        if email and password:
            auto_login = scraper.initialize(email, password)
            if auto_login:
                logger.info("Automatic login succeeded! Proceeding with scraping.")
            else:
                logger.info("Manual login was required, but succeeded. Proceeding with scraping.")
                
            posts = scraper.search_posts(keyword=keyword, date_filters=["past-24h"], max_hours=2)
            logger.info(f"Scraped {len(posts)} posts.")
        else:
            logger.error("No LinkedIn credentials, cannot scrape.")
            return
        
        # Initialize Database and Analyzer (without LLM/Email to just test DB population)
        # We pass None for LLM, Email, and Resume to strictly test the local fallback & db insertion
        db = Database('data/jobs.db')
        analyzer = PostAnalyzer(
            logger=logger,
            llm_service=None,
            email_client=None,
            resume_builder=None,
            resume_data=None
        )
        
        # Analyze and insert
        analyzer.analyze(posts)
        
        # Check DB
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            logger.info(f"Database currently holds {count} total jobs.")
            
            # Print latest
            cursor.execute("SELECT id, is_job_posting, post_url, author_profile FROM jobs ORDER BY id DESC LIMIT 5")
            latest = cursor.fetchall()
            logger.info("Latest 5 jobs in DB:")
            for row in latest:
                logger.info(f"ID: {row[0]}, Is Job: {row[1]}, URL: {row[2]}, Author: {row[3]}")
                
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        scraper.close()
        logger.info("Scraper closed.")

if __name__ == "__main__":
    test_scraper()
