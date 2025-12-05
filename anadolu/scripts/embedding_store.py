import os
import json
import numpy as np
import shutil
from datetime import datetime

class EmbeddingStore:
    """
    Manages embedding storage using NumPy for vectors and JSON for metadata.
    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.embeddings_dir = os.path.join(base_dir, "embeddings")
        self.vectors_path = os.path.join(self.embeddings_dir, "vectors.npy")
        self.metadata_path = os.path.join(self.embeddings_dir, "metadata.json")

        self._ensure_dir()
        self.metadata = {}
        self.vectors = None
        self.dirty = False

        self.load()

    def _ensure_dir(self):
        if not os.path.exists(self.embeddings_dir):
            os.makedirs(self.embeddings_dir)

    def load(self):
        """Load metadata and vectors from disk."""
        # Load metadata
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

        # Load vectors
        if os.path.exists(self.vectors_path):
            try:
                self.vectors = np.load(self.vectors_path)
            except Exception as e:
                print(f"Error loading vectors: {e}")
                self.vectors = None
        else:
            self.vectors = None

    def save(self):
        """Save metadata and vectors to disk."""
        if not self.dirty:
            return

        # Save metadata
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata: {e}")

        # Save vectors
        if self.vectors is not None:
            try:
                np.save(self.vectors_path, self.vectors)
            except Exception as e:
                print(f"Error saving vectors: {e}")

        self.dirty = False

    def get_embedding(self, key):
        """Get embedding vector for a key."""
        if key not in self.metadata:
            return None

        idx = self.metadata[key]["index"]
        if self.vectors is None or idx >= len(self.vectors):
            return None

        return self.vectors[idx]

    def add_embedding(self, key, vector, extra_metadata=None):
        """Add or update an embedding."""
        vector = np.array(vector, dtype=np.float32)

        if key in self.metadata:
            # Update existing
            idx = self.metadata[key]["index"]
            self.vectors[idx] = vector
        else:
            # Add new
            if self.vectors is None:
                self.vectors = np.array([vector], dtype=np.float32)
                idx = 0
            else:
                idx = len(self.vectors)
                self.vectors = np.vstack([self.vectors, vector])

        # Update metadata
        meta = {
            "index": idx,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        if extra_metadata:
            meta.update(extra_metadata)

        self.metadata[key] = meta
        self.dirty = True

    def migrate_from_json(self, json_path):
        """Migrate from legacy JSON cache file."""
        if not os.path.exists(json_path):
            print(f"JSON cache not found: {json_path}")
            return

        print(f"Migrating from {json_path}...")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                legacy_data = json.load(f)

            count = 0
            for key, value in legacy_data.items():
                if isinstance(value, dict) and "embedding" in value:
                    # New format in JSON
                    vector = value["embedding"]
                    meta = {k: v for k, v in value.items() if k != "embedding"}
                    self.add_embedding(key, vector, meta)
                    count += 1
                elif isinstance(value, list):
                    # Old format (just list)
                    self.add_embedding(key, value)
                    count += 1

            self.save()
            print(f"Migrated {count} embeddings.")

        except Exception as e:
            print(f"Error during migration: {e}")
