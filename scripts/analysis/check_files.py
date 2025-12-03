
import os
from dotenv import load_dotenv

load_dotenv()

base_path = os.getenv("LOCAL_MATERIALS_ROOT")
if not base_path:
    print("Error: LOCAL_MATERIALS_ROOT not set in .env")
    exit(1)

path = os.path.join(base_path, "II. Yarıyıl/Anadolu Kültür Tarihi/Çıkmış Sorular")

try:
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"Found {len(files)} files:")
        for f in sorted(files):
            print(f" - {f}")
    else:
        print("Directory does not exist!")
except Exception as e:
    print(f"Error: {e}")
