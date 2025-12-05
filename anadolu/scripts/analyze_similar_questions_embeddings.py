#!/usr/bin/env python3
"""
Analyze similar questions using Gemini embeddings for semantic similarity.
More accurate than text-based comparison for finding conceptually similar questions.
"""

import os
import json
import sys
from dotenv import load_dotenv
from google import genai
import numpy as np
from tqdm import tqdm

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")
CACHE_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "question_embeddings_cache.json")

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_embedding(text):
    """Get embedding for a text using Gemini API."""
    try:
        response = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def load_cache():
    """Load cached embeddings."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Save embeddings cache."""
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze similar questions using embeddings.")
    parser.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold (0-1)")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses")
    parser.add_argument("--course", help="Filter by course name")

    args = parser.parse_args()

    print("Starting embedding-based similarity analysis...")
    print(f"Similarity threshold: {args.threshold}")

    # Load cache
    cache = load_cache()
    print(f"Loaded {len(cache)} cached embeddings.")

    # Collect questions
    questions_by_course = {}

    enrolled_courses = set()
    if args.enrolled:
        enrolled_file = os.path.join(PROJECT_ROOT, "anadolu", "enrolled_courses.json")
        dersler_file = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")

        if os.path.exists(enrolled_file) and os.path.exists(dersler_file):
            with open(enrolled_file, 'r', encoding='utf-8') as f:
                enrolled_data = json.load(f)
                enrolled_codes = {c.get("kod") for c in enrolled_data}

            with open(dersler_file, 'r', encoding='utf-8') as f:
                dersler_data = json.load(f)

            for ders in dersler_data:
                if ders.get("DersKodu") in enrolled_codes:
                    enrolled_courses.add(ders.get("CourseName"))

    # Scan JSON files
    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" in filename:
                file_path = os.path.join(donem_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    course_name = filename.split(" - ")[2]

                    # Filter by enrolled
                    if args.enrolled and course_name not in enrolled_courses:
                        continue

                    # Filter by course name
                    if args.course and args.course.lower() not in course_name.lower():
                        continue

                    questions_by_course[course_name] = data.get("questions", [])

                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    print(f"Processing {len(questions_by_course)} courses...")

    # Generate embeddings for all questions
    all_questions = []
    for course_name, questions in questions_by_course.items():
        for q in questions:
            if q.get("question"):
                all_questions.append({
                    "course": course_name,
                    "question": q
                })

    print(f"Total questions: {len(all_questions)}")

    # Get embeddings (with caching)
    embeddings = []
    cache_updated = False

    for item in tqdm(all_questions, desc="Generating embeddings"):
        q_text = item["question"]["question"]
        q_id = f"{item['course']}_{item['question'].get('id')}"

        if q_id in cache:
            embeddings.append(cache[q_id])
        else:
            emb = get_embedding(q_text)
            if emb:
                cache[q_id] = emb
                embeddings.append(emb)
                cache_updated = True
            else:
                embeddings.append(None)

    if cache_updated:
        save_cache(cache)
        print("Cache updated.")

    # Find similar pairs
    print("Finding similar pairs...")
    similar_pairs = []

    n = len(all_questions)
    for i in tqdm(range(n), desc="Comparing"):
        if embeddings[i] is None:
            continue

        for j in range(i + 1, n):
            if embeddings[j] is None:
                continue

            # Skip if same course (optional)
            # if all_questions[i]["course"] == all_questions[j]["course"]:
            #     continue

            similarity = cosine_similarity(embeddings[i], embeddings[j])

            if similarity >= args.threshold:
                similar_pairs.append({
                    "similarity": float(similarity),
                    "q1": {
                        "course": all_questions[i]["course"],
                        "id": all_questions[i]["question"].get("id"),
                        "text": all_questions[i]["question"]["question"],
                        "source": all_questions[i]["question"].get("source"),
                        "answer": all_questions[i]["question"]["options"][all_questions[i]["question"]["correctIndex"]]
                            if all_questions[i]["question"].get("options") and
                               0 <= all_questions[i]["question"].get("correctIndex", -1) < len(all_questions[i]["question"]["options"])
                            else None
                    },
                    "q2": {
                        "course": all_questions[j]["course"],
                        "id": all_questions[j]["question"].get("id"),
                        "text": all_questions[j]["question"]["question"],
                        "source": all_questions[j]["question"].get("source"),
                        "answer": all_questions[j]["question"]["options"][all_questions[j]["question"]["correctIndex"]]
                            if all_questions[j]["question"].get("options") and
                               0 <= all_questions[j]["question"].get("correctIndex", -1) < len(all_questions[j]["question"]["options"])
                            else None
                    }
                })

    # Sort by similarity
    similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # Save report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(similar_pairs, f, indent=4, ensure_ascii=False)

    print(f"\nFound {len(similar_pairs)} similar pairs.")
    print(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    main()
