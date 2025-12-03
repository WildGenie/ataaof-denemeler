import requests

url = "https://ets.anadolu.edu.tr/storage/nfs/html_books/EST101U_INTERACTIVE/EST101U-U1/index.html"

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    if response.status_code == 200:
        print(f"Content Preview:\n{response.text[:500]}")
    else:
        print("Failed to fetch.")
except Exception as e:
    print(f"Exception: {e}")
