import sys
import os
from src.job_seeker.db import Database

def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_job.py <job_id>")
        print("You can find the job_id in the first column of the generated markdown/csv file.")
        sys.exit(1)
        
    try:
        job_id = int(sys.argv[1])
    except ValueError:
        print("Error: job_id must be an integer.")
        sys.exit(1)
        
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'jobs.db')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    db = Database(db_path)
    if db.mark_applied(job_id):
        print(f"Successfully marked Job ID {job_id} as APPLIED.")
        print("This job will no longer appear in your generated CSV/MD files.")
    else:
        print(f"Error: Could not find Job ID {job_id} with a 'NEW' status in the database.")

if __name__ == "__main__":
    main()
