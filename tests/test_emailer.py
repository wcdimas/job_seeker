import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.job_seeker.emailer import EmailClient

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestEmailer")

def test_emailer():
    # Load .env file
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    client = EmailClient(logger=logger)
    
    if not client.is_configured():
        logger.error("Azure credentials not configured in .env! Cannot run test.")
        logger.error("Please add AZURE_CLIENT_ID and AZURE_CLIENT_SECRET to your .env file.")
        return
        
    # The first time this runs, it will pause and print a URL for the user to visit
    if not client.authenticate_if_needed():
        logger.error("Authentication failed. Cannot proceed with email test.")
        return
        
    # Send a test email to YOURSELF to verify it works
    # Using LINKEDIN_EMAIL as a fallback test recipient if needed
    test_email_address = os.getenv("LINKEDIN_EMAIL", "wescleydecarvalho@hotmail.com")
    
    test_subject = "Job Seeker Bot - OAuth2 Test Email"
    test_body = "Hello!\n\nThis is a test email sent from your Job Seeker bot via the modern Microsoft Graph API (OAuth2) to verify settings are working perfectly."
    
    # Optionally attach the test resume if it was generated
    test_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'test_resume_output.pdf'))
    attachment = test_pdf if os.path.exists(test_pdf) else None
    
    logger.info(f"Sending test email to {test_email_address}...")
    success = client.send_application(
        to_email=test_email_address,
        subject=test_subject,
        body=test_body,
        attachment_path=attachment
    )
    
    if success:
        logger.info("Test passed! Check your inbox for the test email.")
    else:
        logger.error("Test failed. Email was not sent.")

if __name__ == "__main__":
    test_emailer()
