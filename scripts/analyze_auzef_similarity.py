import os
import json
import hashlib
import time
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm
import glob
import re

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Auzef", "json")
CACHE_PATH = os.path.join(PROJECT_ROOT, "output", "Auzef", "auzef_embeddings_cache.json")

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_embedding(text):
    try:
        response = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    # 1. Collect all unique questions
    print("Collecting questions...")
    json_files = glob.glob(os.path.join(AUZEF_JSON_DIR, "**", "*.json"), recursive=True)

    questions = []
    for file_path in json_files:
        if "user-courses.json" in file_path: continue
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            course_name = data.get("meta", {}).get("course_name", "Unknown")
            for q in data.get("questions", []):
                questions.append({
                    "id": q.get("id"),
                    "text": q.get("question"),
                    "clean_text": normalize_text(q.get("question")),
                    "course": course_name,
                    "file": file_path
                })

    print(f"Found {len(questions)} questions.")

    # 2. Load/Update Cache
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)

    # 3. Generate Embeddings
    print("Checking/Generating embeddings...")
    updated = False
    for q in tqdm(questions):
        text_hash = hashlib.sha256(q["clean_text"].encode('utf-8')).hexdigest()
        if text_hash not in cache:
            emb = get_embedding(q["text"])
            if emb:
                cache[text_hash] = emb
                updated = True
                time.sleep(0.2) # Rate limiting

    if updated:
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f)

    # 4. Analyze Similarity
    print("Analyzing similarity (this may take a moment)...")
    similar_pairs = []
    threshold = 0.95

    # Pre-calculate hashes and get embeddings from cache
    for q in questions:
        q["hash"] = hashlib.sha256(q["clean_text"].encode('utf-8')).hexdigest()
        q["emb"] = cache.get(q["hash"])

    # Nested loop for comparison (only within the same course or all?)
    # User asked for "any other duplicates", so let's check within each course first
    courses = set(q["course"] for q in questions)

    for course in courses:
        course_qs = [q for q in questions if q["course"] == course]
        if len(course_qs) < 2: continue

        print(f"Analysing {course}...")
        for i in range(len(course_qs)):
            for j in range(i + 1, len(course_qs)):
                q1 = course_qs[i]
                q2 = course_qs[j]

                if not q1["emb"] or not q2["emb"]: continue

                sim = cosine_similarity(q1["emb"], q2["emb"])
                if sim >= threshold:
                    # Skip if exact text was already caught (though converter should have removed them)
                    if q1["clean_text"] != q2["clean_text"]:
                        similar_pairs.append({
                            "course": course,
                            "similarity": float(sim),
                            "q1_id": q1["id"],
                            "q1_text": q1["text"],
                            "q2_id": q2["id"],
                            "q2_text": q2["text"]
                        })

    # 5. Report
    print("\n" + "="*50)
    print(f"SIMILARITY REPORT (Threshold: {threshold})")
    print("="*50)

    if not similar_pairs:
        print("No near-duplicates found (textually different but semantically 95%+ similar).")
    else:
        for p in sorted(similar_pairs, key=lambda x: x["similarity"], reverse=True):
            print(f"Course: {p['course']}")
            print(f"Similarity: {p['similarity']:.4f}")
            print(f"  Q1 ({p['q1_id']}): {p['q1_text'][:100]}...")
            print(f"  Q2 ({p['q2_id']}): {p['q2_text'][:100]}...")
            print("-" * 30)

if __name__ == "__main__":
    main()
