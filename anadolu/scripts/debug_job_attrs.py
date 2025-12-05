
import os
import sys
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    job = client.batches.get(name="batches/e8khbm9snnbvqmi34wiywhr2zdpf2f1xpx1f")
    print(f"Stats: {job.completion_stats}")
    print(f"State: {job.state}")
except Exception as e:
    print(e)
