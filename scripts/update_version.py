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

    # Regex to match version = "..." or version='...'
    # Captures: 1=(version = ), 2=(" or '), 3=(current_version), 4=(" or ')
    pattern = r'(version\s*=\s*)([\"\'])([^\"\\]+)([\"\\]))'
    
    if re.search(pattern, content):
        # Use raw string for replacement pattern to avoid escape issues
        # \g<1> refers to group 1, etc.
        new_content = re.sub(pattern, f'\\g<1>\\g<2>{new_version}\\g<4>', content)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"  -> Success: Version set to {new_version}")
    else:
        print(f"  -> Warning: Could not find version string pattern.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]
    
    # Define files to update (relative to repo root)
    files = ['pyproject.toml', 'setup.py']
    
    for f in files:
        update_file(f, new_version)
