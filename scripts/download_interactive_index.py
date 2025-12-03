import requests

url = "https://ets.anadolu.edu.tr/storage/nfs/html_books/EST101U_INTERACTIVE/EST101U-U1/index.html"
response = requests.get(url)
with open("interactive_index.html", "w", encoding="utf-8") as f:
    f.write(response.text)
