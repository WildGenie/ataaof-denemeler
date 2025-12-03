
import os

def list_jsons():
    print("JSON files in root:")
    try:
        for f in os.listdir("."):
            if f.endswith(".json") and os.path.isfile(f):
                print(f" - {f}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_jsons()
