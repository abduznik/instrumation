import sys
import re
import os

def update_file(file_path, new_version):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}: File not found.")
        return

    print(f"Updating {file_path}...")
    with open(file_path, 'r') as f:
        content = f.read()

    # Regex breakdown:
    # (version\s*=\s*["\'])  -> Group 1: Matches 'version = "' or 'version="'
    # ([^"\']+)              -> Group 2: Matches the version number inside
    # ([ "\'])                -> Group 3: Matches the closing quote
    pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
    
    if re.search(pattern, content):
        # We replace Group 2 (the old version) with the new_version
        new_content = re.sub(pattern, f'\g<1>{new_version}\g<3>', content)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"  -> Success: Version set to {new_version}")
    else:
        print(f"  -> Warning: Could not find version string pattern in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]
    
    files = ['pyproject.toml', 'setup.py']
    
    for f in files:
        update_file(f, new_version)
