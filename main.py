import os
from dotenv import load_dotenv
from src.job_seeker.linkedin_scraper import LinkedInScraper
from src.job_seeker.analyzer import PostAnalyzer
from src.job_seeker.logger import ProjectLogger
from src.job_seeker.llm_service import LLMService
import json

def main():
    load_dotenv()
    logger = ProjectLogger.get_logger("Main")
    logger.info("Starting LinkedIn Post Search and Analysis...")
    
    # Keyword to search
    keyword = os.getenv("LINKEDIN_KEYWORD")
    if not keyword:
        keyword = input("Enter keyword to search on LinkedIn: ").strip()
        
    if not keyword:
        logger.warning("Keyword cannot be empty.")
        return

    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    scraper = LinkedInScraper(logger=logger, headless=False)
    
    try:
        # Step 1: Login
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        scraper.login(email=email, password=password)
        
        # Step 2: Search for posts
        date_posted_env = os.getenv("LINKEDIN_DATE_POSTED")
        date_filters = None
        if date_posted_env:
            date_filters = [d.strip() for d in date_posted_env.split(',') if d.strip()]
            
        # Note: You can change max_posts to collect more posts
        posts = scraper.search_posts(keyword=keyword, max_posts=10, date_filters=date_filters)
        
        if not posts:
            logger.warning("No posts found or scraping failed.")
            return
            
        logger.info(f"Successfully scraped {len(posts)} posts.")
        
        # Load resume if available
        resume_data = None
        resume_path = os.path.join(data_dir, 'resume.json')
        if os.path.exists(resume_path):
            try:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                logger.info("Loaded resume.json successfully.")
            except Exception as e:
                logger.warning(f"Could not load resume.json: {e}")
                
        # Initialize LLM Service
        llm_service = LLMService(logger=logger, resume_data=resume_data)
        
        # Initialize Auto-Apply Components
        from src.job_seeker.emailer import EmailClient
        from src.job_seeker.resume_builder import ResumeBuilder
        
        email_client = EmailClient(logger=logger)
        resume_builder = ResumeBuilder(logger=logger)
        
        # Step 3: Analyze posts
        analyzer = PostAnalyzer(
            logger=logger, 
            llm_service=llm_service,
            email_client=email_client,
            resume_builder=resume_builder,
            resume_data=resume_data
        )
        df = analyzer.analyze(posts)
        
        # Step 4: Save to CSV and MD
        output_file = os.path.join(data_dir, f'linkedin_posts_{keyword.replace(" ", "_")}.csv')
        analyzer.save_to_csv(df, output_file)
        
        md_file = os.path.join(data_dir, f'linkedin_posts_{keyword.replace(" ", "_")}.md')
        analyzer.save_to_md(df, md_file)
        
        logger.info("Process completed successfully!")
        logger.info(f"Check the output files in {data_dir}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        
    finally:
        # Ensure browser is closed even if there's an error
        scraper.close()

if __name__ == "__main__":
    main()
