import requests

base_url = "https://ets.anadolu.edu.tr/storage/nfs/html_books/EST101U_INTERACTIVE/EST101U-U1/"
files_to_check = ["data.json", "content.json", "config.json", "questions.json", "manifest.json", "tincan.xml"]

for filename in files_to_check:
    url = base_url + filename
    try:
        response = requests.head(url, timeout=5)
        print(f"{filename}: {response.status_code}")
        if response.status_code == 200:
             # If found, print a snippet
             r = requests.get(url, timeout=5)
             print(f"--- Content of {filename} ---")
             print(r.text[:200])
             print("-----------------------------")
    except Exception as e:
        print(f"{filename}: Error {e}")
