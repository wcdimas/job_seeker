import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class JobAnalysisResult(BaseModel):
    is_job_posting: bool = Field(description="True if the text is a job opening/opportunity/hiring post, False otherwise.")
    is_remote_or_sponsored: bool = Field(description="True if the job explicitly mentions being Remote, offering Visa Sponsorship, or is located in Brazil. False if it requires being on-site outside of Brazil without sponsorship.")
    application_links: list[str] = Field(description="List of URLs to apply for the job, if any.")
    emails: list[str] = Field(description="List of email addresses found in the post.")
    required_skills: list[str] = Field(description="List of tools, technologies, or skills required for the job.")
    match_score: int = Field(description="A score from 0 to 100 indicating how well the candidate's profile matches the job requirements.")
    match_reason: str = Field(description="A one-sentence explanation of why this match score was given.")
    email_subject: str = Field(description="If match_score >= 80, draft an email subject for applying. Otherwise leave blank.")
    email_body: str = Field(description="If match_score >= 80, draft a highly professional, concise email tailored to the skills mentioned in the job post, explaining why the candidate is a great fit. Mention the attached resume. Otherwise leave blank.")
    tailored_summary: str = Field(description="If match_score >= 80, write a 2-3 sentence resume summary emphasizing candidate's skills that directly match the job post. Otherwise leave blank.")
    tailored_skills: list[str] = Field(description="If match_score >= 80, output a prioritized list of the candidate's skills, putting the ones most relevant to the job at the top. Otherwise leave blank.")
    connection_invite_message: str = Field(description="A short message (max 200 characters) to be sent as a LinkedIn connection invite to the recruiter/author, introducing the candidate for the role.")
    company_name: str = Field(description="The name of the company hiring for the position, if mentioned. If not found or confidential, return 'Confidential'.")

class LLMService:
    def __init__(self, logger, resume_data=None):
        """
        Initializes the LLM Service using google-genai.
        """
        self.logger = logger
        self.resume_data = resume_data
        self.last_request_time = 0
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.warning("GEMINI_API_KEY not found in environment variables. LLM analysis will fail.")
            self.client = None
        else:
            try:
                # The modern google-genai SDK
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None

    def analyze_post(self, post_text):
        """
        Analyzes a single post using Gemini and returns a JobAnalysisResult.
        """
        if not self.client:
            return None
            
        # Enforce rate limit (15 req/min = 1 req / 4s). We wait 4.2s to be safe.
        elapsed = time.time() - self.last_request_time
        if elapsed < 4.2:
            time.sleep(4.2 - elapsed)
        self.last_request_time = time.time()
            
        system_instruction = """You are an expert technical recruiter, executive assistant, and professional copywriter.
You will be provided with a job description and a candidate's resume (in JSON format).

Your task is to analyze the match between the candidate and the job, and return a JSON object containing:
1. 'match_score': an integer from 0 to 100 representing how well the candidate matches the job.
2. 'match_reason': a short string explaining the score.
3. 'emails': a list of any email addresses found in the job description.
4. 'email_subject': a professional, eye-catching subject line for an application email.
5. 'email_body': A highly persuasive, well-structured application email tailored to the specific job. 
   - MUST be formatted in HTML (use <p>, <br>, <ul>, <li>, and <strong> tags).
   - Do NOT output plain text; use HTML for proper paragraph spacing and emphasis.
   - Include a professional greeting.
   - Write an engaging opening paragraph expressing interest in the specific role.
   - Include a bulleted list (using <ul> and <li>) of 2-3 key achievements or skills from the candidate's resume that perfectly align with the job requirements.
   - Include a confident closing paragraph mentioning the attached resume.
   - Add a professional sign-off with the candidate's name.
6. 'tailored_summary': a tailored version of the candidate's professional summary.
7. 'tailored_skills': a tailored list of skills relevant to the job.
8. 'connection_invite_message': A short text (max 200 characters) to be sent as a LinkedIn connection invite to the recruiter/author, introducing the candidate for the role.
9. 'company_name': The name of the company hiring. If not specified or confidential, output 'Confidential'.
If the job strictly requires being on-site outside of Brazil without visa sponsorship, set the match_score to 0.
If the match_score < 80, leave the email and tailored resume fields empty or blank. You can still generate the connection invite if it's a good match but didn't reach 80."""
        
        prompt = f"### LinkedIn Post:\n{post_text}\n\n"
        if self.resume_data:
            prompt += f"### Candidate Profile (Resume):\n{json.dumps(self.resume_data, indent=2)}\n\n"
            
        try:
            response = self.client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=JobAnalysisResult,
                    temperature=0.2,
                ),
            )
            
            # The response text will be a valid JSON string matching the JobAnalysisResult schema
            result_dict = json.loads(response.text)
            return JobAnalysisResult(**result_dict)
            
        except Exception as e:
            self.logger.error(f"Error during LLM analysis: {e}")
            return None
