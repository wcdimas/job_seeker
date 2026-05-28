import os
import sys
import json
import logging

# Add the project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.job_seeker.resume_builder import ResumeBuilder

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestResumeBuilder")

def test_resume_builder():
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'resume.json'))
    
    if not os.path.exists(resume_path):
        logger.error(f"Cannot find resume.json at {resume_path}")
        return

    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
        
    builder = ResumeBuilder(logger=logger)
    
    # Dummy tailored data
    tailored_summary = "This is a TEST tailored summary. I am an expert in Python, RPA, and testing automated systems. I am highly motivated to join your company."
    tailored_skills = ["Python", "Selenium", "Test-Driven Development", "RPA", "UiPath"]
    
    output_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'test_resume_output.pdf'))
    
    logger.info("Starting resume generation test...")
    success = builder.build_resume_pdf(resume_data, tailored_summary, tailored_skills, output_pdf)
    
    if success:
        logger.info(f"Test passed! Check {output_pdf} to see the generated resume.")
    else:
        logger.error("Test failed. PDF was not generated.")

if __name__ == "__main__":
    test_resume_builder()
