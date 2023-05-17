import sys
import io

from diff_fuzz import run_executables
from config import TARGET_CONFIGS

def main(input_file: io.BufferedReader) -> None:
    fingerprint, _, parse_trees = run_executables(input_file.read())
    for tc, parse_tree in zip(TARGET_CONFIGS, parse_trees):
        print(tc.executable)
        print(parse_tree)
        print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <file_to_interpret>")
        sys.exit(1)

    main(open(sys.argv[1], "rb"))
