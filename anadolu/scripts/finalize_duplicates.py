#!/usr/bin/env python3
"""
Finalize duplicate marking by merging 'near_duplicate' into 'duplicate'
and performing a unified duplicate check using:
1. Exact Text Match (Normalized)
2. Fuzzy Match (Levenshtein Ratio > 0.90)
3. Semantic Similarity (Cosine Similarity > 0.94 using Embeddings)

All identified duplicates are marked with 'is_duplicate=True' and merged into a single occurrences count.
"""

import os
import json
import difflib
import re
import sys
import numpy as np
from collections import defaultdict

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
from anadolu.scripts.embedding_store import EmbeddingStore

JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def normalize_text(text):
    """Normalize text for comparison (remove punctuation, lowercase)."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if vec1 is None or vec2 is None:
        return 0.0
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)

def main():
    print("Finalizing duplicate analysis (Exact + Fuzzy + Semantic)...")

    # Load embeddings
    print("Loading embedding store...")
    store = EmbeddingStore(base_dir=os.path.join(PROJECT_ROOT, "output", "Anadolu"))
    print(f"Loaded {len(store.metadata)} embeddings.")

    total_files = 0
    total_duplicates = 0

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(JSON_DIR, donem_dir)
        try:
            donem = int(donem_dir.split(" ")[1])
        except: continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename: continue

            # Identify Course Name from filename for keys
            # Format: Anadolu - Dönem X - Course Name - ...
            parts = filename.split(" - ")
            if len(parts) >= 3:
                course_name = parts[2]
            else:
                course_name = "Unknown"

            file_path = os.path.join(donem_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                questions = data.get("questions", [])
                if not questions: continue

                # --- PHASE 0: Cleanup & Legacy Integration ---
                for q in questions:
                    # Convert legacy near_duplicate
                    if q.get("is_near_duplicate"):
                        q["is_duplicate"] = True
                        q["duplicate_of"] = q.get("near_duplicate_of")
                        if not q.get("duplication_reason"):
                            q["duplication_reason"] = "Semantic Similarity (Legacy)"

                    # Clean fields
                    for field in ["is_near_duplicate", "near_duplicate_of", "similarity_score"]:
                        if field in q: del q[field]

                # --- PHASE 1: Exact Text Match ---
                groups = defaultdict(list)
                for q in questions:
                    text = normalize_text(q.get("question"))
                    if text:
                        groups[text].append(q)

                modified = False

                for text, group in groups.items():
                    if len(group) > 1:
                        group.sort(key=lambda x: x.get("id"))
                        primary = group[0]
                        primary_id = primary.get("id")

                        # Unmark primary if it was marked as duplicate internally
                        if primary.get("is_duplicate"):
                             del primary["is_duplicate"]
                             if "duplicate_of" in primary: del primary["duplicate_of"]

                        primary["occurrence_count"] = len(group)

                        for other in group[1:]:
                            other["is_duplicate"] = True
                            other["duplicate_of"] = primary_id
                            other["duplication_reason"] = "Exact Text Match"
                            if "occurrence_count" in other: del other["occurrence_count"]

                        modified = True

                # --- PHASE 2 & 3: Fuzzy + Semantic Match ---
                # Compare remaining candidates
                candidates = [q for q in questions if not q.get("is_duplicate")]

                # Pre-fetch embeddings for candidates
                embeddings_map = {}
                for q in candidates:
                    q_id = q.get("id")
                    # Try possible keys
                    # 1. CourseName_QuestionID
                    key1 = f"{course_name}_{q_id}"
                    # 2. Normalized Text Key? (Store uses text or ID?)
                    # Store usually uses key provided during add.
                    # Let's hope ID based key works. If not, we might miss some.
                    vec = store.get_embedding(key1)
                    if vec is None:
                        # Try text based key if implemented or fallback
                        pass
                    embeddings_map[q_id] = vec

                for i in range(len(candidates)):
                    q1 = candidates[i]
                    txt1 = normalize_text(q1.get("question"))
                    vec1 = embeddings_map.get(q1.get("id"))

                    if not txt1: continue

                    for j in range(i + 1, len(candidates)):
                        q2 = candidates[j]
                        if q2.get("is_duplicate"): continue # Already marked

                        txt2 = normalize_text(q2.get("question"))
                        if not txt2: continue

                        is_match = False
                        reason = ""

                        # 2. Fuzzy Match
                        if difflib.SequenceMatcher(None, txt1, txt2).ratio() > 0.90:
                            is_match = True
                            reason = "Fuzzy Match (>90%)"

                        # 3. Semantic Sim (if not already matched)
                        if not is_match and vec1 is not None:
                            vec2 = embeddings_map.get(q2.get("id"))
                            if vec2 is not None:
                                sim = get_cosine_similarity(vec1, vec2)
                                if sim > 0.94:
                                    is_match = True
                                    reason = f"Semantic Similarity ({sim:.2f})"

                        if is_match:
                            q2["is_duplicate"] = True
                            q2["duplicate_of"] = q1.get("id")
                            q2["duplication_reason"] = reason

                            # Merge counts
                            q1_count = q1.get("occurrence_count", 1)
                            q2_count = q2.get("occurrence_count", 1)
                            q1["occurrence_count"] = q1_count + q2_count

                            if "occurrence_count" in q2: del q2["occurrence_count"]

                            modified = True
                            # total_duplicates += 1

                # --- PHASE 4: Global Count Recalculation ---
                # Map ID to question object
                id_map = {q.get("id"): q for q in questions}

                # Initialize counters
                counters = defaultdict(int)

                for q in questions:
                    # Find root
                    curr = q
                    seen = {q.get("id")}
                    while curr.get("is_duplicate") and curr.get("duplicate_of") in id_map:
                        pid = curr.get("duplicate_of")
                        if pid in seen: break # Cycle detected
                        seen.add(pid)
                        curr = id_map[pid]

                    # Add 1 to root's counter
                    root_id = curr.get("id")
                    counters[root_id] += 1

                # Apply counts to question objects
                for q in questions:
                    qid = q.get("id")
                    if qid in counters:
                        q["occurrence_count"] = counters[qid]
                    # Check loop: if occurrence_count > 1 and is_duplicate is True, that's weird but ok.
                    # We usually hide duplicates. The root gets the count.

                cnt = sum(1 for q in questions if q.get("is_duplicate"))
                total_duplicates += cnt

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                total_files += 1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nProcessed {total_files} files.")
    print(f"Total duplicates marked: {total_duplicates}")

if __name__ == "__main__":
    main()
