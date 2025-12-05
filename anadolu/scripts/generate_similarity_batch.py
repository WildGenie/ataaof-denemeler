#!/usr/bin/env python3
"""
Generate Gemini Batch API requests for similarity analysis.
1. Uses existing embeddings to find candidate duplicate pairs (> 0.90 similarity).
2. Generates a batch request for each candidate pair to ask Gemini for confirmation.
"""

import os
import json
import sys
import numpy as np
from dotenv import load_dotenv
from typing import List, Dict
import itertools

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from anadolu.scripts.embedding_store import EmbeddingStore

load_dotenv()

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")
BATCH_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "similarity_batch_requests.jsonl")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")

def load_questions_for_course(course_name, donem):
    """Load enriched questions for a specific course."""
    path = os.path.join(JSON_DIR, f"Donem {donem}", f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json")
    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("questions", [])

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def create_prompt(q1, q2):
    """Create a prompt to compare two questions."""
    return f"""
    Aşağıda iki sınav sorusu verilmiştir. Bu iki sorunun anlamsal olarak AYNI sorunun kopyası veya çok yakın varyasyonu olup olmadığını belirle.

    SORU 1:
    Metin: {q1['question']}
    Şıklar: {q1.get('options', [])}
    Doğru Cevap Index: {q1.get('correctIndex')}

    SORU 2:
    Metin: {q2['question']}
    Şıklar: {q2.get('options', [])}
    Doğru Cevap Index: {q2.get('correctIndex')}

    ANALİZ KRİTERLERİ:
    1. Soru kökü aynı şeyi mi soruyor? (Ufak kelime farkları önemsiz)
    2. Şıklar aynı veya eşdeğer mi?
    3. Doğru cevap aynı mı?
    4. Bu iki soru bir sınav veritabanında "Duplicate" (Kopya) olarak işaretlenip biri silinmeli mi?

    CEVAP FORMATI (JSON):
    {{
      "is_duplicate": boolean,
      "reason": "kısa açıklama"
    }}
    """

def normalize_text(text):
    """Normalize text for consistent key generation."""
    if not text: return ""
    return " ".join(text.strip().split())

def main():
    store = EmbeddingStore(OUTPUT_DIR)
    print(f"Loaded store with {len(store.metadata)} embeddings.")

    batch_requests = []

    # Iterate over courses
    courses_processed = 0
    total_pairs = 0

    print("Scanning courses for candidate pairs...")

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(JSON_DIR, donem_dir)
        try:
            donem = int(donem_dir.split(" ")[1])
        except: continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename: continue

            # Extract course name
            try:
                parts = filename.split(" - ")
                course_name = parts[2]
            except: continue

            questions = load_questions_for_course(course_name, donem)
            if not questions:
                # print(f"  No questions for {course_name}")
                continue

            # Get embeddings for all questions in this course
            q_embeddings = []
            valid_questions = []

            miss_count = 0
            for q in questions:
                # Key format in store seems to be "CourseName_QuestionID"
                # Assuming question ID is consistent.
                # Example: "Sanatta Eleştirel Düşünce_1"
                key = f"{course_name}_{q['id']}"

                emb = store.get_embedding(key)
                if emb is not None:
                    q_embeddings.append(emb)
                    valid_questions.append(q)
                else:
                    miss_count += 1

            if len(valid_questions) < 2:
                if miss_count > 0:
                    print(f"  {course_name}: {len(questions)} questions, {miss_count} missing embeddings. Skipping.")
                continue

            # Compute pairwise similarities
            embeddings_matrix = np.array(q_embeddings)
            norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1e-10
            normalized_matrix = embeddings_matrix / norms
            similarity_matrix = np.dot(normalized_matrix, normalized_matrix.T)

            # Find pairs > 0.90 but < 0.999 (ignore exact duplicates)
            rows, cols = np.where((similarity_matrix > 0.90) & (similarity_matrix < 0.999))

            course_pairs = []
            seen_pairs = set()

            for r, c in zip(rows, cols):
                if r >= c: continue

                # Avoid processing same pair twice (should be handled by r>=c but being safe)
                if (r, c) in seen_pairs: continue
                seen_pairs.add((r, c))

                q1 = valid_questions[r]
                q2 = valid_questions[c]

                if q1['id'] == q2['id']: continue

                course_pairs.append((q1, q2))

            if course_pairs:
                print(f"  {course_name}: Found {len(course_pairs)} candidate pairs.")
                courses_processed += 1

            for q1, q2 in course_pairs:
                prompt = create_prompt(q1, q2)

                # Construct ID for later processing: Course|Donem|Q1_ID|Q2_ID
                key = f"{course_name}|{donem}|{q1['id']}|{q2['id']}"

                request_body = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generation_config": {
                        "response_mime_type": "application/json",
                        "response_schema": {
                            "type": "OBJECT",
                            "required": ["is_duplicate", "reason"],
                            "properties": {
                                "is_duplicate": {"type": "BOOLEAN"},
                                "reason": {"type": "STRING"}
                            }
                        }
                    }
                }

                batch_requests.append({"key": key, "request": request_body})
                total_pairs += 1

    print(f"\nGenerated {len(batch_requests)} batch requests from {courses_processed} courses with similar questions.")

    with open(BATCH_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        for req in batch_requests:
            json.dump(req, f, ensure_ascii=False)
            f.write('\n')

    print(f"Saved requests to {BATCH_REQUESTS_FILE}")

if __name__ == "__main__":
    main()
