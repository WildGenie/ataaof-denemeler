#!/usr/bin/env python3
"""
Submit a JSONL file to Gemini Batch API.
"""

import os
import sys
import time
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def upload_file(file_path):
    print(f"Uploading {file_path}...")
    try:
        # Note: 'batch' purpose is assumed for batch jobs
        file_ref = client.files.upload(file=file_path, config={'mime_type': 'application/json'})
        print(f"File uploaded: {file_ref.name} (State: {file_ref.state})")

        # Wait for file to be active
        while file_ref.state.name == "PROCESSING":
            print("Waiting for file processing...")
            time.sleep(2)
            file_ref = client.files.get(name=file_ref.name)

        if file_ref.state.name != "ACTIVE":
            print(f"File upload failed with state: {file_ref.state}")
            return None

        return file_ref.name
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def submit_job(file_resource_name, display_name="Batch Job"):
    print(f"Submitting batch job with file: {file_resource_name}")
    try:
        job = client.batches.create(
            model="models/gemini-flash-latest",
            src=file_resource_name,
            config={
                "dest": f"gs://{file_resource_name}-output" if False else None # Output to GCS or default? Default is separate file download.
            }
        )
        print(f"Job submitted successfully!")
        print(f"Job Name: {job.name}")
        print(f"Initial State: {job.state}")
        return job.name
    except Exception as e:
        print(f"Error submitting job: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 submit_batch.py <path_to_jsonl>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    if not os.path.exists(jsonl_path):
        print(f"File not found: {jsonl_path}")
        sys.exit(1)

    file_uri = upload_file(jsonl_path)
    if not file_uri:
        sys.exit(1)

    job_name = submit_job(file_uri, display_name=f"Similarity Analysis {os.path.basename(jsonl_path)}")

    if job_name:
        print("\nUse the following command to check status:")
        print(f"python3 anadolu/scripts/check_batch_status.py --monitor {job_name}")

if __name__ == "__main__":
    main()
