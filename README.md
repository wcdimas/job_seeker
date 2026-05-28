# 🤖 Autonomous Job Seeker Agent

A powerful, fully autonomous agent that acts as your personal technical recruiter. It automatically scrapes LinkedIn for job posts, uses Google's Gemini AI to evaluate your fit for the role, generates a custom-tailored PDF resume, and automatically sends highly personalized application emails to recruiters via Microsoft Graph API. It also features a sleek Web Dashboard to monitor all activities.

## ✨ Key Features

- **LinkedIn Scraper**: Uses Selenium to dynamically scroll and extract recent job postings based on custom keywords and date filters.
- **AI-Powered Evaluation (Gemini 3.1 Flash Lite)**: Analyzes job descriptions against your resume, generating a "Match Score". 
- **Dynamic Resume Builder**: Automatically generates a professional PDF resume tailored to the specific company using WeasyPrint.
- **Automated Email Outreach**: Drafts a highly persuasive HTML email highlighting your exact matching skills and automatically sends it to the recruiter using Microsoft Graph API (O365).
- **Web Dashboard**: A beautiful, real-time FastAPI + Vanilla JS dashboard to view all scraped jobs, LLM reasoning, generated emails, and connection invite drafts.
- **Smart Rate Limiting**: Built-in logic to stay under Gemini free-tier API quotas.

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Poetry** (for dependency management)
- Google Gemini API Key
- Microsoft Azure App credentials (for sending emails via Outlook/Hotmail)
- Google Chrome installed (for Selenium)
- GTK3 installed (required for WeasyPrint PDF generation on Windows)

### 2. Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/wcdimas/job_seeker.git
cd job_seeker
poetry install
```

### 3. Configuration

1. Copy the example environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
2. Set up your personal resume JSON. Copy the template and fill it with your real data:
   ```bash
   cp resume.example.json data/resume.json
   ```
   *(Note: The `data/` folder is gitignored to protect your privacy).*

### 4. Microsoft Graph Authentication (First Run)
Before running the autonomous agent for the first time, you must authorize the app to send emails on your behalf:
```bash
poetry run python tests/test_email_self.py
```
A URL will appear in your console. Open it, log in to your Microsoft account, consent to the permissions, and paste the redirected URL back into the console.

## 🛠️ Usage

### Run the Autonomous Agent
To launch the agent in the background (it will scrape, analyze, and apply automatically):

```bash
poetry run python run_job_seeker.py
```

You can optionally pass arguments to customize the search without editing the `.env` file:
```bash
poetry run python run_job_seeker.py --keyword '"rpa" AND "python"' --date-filter "past-week" --max-hours 168
```

### Access the Dashboard
To monitor the agent's findings and read the AI-generated emails:
```bash
poetry run uvicorn src.job_seeker.web.api:app --host 0.0.0.0 --port 8000 --reload
```
Then open `http://localhost:8000` in your browser (or use your machine's IP address to access it from your phone).

## 🔒 Security & Privacy
This repository is configured with a strict `.gitignore` to ensure your sensitive data (passwords, tokens, `data/` folder, DB, and personal PDFs) are **never** committed to version control. 

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
