
import os

target_dir = "/Users/wildgenie/Projects/ataaof-denemeler/output/Auzef/json"

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
