import sqlite3
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Job Seeker Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'jobs.db'))

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.get("/api/jobs")
def get_jobs():
    """Fetches all jobs from the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            # We sort by id DESC to get the newest first
            cursor.execute('''
                SELECT id, is_job_posting, is_remote_or_sponsored, 
                       match_score, match_reason, required_skills, emails,
                       status, post_url, author_profile, scraped_at, text
                FROM jobs 
                ORDER BY id DESC
            ''')
            return {"jobs": cursor.fetchall()}
    except Exception as e:
        return {"error": str(e), "jobs": []}

@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: int):
    """Fetches a single job's full details."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, is_job_posting, is_remote_or_sponsored, 
                       match_score, match_reason, required_skills, emails,
                       application_links, status, post_url, author_profile, 
                       scraped_at, text, connection_invite, email_body
                FROM jobs WHERE id = ?
            ''', (job_id,))
            job = cursor.fetchone()
            if job:
                return {"job": job}
            return {"error": "Job not found"}
    except Exception as e:
        return {"error": str(e)}

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    import uvicorn
    # Make sure to run from project root: poetry run python src/job_seeker/web/api.py
    uvicorn.run("src.job_seeker.web.api:app", host="0.0.0.0", port=8000, reload=True)
