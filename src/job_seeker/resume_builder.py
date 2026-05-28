import os
import json
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions
import tempfile
import time

class ResumeBuilder:
    def __init__(self, logger):
        self.logger = logger
        
    def build_resume_pdf(self, resume_data, tailored_summary, tailored_skills, output_path):
        """
        Builds an HTML resume and converts it to PDF using Headless Chrome.
        """
        self.logger.info("Generating tailored HTML resume...")
        
        # Override with tailored sections
        if tailored_summary:
            resume_data['summary'] = tailored_summary
            
        # The tailored_skills from LLM is a list of strings, so we replace the dict categories with a single list
        skills_html = ""
        if tailored_skills:
            skills_html = f"<div class='skills-list'>" + "".join([f"<span class='skill-tag'>{s}</span>" for s in tailored_skills]) + "</div>"
        else:
            # Fallback to original dict
            for category, skills in resume_data.get('skills', {}).items():
                cat_name = category.replace('_', ' ').title()
                skills_html += f"<div><strong>{cat_name}:</strong> {', '.join(skills)}</div>"
                
        # Build HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Resume - {resume_data['personal_information']['name']}</title>
            <style>
                @page {{ size: A4; margin: 15mm; }}
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; margin: 0; padding: 0; }}
                h1 {{ margin: 0 0 5px 0; color: #2c3e50; font-size: 28px; }}
                .contact-info {{ font-size: 13px; color: #666; margin-bottom: 20px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .contact-info a {{ color: #3498db; text-decoration: none; }}
                h2 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 20px; font-size: 18px; }}
                p {{ margin: 0 0 10px 0; font-size: 14px; text-align: justify; }}
                .experience-item, .education-item {{ margin-bottom: 15px; }}
                .header {{ display: flex; justify-content: space-between; align-items: baseline; }}
                .title {{ font-weight: bold; font-size: 15px; }}
                .company {{ font-style: italic; color: #555; font-size: 14px; }}
                .period {{ font-size: 13px; color: #777; }}
                ul {{ margin: 5px 0 10px 0; padding-left: 20px; font-size: 14px; }}
                li {{ margin-bottom: 4px; text-align: justify; }}
                .skill-tag {{ display: inline-block; background-color: #f1f2f6; border: 1px solid #dcdde1; padding: 3px 8px; margin: 3px; border-radius: 4px; font-size: 12px; color: #2f3640; }}
                .skills-list {{ display: flex; flex-wrap: wrap; }}
            </style>
        </head>
        <body>
            <div class="header-main">
                <h1>{resume_data['personal_information']['name']}</h1>
                <div class="contact-info">
                    {resume_data['personal_information']['location']} | 
                    {resume_data['personal_information']['email']} | 
                    {resume_data['personal_information']['phone']}<br>
                    <a href="{resume_data['personal_information']['links'].get('linkedin', '')}">LinkedIn</a> | 
                    <a href="{resume_data['personal_information']['links'].get('github', '')}">GitHub</a>
                </div>
            </div>
            
            <h2>Summary</h2>
            <p>{resume_data['summary']}</p>
            
            <h2>Skills</h2>
            {skills_html}
            
            <h2>Experience</h2>
        """
        
        for exp in resume_data.get('experience', []):
            html_content += f"""
            <div class="experience-item">
                <div class="header">
                    <span class="title">{exp['title']}</span>
                    <span class="period">{exp['period']}</span>
                </div>
                <div class="company">{exp['company']} - {exp['location']}</div>
                <ul>
            """
            for resp in exp.get('responsibilities', []):
                html_content += f"<li>{resp}</li>"
            html_content += "</ul></div>"
            
        html_content += "<h2>Education</h2>"
        for edu in resume_data.get('education', []):
            html_content += f"""
            <div class="education-item">
                <div class="header">
                    <span class="title">{edu['degree']}</span>
                    <span class="period">{edu['period']}</span>
                </div>
                <div class="company">{edu['institution']} - {edu['location']}</div>
                <p>{edu['description']}</p>
            </div>
            """
            
        html_content += """
        </body>
        </html>
        """
        
        # Write to temp HTML file
        temp_dir = tempfile.gettempdir()
        temp_html_path = os.path.join(temp_dir, "temp_resume.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # Use Selenium to print to PDF
        self.logger.info("Converting HTML to PDF via Headless Chrome...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(f"file:///{temp_html_path.replace(chr(92), '/')}")
            time.sleep(1) # wait for render
            
            print_options = PrintOptions()
            print_options.page_ranges = ['1-2']
            pdf_base64 = driver.print_page(print_options)
            
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(pdf_base64))
                
            self.logger.info(f"Successfully generated PDF: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            return False
        finally:
            driver.quit()
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)
