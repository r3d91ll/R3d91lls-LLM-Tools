import os
import hashlib

def compute_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()

def find_duplicate_files(directory):
    hashes = {}
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):  # Check if it's a file
            file_hash = compute_sha256(file_path)
            if file_hash in hashes:
                hashes[file_hash].append(filename)
            else:
                hashes[file_hash] = [filename]
    return hashes

def print_duplicates(directory):
    duplicates = find_duplicate_files(directory)
    for file_hash, files in duplicates.items():
        if len(files) > 1:
            print(f"Duplicate files (hash {file_hash}): {', '.join(files)}")

if __name__ == "__main__":
    directory = input("Enter the directory path to check for duplicate files: ")
    print_duplicates(directory)
