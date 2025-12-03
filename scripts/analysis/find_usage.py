
import os

def find_usage(search_str):
    print(f"Searching for '{search_str}'...")
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if search_str in content:
                            print(f"Found in: {path}")
                except:
                    pass

if __name__ == "__main__":
    find_usage("course_mapping.json")
