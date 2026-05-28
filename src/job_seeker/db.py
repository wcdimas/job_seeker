import sqlite3
import os
import hashlib
from datetime import datetime
import pandas as pd

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
        
    def get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_hash TEXT UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    is_job_posting BOOLEAN,
                    is_remote_or_sponsored BOOLEAN,
                    application_links TEXT,
                    emails TEXT,
                    required_skills TEXT,
                    match_score INTEGER,
                    match_reason TEXT,
                    status TEXT DEFAULT 'NEW',
                    post_url TEXT,
                    author_profile TEXT,
                    connection_invite TEXT,
                    email_body TEXT
                )
            ''')
            
            # Migration: Add new columns if they don't exist
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN post_url TEXT")
            except sqlite3.OperationalError:
                pass # Column already exists
                
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN author_profile TEXT")
            except sqlite3.OperationalError:
                pass # Column already exists
                
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN connection_invite TEXT")
            except sqlite3.OperationalError:
                pass # Column already exists
                
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN email_body TEXT")
            except sqlite3.OperationalError:
                pass # Column already exists
                
            conn.commit()
            
    def generate_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
        
    def post_exists(self, text):
        post_hash = self.generate_hash(text)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM jobs WHERE post_hash = ?', (post_hash,))
            return cursor.fetchone() is not None
            
    def insert_post(self, text, result_dict, post_url=None, author_profile=None):
        post_hash = self.generate_hash(text)
        scraped_at = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO jobs (
                        post_hash, text, scraped_at, is_job_posting, is_remote_or_sponsored, 
                        application_links, emails, required_skills, match_score, match_reason,
                        post_url, author_profile, connection_invite, email_body
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_hash, 
                    text, 
                    scraped_at,
                    result_dict.get('is_job_posting', False),
                    result_dict.get('is_remote_or_sponsored', False),
                    result_dict.get('application_links', ''),
                    result_dict.get('emails', ''),
                    result_dict.get('required_skills', ''),
                    result_dict.get('match_score', 0),
                    result_dict.get('match_reason', ''),
                    post_url,
                    author_profile,
                    result_dict.get('connection_invite', ''),
                    result_dict.get('email_body', '')
                ))
                conn.commit()
            except sqlite3.IntegrityError:
                pass # Ignore if hash already exists
                
    def get_new_jobs_df(self):
        """Returns a Pandas DataFrame of all jobs with status='NEW' and is_job_posting=True."""
        with self.get_connection() as conn:
            query = "SELECT id, is_job_posting, is_remote_or_sponsored, match_score, required_skills, emails, match_reason, text FROM jobs WHERE status = 'NEW' AND is_job_posting = 1 ORDER BY match_score DESC"
            df = pd.read_sql_query(query, conn)
            # Map sqlite 1/0 back to boolean
            df['is_job_posting'] = df['is_job_posting'].astype(bool)
            df['is_remote_or_sponsored'] = df['is_remote_or_sponsored'].astype(bool)
            return df
            
    def mark_applied(self, job_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET status = 'APPLIED' WHERE id = ?", (job_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            return False
