import os

# Determine the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_DIR = os.path.join(BASE_DIR, 'output', 'Auzef')
target_dir = os.path.join(AUZEF_DIR, 'json')

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if " Ve " in file:
            new_name = file.replace(" Ve ", " ve ")

            # Additional check for cases like "Ve " at start of course name part?
            # But " Ve " covers the space usage.

            old_path = os.path.join(root, file)
            new_path = os.path.join(root, new_name)

            print(f"Renaming: {file} -> {new_name}")
            os.rename(old_path, new_path)
