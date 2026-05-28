import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.job_seeker.llm_service import LLMService
from src.job_seeker.emailer import EmailClient
from src.job_seeker.resume_builder import ResumeBuilder

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPipeline")

def test_full_pipeline():
    # Load .env file
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    # 1. Load Resume
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'resume.json'))
    if not os.path.exists(resume_path):
        logger.error(f"Cannot find resume.json at {resume_path}")
        return
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
        
    # 2. Initialize Services
    llm_service = LLMService(logger=logger, resume_data=resume_data)
    email_client = EmailClient(logger=logger)
    resume_builder = ResumeBuilder(logger=logger)
    
    if not llm_service.client:
        logger.error("Gemini API Key not configured. Cannot run test.")
        return
        
    if not email_client.is_configured():
        logger.error("Azure credentials not configured. Cannot run test.")
        return

    # 3. Create a Dummy LinkedIn Post guaranteed to match Wescley's profile
    my_email = os.getenv("LINKEDIN_EMAIL", "wescleydecarvalho@hotmail.com")
    
    dummy_post = f"""
    🚀 WE ARE HIRING! 🚀
    We are looking for a Senior RPA Developer & Python Software Engineer to join our fully remote team!
    
    Requirements:
    - 3+ years of experience with enterprise RPA platforms (UiPath, Power Automate, Automation Anywhere).
    - Strong backend development skills in Python and cloud architecture (AWS).
    - Experience building scalable data pipelines and asynchronous processing.
    - Located in Brazil or willing to work remotely.
    
    This is a perfect opportunity for someone who loves automating complex workflows!
    Please send your application and resume to our lead recruiter at: {my_email}
    """
    
    logger.info("Sending dummy post to Gemini for analysis and email drafting...")
    
    # 4. Analyze Post
    res = llm_service.analyze_post(dummy_post)
    
    if not res:
        logger.error("LLM failed to return a valid response.")
        return
        
    logger.info(f"Match Score: {res.match_score}")
    logger.info(f"Match Reason: {res.match_reason}")
    logger.info(f"Extracted Emails: {res.emails}")
    
    if res.match_score < 80:
        logger.warning(f"Score was only {res.match_score}. The pipeline requires >= 80 to auto-apply.")
        return
        
    if not res.emails:
        logger.warning("No emails extracted. Cannot auto-apply.")
        return
        
    # 5. Build Tailored Resume
    logger.info("High match! Building tailored resume PDF...")
    import copy
    safe_data = copy.deepcopy(resume_data)
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'pipeline_test_resume.pdf'))
    
    success = resume_builder.build_resume_pdf(
        safe_data, 
        res.tailored_summary, 
        res.tailored_skills, 
        pdf_path
    )
    
    if not success:
        logger.error("Failed to build PDF.")
        return
        
    # 6. Send Email
    target_email = res.emails[0]
    logger.info(f"Sending tailored application email to {target_email}...")
    
    mail_sent = email_client.send_application(
        to_email=target_email,
        subject=res.email_subject or "Application for Senior RPA Developer",
        body=res.email_body or "Please find my resume attached.",
        attachment_path=pdf_path
    )
    
    if mail_sent:
        logger.info("Pipeline Test Complete! Check your inbox to see the AI-generated email and tailored PDF.")
    else:
        logger.error("Pipeline Test Failed at email sending stage.")

if __name__ == "__main__":
    test_full_pipeline()
