import pandas as pd
import re
from src.job_seeker.db import Database

class PostAnalyzer:
    def __init__(self, logger, llm_service=None, email_client=None, resume_builder=None, resume_data=None):
        """
        Initializes the PostAnalyzer.
        """
        self.logger = logger
        self.llm_service = llm_service
        self.email_client = email_client
        self.resume_builder = resume_builder
        self.resume_data = resume_data
        
        # Keywords to quickly pre-filter if a post is likely a job
        self.job_keywords = re.compile(
            r'\b(hiring|vaga|opportunity|apply|looking for|contratando|oportunidade|vacancy|role|position)\b', 
            re.IGNORECASE
        )
        self.db = Database('data/jobs.db')

    def analyze(self, posts):
        """
        Analyzes a list of posts, saves them to DB, and returns a DataFrame of all NEW jobs.
        """
        self.logger.info(f"Analyzing {len(posts)} posts...")
        
        new_posts_count = 0
        
        for i, post_data in enumerate(posts):
            text = str(post_data.get('text', ''))
            if not text or self.db.post_exists(text):
                continue
                
            new_posts_count += 1
            self.logger.info(f"Analyzing new post {i+1}/{len(posts)}...")
            
            # 1. Local Pre-Filter
            if not self.job_keywords.search(text):
                self.db.insert_post(text, {
                    'is_job_posting': False,
                    'is_remote_or_sponsored': False,
                    'application_links': '',
                    'emails': '',
                    'required_skills': '',
                    'match_score': 0,
                    'match_reason': 'Skipped by local filter (no job keywords found).'
                })
                continue
                
            # 2. LLM Analysis
            if self.llm_service and self.llm_service.client:
                res = self.llm_service.analyze_post(text)
                if res:
                    self.db.insert_post(
                        text, 
                        {
                            'is_job_posting': res.is_job_posting,
                            'is_remote_or_sponsored': res.is_remote_or_sponsored,
                            'application_links': ', '.join(res.application_links),
                            'emails': ', '.join(res.emails),
                            'required_skills': ', '.join(res.required_skills),
                            'match_score': res.match_score,
                            'match_reason': res.match_reason,
                            'connection_invite': res.connection_invite_message,
                            'email_body': res.email_body
                        },
                        post_url=post_data.get('post_url'),
                        author_profile=post_data.get('author_profile')
                    )
                    
                    # Auto-Apply Logic
                    if res.match_score >= 80 and res.emails:
                        first_email = res.emails[0]
                        self.logger.info(f"High match found ({res.match_score})! Preparing auto-application to {first_email}...")
                        
                        import copy
                        # Create tailored PDF
                        safe_data = copy.deepcopy(self.resume_data)
                        
                        # Use company name for PDF filename
                        company = getattr(res, 'company_name', 'Confidential')
                        company_clean = company if company and company != 'Confidential' else 'LinkedIn'
                        # Sanitize company name for file system
                        safe_company = "".join([c if c.isalnum() else "_" for c in company_clean]).strip("_")
                        pdf_path = f"data/CV_Wescley_{safe_company}.pdf"
                        
                        if self.resume_builder and self.resume_data:
                            success = self.resume_builder.build_resume_pdf(
                                safe_data, 
                                res.tailored_summary, 
                                res.tailored_skills, 
                                pdf_path
                            )
                        else:
                            success = False
                            pdf_path = None
                            
                        if self.email_client and self.email_client.is_configured():
                            mail_sent = self.email_client.send_application(
                                to_email=first_email,
                                subject=res.email_subject or f"Application for Role - {safe_data['personal_information']['name']}",
                                body=res.email_body or "Please find my resume attached.",
                                attachment_path=pdf_path if success else None
                            )
                            
                            if mail_sent:
                                # Fetch the inserted post's ID to mark it as applied
                                import hashlib
                                post_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                                with self.db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("SELECT id FROM jobs WHERE post_hash = ?", (post_hash,))
                                    row = cursor.fetchone()
                                    if row:
                                        self.db.mark_applied(row[0])
                                        self.logger.info(f"Successfully auto-applied and marked job {row[0]} as APPLIED.")
                else:
                    # Fallback if LLM fails
                    self.db.insert_post(
                        text, 
                        {
                            'is_job_posting': True, # It passed the regex filter
                            'is_remote_or_sponsored': False,
                            'application_links': '',
                            'emails': ', '.join(re.findall(r'[\w\.-]+@[\w\.-]+', text)),
                            'required_skills': '',
                            'match_score': 0,
                            'match_reason': 'LLM Analysis Failed'
                        },
                        post_url=post_data.get('post_url'),
                        author_profile=post_data.get('author_profile')
                    )
            else:
                 # Fallback if no LLM service is available
                 self.db.insert_post(
                     text, 
                     {
                         'is_job_posting': True,
                         'is_remote_or_sponsored': False,
                         'application_links': '',
                         'emails': ', '.join(re.findall(r'[\w\.-]+@[\w\.-]+', text)),
                         'required_skills': '',
                         'match_score': 0,
                         'match_reason': 'No LLM Service Available'
                     },
                     post_url=post_data.get('post_url'),
                     author_profile=post_data.get('author_profile')
                 )
                 
        self.logger.info(f"Found {new_posts_count} new posts out of {len(posts)} scraped.")
        
        # Return a dataframe of ALL unapplied (NEW) jobs for the markdown/CSV export
        return self.db.get_new_jobs_df()

    def save_to_csv(self, df, filepath):
        """
        Saves the DataFrame to a CSV file.
        """
        df.to_csv(filepath, index=False, encoding='utf-8')
        self.logger.info(f"Data saved to {filepath}")

    def save_to_md(self, df, filepath):
        """
        Saves a summary of the DataFrame to a Markdown file.
        """
        df_md = df.copy()
        if 'text' in df_md.columns:
            df_md['text'] = df_md['text'].astype(str).str.replace('\n', ' ', regex=False).str[:100] + '...'
            
        cols_to_show = ['id', 'is_job_posting', 'is_remote_or_sponsored', 'match_score', 'required_skills', 'emails', 'match_reason', 'text']
        cols_to_show = [c for c in cols_to_show if c in df_md.columns]
        
        md_content = '# Extracted LinkedIn Posts\n\n'
        md_content += 'This is a summary of the recently extracted posts. The full text has been truncated for readability.\n\n'
        
        md_content += df_md[cols_to_show].to_markdown(index=False)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        self.logger.info(f"Markdown summary saved to {filepath}")
