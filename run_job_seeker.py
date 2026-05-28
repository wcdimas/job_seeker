import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.job_seeker.linkedin_scraper import LinkedInScraper
from src.job_seeker.db import Database
from src.job_seeker.analyzer import PostAnalyzer
from src.job_seeker.llm_service import LLMService
from src.job_seeker.resume_builder import ResumeBuilder
from src.job_seeker.emailer import EmailClient

import argparse

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobSeekerAgent")

def run():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
    load_dotenv(env_path)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Job Seeker Autonomous Agent.")
    parser.add_argument("--keyword", type=str, help="The search keyword for LinkedIn.")
    parser.add_argument("--max-hours", type=int, help="Maximum age of posts in hours.")
    parser.add_argument("--date-filter", type=str, help="Date filter (e.g. past-24h, past-week, past-month).")
    args = parser.parse_args()
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    # Use CLI args if provided, else fallback to .env, else fallback to defaults
    keyword = args.keyword if args.keyword else os.getenv("LINKEDIN_KEYWORD", "RPA Developer")
    date_filter = args.date_filter if args.date_filter else os.getenv("LINKEDIN_DATE_POSTED", "past-week")
    max_hours = args.max_hours if args.max_hours else 168 # Default 168 hours = 7 days
    
    # Load resume
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'resume.json'))
    if not os.path.exists(resume_path):
        logger.error(f"Cannot find resume.json at {resume_path}")
        return
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
        
    logger.info("===========================================")
    logger.info("   🤖 JOB SEEKER AUTONOMOUS AGENT 🤖   ")
    logger.info("===========================================")
    
    # Initialize the REAL EmailClient
    email_client = EmailClient(logger=logger)
    
    # Check authentication
    if not email_client.authenticate_if_needed():
        logger.error("Microsoft Graph authentication failed. Exiting.")
        return
    
    # 1. Start Scraper
    # Set headless=True for background running!
    scraper = LinkedInScraper(logger=logger, headless=False)
    posts = []
    try:
        if email and password:
            auto_login = scraper.initialize(email, password)
            if auto_login:
                logger.info("Automatic login succeeded! Proceeding with scraping.")
            else:
                logger.info("Manual login was required, but succeeded. Proceeding with scraping.")
                
            # Scrape posts (using infinite scroll)
            logger.info(f"Searching for: {keyword} ({date_filter})")
            posts = scraper.search_posts(keyword=keyword, max_hours=max_hours, date_filters=[date_filter])
            logger.info(f"Scraped {len(posts)} posts.")
        else:
            logger.error("No LinkedIn credentials found in .env.")
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
        email_client=email_client, # USING THE REAL CLIENT DIRECTLY
        resume_builder=resume_builder,
        resume_data=resume_data
    )
    
    # 3. Analyze
    logger.info("Sending posts to Gemini AI for analysis...")
    analyzer.analyze(posts)
    
    logger.info("===========================================")
    logger.info("             ✅ RUN COMPLETE ✅            ")
    logger.info("===========================================")

if __name__ == "__main__":
    run()
