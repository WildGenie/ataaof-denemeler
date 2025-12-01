import os
import json
import re

def find_tags_in_text(text):
    if not text or not isinstance(text, str):
        return set()
    # Find all tags like <tagname ...>
    # Regex to capture the full opening tag
    tags = set()
    matches = re.findall(r'(<[a-zA-Z0-9]+[^>]*>)', text)
    for match in matches:
        tags.add(match)
    return tags

def main():
    json_dir = 'sorular-anadolu' # Or 'output/json' depending on what we want to check. Let's check the source of truth 'sorular-anadolu'
    all_tags = set()

    print(f"Scanning {json_dir} for HTML tags...")

    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(json_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for q in data:
                    fields = ['SoruMetni', 'Aciklama', 'A', 'B', 'C', 'D', 'E']
                    for field in fields:
                        content = q.get(field)
                        tags = find_tags_in_text(content)
                        all_tags.update(tags)
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    print("\nFound HTML tags:")
    for tag in sorted(all_tags):
        print(f"- {tag}")

if __name__ == "__main__":
    main()
