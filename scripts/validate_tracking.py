import subprocess
import sys

def check_untracked_files(directories):
    print("Checking for untracked files in key directories...")
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        stdout=subprocess.PIPE,
        text=True
    )
    untracked = result.stdout.strip().split('\n') if result.stdout else []
    flagged = []
    for f in untracked:
        if any(f.startswith(d + '/') or f.startswith(d + '\\') or f == d for d in directories):
            flagged.append(f)
    if flagged:
        print("ERROR: The following files are untracked and must be added to git:")
        for f in flagged:
            print(f"  - {f}")
        print("Please run 'git add <file>' and commit.")
        sys.exit(1)
    else:
        print("All data/scripts/docs are tracked by git.")
        sys.exit(0)

if __name__ == '__main__':
    check_untracked_files(['data', 'scripts', 'docs', 'src', 'templates']) 