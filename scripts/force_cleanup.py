import os
import shutil
import stat

def on_rm_error(func, path, exc_info):
    # If access is denied, try to change permissions and delete again
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

def main():
    base_dir = "output/Anadolu"
    print(f"Cleaning up {base_dir}...")

    for root, dirs, files in os.walk(base_dir):
        if "Materyaller" in root:
            for file in files:
                if file.endswith(".pdf") or file.endswith(".epub"):
                    path = os.path.join(root, file)
                    try:
                        # Try to give write permission
                        os.chmod(path, stat.S_IWUSR | stat.S_IREAD)
                        os.remove(path)
                        print(f"Deleted: {path}")
                    except Exception as e:
                        print(f"Failed to delete {path}: {e}")
                        # Try force delete strategy
                        try:
                            os.chmod(path, 0o777)
                            os.remove(path)
                            print(f"Force deleted: {path}")
                        except Exception as e2:
                            print(f"Force delete failed {path}: {e2}")

if __name__ == "__main__":
    main()
