#!/usr/bin/env python3
"""
Generate embeddings for all questions in batch with metadata tracking.
Supports incremental updates - only regenerates embeddings for modified questions.
Uses EmbeddingStore for efficient storage (NumPy + JSON).
"""

import os
import json
import sys
import hashlib
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from anadolu.scripts.embedding_store import EmbeddingStore

JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
ANADOLU_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")
OLD_CACHE_PATH = os.path.join(ANADOLU_OUTPUT_DIR, "question_embeddings_cache.json")

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def get_question_hash(question_text):
    """Generate SHA256 hash of question text."""
    return hashlib.sha256(question_text.encode('utf-8')).hexdigest()

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

def load_questions(course_filter=None, donem_filter=None):
    """Collect all questions from JSON files."""
    questions = []

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        # Filter by donem if specified
        if donem_filter:
            try:
                current_donem = int(donem_dir.split(" ")[1])
                if current_donem != donem_filter:
                    continue
            except (IndexError, ValueError):
                continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename:
                continue

            file_path = os.path.join(donem_path, filename)
            course_name = filename.split(" - ")[2]

            # Filter by course if specified
            if course_filter and course_name not in course_filter:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for q in data.get("questions", []):
                    if q.get("question"):
                        questions.append({
                            "course": course_name,
                            "id": q.get("id"),
                            "text": q["question"],
                            "cache_key": f"{course_name}_{q.get('id')}"
                        })

            except Exception as e:
                print(f"Error reading {filename}: {e}")

    return questions

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings in batch with metadata tracking.")
    parser.add_argument("--courses", nargs="+", help="Specific courses to process (test mode)")
    parser.add_argument("--donem", type=int, help="Specific semester to process (e.g., 1, 7)")
    parser.add_argument("--all", action="store_true", help="Process all courses")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size (default: 10)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between batches in seconds (default: 0.5)")
    parser.add_argument("--migrate", action="store_true", help="Force migration from old JSON cache")

    args = parser.parse_args()

    if not args.courses and not args.all and not args.migrate and not args.donem:
        print("Error: Please specify --courses, --donem, --all, or --migrate")
        return sys.exit(1)

    print("=" * 80)
    print("BATCH EMBEDDING GENERATION")
    print("=" * 80)

    # Initialize store
    store = EmbeddingStore(ANADOLU_OUTPUT_DIR)

    # Check if migration is needed
    if args.migrate or (os.path.exists(OLD_CACHE_PATH) and len(store.metadata) == 0):
        print("Migrating existing cache...")
        store.migrate_from_json(OLD_CACHE_PATH)
        print("Migration complete.")

    print(f"Loaded store with {len(store.metadata)} existing embeddings.")

    if args.migrate and not args.courses and not args.all:
        return

    # Collect questions
    print("\nCollecting questions...")
    questions = load_questions(args.courses, args.donem)

    if not questions:
        print("No questions found.")
        return

    print(f"Found {len(questions)} questions across {len(set(q['course'] for q in questions))} courses.")

    # Determine which questions need embeddings
    to_generate = []
    cache_hits = 0
    stale_embeddings = 0

    for q in questions:
        cache_key = q["cache_key"]
        q_hash = get_question_hash(q["text"])

        if cache_key in store.metadata:
            meta = store.metadata[cache_key]

            # Check hash
            if meta.get("question_text_hash") == q_hash:
                cache_hits += 1
            else:
                stale_embeddings += 1
                to_generate.append(q)
        else:
            to_generate.append(q)

    print(f"\nCache Analysis:")
    print(f"  Cache hits: {cache_hits}")
    print(f"  Stale embeddings: {stale_embeddings}")
    print(f"  New questions: {len(to_generate) - stale_embeddings}")
    print(f"  Total to generate: {len(to_generate)}")

    if not to_generate:
        print("\nAll embeddings are up to date!")
        return

    # Generate embeddings in batches
    print(f"\nGenerating embeddings (batch size: {args.batch_size})...")

    generated_count = 0
    error_count = 0

    with tqdm(total=len(to_generate), desc="Generating embeddings", unit="q") as pbar:
        for i in range(0, len(to_generate), args.batch_size):
            batch = to_generate[i:i+args.batch_size]

            for q in batch:
                embedding = get_embedding(q["text"])

                if embedding:
                    store.add_embedding(
                        q["cache_key"],
                        embedding,
                        {
                            "question_text_hash": get_question_hash(q["text"]),
                            "generated_at": datetime.utcnow().isoformat() + "Z",
                            "question_updated_at": datetime.utcnow().isoformat() + "Z"
                        }
                    )
                    generated_count += 1
                else:
                    error_count += 1

                pbar.update(1)

            # Save store after each batch
            store.save()

            # Rate limiting
            if i + args.batch_size < len(to_generate):
                time.sleep(args.delay)

    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Successfully generated: {generated_count}")
    print(f"Errors: {error_count}")
    print(f"Total store size: {len(store.metadata)} embeddings")
    print(f"Store saved to: {store.embeddings_dir}")

if __name__ == "__main__":
    main()
