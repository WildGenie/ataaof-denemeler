import os
from dotenv import load_dotenv
from google import genai

# Add project root to sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing caches...")
try:
    caches = client.caches.list()
    count = 0
    for cache in caches:
        print(f"Cache: {cache.name}")
        print(f"  Model: {cache.model}")
        print(f"  Create Time: {cache.create_time}")
        print(f"  Expire Time: {cache.expire_time}")
        print("-" * 20)
        count += 1

    if count == 0:
        print("No caches found.")
    else:
        print(f"Total caches: {count}")

except Exception as e:
    print(f"Error listing caches: {e}")
