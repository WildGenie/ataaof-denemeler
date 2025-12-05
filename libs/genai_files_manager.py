import os
import json
import time
import hashlib
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "download_tracker.json")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GenAIFilesManager:
    def __init__(self, tracker_path=None):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.tracker_path = tracker_path if tracker_path else TRACKER_PATH
        self.tracker = self._load_tracker()

    def _load_tracker(self):
        if os.path.exists(self.tracker_path):
            try:
                with open(self.tracker_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading tracker: {e}")
        return {}

    def _save_tracker(self):
        dirname = os.path.dirname(self.tracker_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.tracker_path, 'w', encoding='utf-8') as f:
            json.dump(self.tracker, f, indent=4, ensure_ascii=False)

    def upload_file(self, local_path, material_id=None, display_name=None):
        """
        Uploads a file to GenAI, handling duplicates via tracker.
        Returns the File object (with .name, .uri, etc.).
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        if not display_name:
            display_name = os.path.basename(local_path)

        # If material_id is not provided, try to extract from filename
        if not material_id:
             # Try to extract from filename like "... - <ID>.pdf"
             try:
                 parts = display_name.rsplit(" - ", 1)
                 if len(parts) > 1 and parts[1].replace(".pdf", "").isdigit():
                     material_id = parts[1].replace(".pdf", "")
             except:
                 pass

        # fallback material_id if still None
        if not material_id:
            # Create a pseudo ID based on hash of filename to be consistent
            material_id = "unknown_" + hashlib.md5(display_name.encode()).hexdigest()

        # Check tracker
        if material_id in self.tracker:
            file_info = self.tracker[material_id]
            genai_name = file_info.get("genai_name")

            if genai_name:
                # Verify if it still exists on GenAI
                try:
                    existing_file = self.client.files.get(name=genai_name)

                    # Check state (enum or string)
                    state = str(existing_file.state)
                    if "ACTIVE" in state:
                        print(f"  Using cached file for Material {material_id}: {existing_file.uri}")
                        return existing_file
                    else:
                        print(f"  Cached file {genai_name} is not ACTIVE ({state}). Re-uploading...")
                except Exception as e:
                    # print(f"  Cached file {genai_name} not found on GenAI ({e}). Re-uploading...")
                    pass

        # Upload
        print(f"  Uploading {display_name} to GenAI...")
        try:
            # Using google.genai client
            # It accepts 'file' as path
            uploaded_file = self.client.files.upload(
                file=local_path,
                config=types.UploadFileConfig(display_name=display_name)
            )

            # Wait for processing
            while True:
                # Refresh file status
                uploaded_file = self.client.files.get(name=uploaded_file.name)
                state = str(uploaded_file.state)

                if "ACTIVE" in state:
                    break
                elif "FAILED" in state:
                    raise Exception("File upload failed state.")

                print('.', end='', flush=True)
                time.sleep(1)

            print(" Done.")

            # Update Tracker
            self.tracker[material_id] = {
                "genai_name": uploaded_file.name,
                "genai_uri": uploaded_file.uri,
                "size_bytes": uploaded_file.size_bytes,
                # sha256_hash might not be available on the object directly or named differently
                # "sha256_hash": getattr(uploaded_file, 'sha256_hash', None),
                "display_name": uploaded_file.display_name,
                "create_time": str(uploaded_file.create_time)
            }
            self._save_tracker()

            print(f"  ✅ Uploaded: {uploaded_file.uri}")
            return uploaded_file

        except Exception as e:
            print(f"  ❌ Upload failed: {e}")
            raise e
