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
    # Captures: 1=(version = ), 2=(" or '), 3=(current_version), 4=(matching quote)
    # We use a simplified pattern that handles both quote types
    pattern = r'(version\s*=\s*)([\"\])([^\"\]+)([\"\])')
    
    if re.search(pattern, content):
        # \g<1> is the prefix, \g<2> is the opening quote, \g<4> is the closing quote
        new_content = re.sub(pattern, f'\\g<1>\\g<2>{new_version}\\g<4>', content)
        
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
    
    # Define files to update (relative to repo root)
    files = ['pyproject.toml', 'setup.py']
    
    for f in files:
        update_file(f, new_version)