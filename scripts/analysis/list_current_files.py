
import os

def list_files():
    print("Root:")
    try:
        for f in os.listdir("."):
            if os.path.isfile(f):
                print(f" - {f}")
    except Exception as e:
        print(f"Error listing root: {e}")

    print("\nReports:")
    try:
        if os.path.exists("reports"):
            for f in os.listdir("reports"):
                print(f" - {f}")
        else:
            print("reports directory does not exist")
    except Exception as e:
        print(f"Error listing reports: {e}")

if __name__ == "__main__":
    list_files()
