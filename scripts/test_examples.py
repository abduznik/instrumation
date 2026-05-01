import os
import subprocess
import sys

def run_examples():
    examples_dir = "examples"
    python_path = os.path.abspath("src")
    
    # List of examples to run
    examples = []
    for root, dirs, files in os.walk(examples_dir):
        for file in files:
            if file.endswith(".py"):
                examples.append(os.path.join(root, file))
    
    print(f"--- Running {len(examples)} Examples in SIMULATION Mode ---\n")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = python_path
    env["INSTRUMATION_MODE"] = "SIM"
    
    success_count = 0
    fail_count = 0
    
    for ex in examples:
        print(f"Running: {ex}...", end=" ", flush=True)
        try:
            # Use subprocess to run each example
            # Timeout of 10s to prevent hanging
            result = subprocess.run(
                [sys.executable, ex],
                env=env,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("SUCCESS")
                success_count += 1
            else:
                print("FAILED")
                print(f"  Error: {result.stderr.strip().splitlines()[-1] if result.stderr else 'Unknown Error'}")
                fail_count += 1
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            fail_count += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail_count += 1
            
    print(f"\n--- Summary: {success_count} Passed, {fail_count} Failed ---")
    return fail_count == 0

if __name__ == "__main__":
    if not run_examples():
        sys.exit(1)
