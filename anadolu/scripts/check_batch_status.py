#!/usr/bin/env python3
"""
Check and manage Gemini Batch API job statuses.
Reads batch request keys from JSONL file and checks their status.
"""

import os
import json
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tqdm import tqdm

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
BATCH_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "Anadolu", "batch_requests.jsonl")
BATCH_STATUS_FILE = os.path.join(OUTPUT_DIR, "Anadolu", "batch_status.json")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

# Configure SDK
client = genai.Client(api_key=GEMINI_API_KEY)

def load_batch_requests():
    """Load batch request keys from JSONL file."""
    if not os.path.exists(BATCH_REQUESTS_FILE):
        print(f"Error: {BATCH_REQUESTS_FILE} not found")
        return []

    keys = []
    with open(BATCH_REQUESTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            req = json.loads(line)
            keys.append(req.get("key"))

    return keys

def load_batch_status():
    """Load saved batch status."""
    if os.path.exists(BATCH_STATUS_FILE):
        try:
            with open(BATCH_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_batch_status(status):
    """Save batch status to file."""
    with open(BATCH_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def list_all_batch_jobs():
    """List all batch jobs."""
    print("\n📋 Listing all batch jobs...")
    try:
        jobs = client.batches.list()

        if not jobs:
            print("No batch jobs found.")
            return []

        job_list = []
        for job in jobs:
            job_info = {
                "name": job.name,
                "state": str(job.state),
                "display_name": getattr(job, 'display_name', 'N/A'),
                "create_time": str(getattr(job, 'create_time', 'N/A')),
                "model": getattr(job, 'model', 'N/A')
            }
            job_list.append(job_info)

            # Print job info
            print(f"\n  Job: {job.name}")
            print(f"  Display Name: {job_info['display_name']}")
            print(f"  State: {job_info['state']}")
            print(f"  Model: {job_info['model']}")
            print(f"  Created: {job_info['create_time']}")

        return job_list
    except Exception as e:
        print(f"Error listing jobs: {e}")
        return []

def check_job_status(job_name):
    """Check status of a specific batch job."""
    try:
        job = client.batches.get(name=job_name)

        state = str(job.state)

        info = {
            "name": job.name,
            "state": state,
            "display_name": getattr(job, 'display_name', 'N/A'),
            "model": getattr(job, 'model', 'N/A'),
            "request_count": getattr(job, 'request_count', 0),
            "processed_count": getattr(job, 'completed_request_count', getattr(job, 'processed_count', 0)), # Try different SDK field names
            "succeeded_count": getattr(job, 'succeeded_count', 0),
            "failed_count": getattr(job, 'failed_count', 0),
        }

        # Add result file if succeeded
        if "SUCCEEDED" in state:
            if hasattr(job, 'dest') and hasattr(job.dest, 'file_name'):
                info['result_file'] = job.dest.file_name

        # Add error if failed
        if "FAILED" in state:
            if hasattr(job, 'error'):
                info['error'] = str(job.error)

        return info
    except Exception as e:
        return {"error": str(e)}

def download_results(job_name, output_path):
    """Download results from a completed batch job."""
    try:
        job = client.batches.get(name=job_name)

        state = str(job.state)
        if "SUCCEEDED" not in state:
            print(f"Job {job_name} is not in SUCCEEDED state (current: {state})")
            return False

        result_filename = job.dest.file_name
        print(f"Downloading results from {result_filename}...")

        results_content = client.files.download(file=result_filename).decode('utf-8')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(results_content)

        print(f"✅ Results saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading results: {e}")
        return False

def cancel_job(job_name):
    """Cancel a running batch job."""
    try:
        print(f"Cancelling job {job_name}...")
        client.batches.cancel(name=job_name)
        print(f"✅ Job {job_name} cancelled")
        return True
    except Exception as e:
        print(f"Error cancelling job: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check and manage Gemini Batch API jobs")
    parser.add_argument("--list", action="store_true", help="List all batch jobs")
    parser.add_argument("--check", help="Check status of a specific job by name")
    parser.add_argument("--download", help="Download results from a job")
    parser.add_argument("--output", help="Output file for downloaded results")
    parser.add_argument("--cancel", help="Cancel a running job")
    parser.add_argument("--monitor", help="Monitor a job until completion")

    args = parser.parse_args()

    if args.list:
        jobs = list_all_batch_jobs()
        print(f"\n📊 Total jobs: {len(jobs)}")

    elif args.check:
        print(f"\n🔍 Checking job: {args.check}")
        info = check_job_status(args.check)
        print(json.dumps(info, indent=2))

    elif args.download:
        if not args.output:
            print("Error: --output required for download")
            return
        download_results(args.download, args.output)

    elif args.cancel:
        cancel_job(args.cancel)

    elif args.monitor:
        print(f"\n👀 Monitoring job: {args.monitor}")

        with tqdm(desc="Waiting for job completion", unit="check") as pbar:
            while True:
                info = check_job_status(args.monitor)
                state = info.get("state", "UNKNOWN")

                # Robust state checking
                is_succeeded = "SUCCEEDED" in state
                is_failed = "FAILED" in state
                is_cancelled = "CANCELLED" in state

                pbar.set_description(f"Status: {state}")

                if is_succeeded or is_failed or is_cancelled:
                    print(f"\n✅ Job finished with state: {state}")
                    print(json.dumps(info, indent=2))
                    break

                pbar.update(1)
                time.sleep(30)

    else:
        # Default: list all jobs
        jobs = list_all_batch_jobs()
        print(f"\n📊 Total jobs: {len(jobs)}")

if __name__ == "__main__":
    main()
